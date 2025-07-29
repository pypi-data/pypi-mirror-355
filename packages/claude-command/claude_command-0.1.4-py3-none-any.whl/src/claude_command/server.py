#!/usr/bin/env python3
"""
Claude Command - AI Collaboration MCP Server
Command center enabling Claude Code to collaborate with multiple AI providers (Gemini, OpenAI, etc.)
"""
# /// script
# dependencies = [
#     "google-generativeai",
# ]
# ///

import json
import os
import sys
import threading
from typing import Any, Dict

# Ensure unbuffered output
sys.stdout = os.fdopen(sys.stdout.fileno(), "w", 1)
sys.stderr = os.fdopen(sys.stderr.fileno(), "w", 1)

from .clients.factory import default_client
from .config import __version__
from .sessions import session_manager


def format_ai_response(text: str) -> str:
    """Format AI response with simple formatting for real-time streaming"""
    ai_name = (
        default_client.get_display_name()
        if default_client and default_client.is_available()
        else "AI"
    )
    return f"\n🔷 {ai_name.upper()}:\n\n{text}\n"


def send_response(response: Dict[str, Any]) -> None:
    """Send a JSON-RPC response"""
    print(json.dumps(response), flush=True)


def handle_initialize(request_id: Any) -> Dict[str, Any]:
    """Handle initialization"""
    # Initialize session conversation file
    try:
        session_file = session_manager.initialize_session()
        session_manager.set_current_session_file(session_file)
    except Exception:
        # If session initialization fails, continue without it
        pass

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "claude-command", "version": __version__},
        },
    }


def handle_tools_list(request_id: Any) -> Dict[str, Any]:
    """List available tools"""
    tools = []

    if default_client and default_client.is_available():
        ai_name = default_client.get_display_name() if default_client else "AI"
        tools = [
            {
                "name": "ai_query",
                "description": f"Start a LIVE three-way conversation with {ai_name}! The user can see this conversation in real-time and may interrupt by pressing Esc to add their own input. When this happens, you should relay their message to the AI naturally (e.g., 'Hi {ai_name}, the user just said: [message]. What do you think?'). This creates a live collaborative conversation between Claude, {ai_name}, and the human user. The conversation maintains full context and is saved to a JSON file. Use this for AI-to-AI discussions, problem-solving, or any topic where real-time collaboration would be valuable.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": f"Your message to {ai_name} in this live three-way conversation. The user can see this exchange in real-time. If the user interrupts, include their input like: 'Hi {ai_name}, the user just said: [their message]. What are your thoughts on that?' Write naturally and remember this is a collaborative space.",
                        },
                        "conversation_id": {
                            "type": "string",
                            "description": "Optional conversation ID to maintain context. If not provided, a new conversation will be started. Use the same ID to continue a conversation.",
                            "default": "",
                        },
                        "temperature": {
                            "type": "number",
                            "description": "Temperature for response (0.0-1.0)",
                            "default": 0.5,
                        },
                    },
                    "required": ["prompt"],
                },
            },
            {
                "name": "get_conversation_history",
                "description": f"Get the formatted conversation history from a saved conversation. Use this after ask_ai to see the complete formatted conversation including {ai_name}'s response.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "conversation_id": {
                            "type": "string",
                            "description": "The conversation ID to retrieve. If not provided, gets the most recent conversation.",
                            "default": "",
                        }
                    },
                },
            },
            {
                "name": "ai_review",
                "description": f"Get {ai_name}'s perspective on code! This is perfect for getting a second AI opinion on code quality, security, performance, or best practices. {ai_name} will analyze the code and provide detailed feedback that you can then discuss or build upon.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": f"The code you want {ai_name} to review and provide feedback on",
                        },
                        "focus": {
                            "type": "string",
                            "description": "Specific focus area (security, performance, etc.)",
                            "default": "general",
                        },
                    },
                    "required": ["code"],
                },
            },
            {
                "name": "ai_brainstorm",
                "description": f"Collaborate with {ai_name} on creative problem-solving! Perfect for brainstorming features, architectural decisions, or exploring different approaches to challenges. {ai_name} will contribute ideas and perspectives that complement your own thinking.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "What you want to brainstorm about. Examples: 'improving database performance', 'user authentication strategies', 'API design patterns'",
                        },
                        "context": {
                            "type": "string",
                            "description": f"Background information or constraints to help {ai_name} understand the situation better",
                            "default": "",
                        },
                    },
                    "required": ["topic"],
                },
            },
        ]
    else:
        tools = [
            {
                "name": "server_info",
                "description": "Get server status and error information",
                "inputSchema": {"type": "object", "properties": {}},
            }
        ]

    return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": tools}}


def handle_tool_call(request_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle tool execution"""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    try:
        result = ""

        if tool_name == "server_info":
            if default_client and default_client.is_available():
                result = f"Server v{__version__} - {default_client.get_display_name()} connected and ready!"
            else:
                error_msg = (
                    default_client.get_error()
                    if default_client
                    else "No AI client available"
                )
                result = f"Server v{__version__} - AI client error: {error_msg}"

        elif tool_name == "ai_query":
            if not default_client or not default_client.is_available():
                error_msg = (
                    default_client.get_error()
                    if default_client
                    else "No AI client available"
                )
                result = f"AI client not available: {error_msg}"
            else:
                prompt = arguments.get("prompt", "")
                conversation_id = arguments.get("conversation_id", "")
                temperature = arguments.get("temperature", None)

                # Determine conversation file to use
                if conversation_id:
                    # Use specified conversation ID
                    conversation_file = session_manager.get_conversation_file_path(
                        conversation_id
                    )
                else:
                    # Use current session file
                    current_session = session_manager.get_current_session_file()
                    if current_session is None:
                        # Fallback: create new session
                        conversation_file = session_manager.initialize_session()
                    else:
                        conversation_file = current_session

                # Get conversation history
                conversation_history = session_manager.load_conversation(
                    conversation_file
                )

                # Start background processing with streaming
                streaming_file = session_manager.get_live_stream_path()

                def background_task():
                    try:
                        # Call Gemini with streaming
                        gemini_response = default_client.call_with_streaming(
                            prompt, conversation_history, streaming_file, temperature
                        )

                        # Save the exchange to conversation file
                        session_manager.add_exchange_to_conversation(
                            conversation_file, prompt, gemini_response
                        )
                    except Exception as e:
                        # Write error to streaming file
                        try:
                            with open(streaming_file, "a") as f:
                                f.write(f"\n\nERROR: {str(e)}\n")
                        except Exception:
                            pass

                # Start background thread
                thread = threading.Thread(target=background_task)
                thread.daemon = True
                thread.start()

                # Return immediate response
                ai_name = default_client.get_display_name() if default_client else "AI"
                result = f"""
ASKING {ai_name.upper()} - {os.path.basename(conversation_file)}
========================================================================

CLAUDE (you):
{prompt}

{ai_name.upper()}: Responding... (watch streaming in real-time)

Streaming to: {streaming_file}
Watch with: tail -f {streaming_file}

========================================================================
TIP: Use get_conversation_history after {ai_name} responds to see formatted conversation!
"""

        elif tool_name == "get_conversation_history":
            conversation_id = arguments.get("conversation_id", "")

            if conversation_id:
                # Use specified conversation ID
                conversation_file = session_manager.get_conversation_file_path(
                    conversation_id
                )
            else:
                # Get most recent conversation file
                recent_conversation = session_manager.get_most_recent_conversation()
                if recent_conversation is None:
                    result = "No conversations found."
                else:
                    conversation_file = recent_conversation
                    conversation_id = os.path.basename(conversation_file)

            if conversation_file and os.path.exists(conversation_file):
                result = session_manager.format_conversation_history(conversation_file)
            else:
                result = f"Conversation file not found: {conversation_id}"

        elif tool_name == "ai_review":
            if not default_client or not default_client.is_available():
                error_msg = (
                    default_client.get_error()
                    if default_client
                    else "No AI client available"
                )
                result = f"AI client not available: {error_msg}"
            else:
                code = arguments.get("code", "")
                focus = arguments.get("focus", "general")
                result = (
                    default_client.review_code(code, focus)
                    if default_client
                    else "No AI client available"
                )

        elif tool_name == "ai_brainstorm":
            if not default_client or not default_client.is_available():
                error_msg = (
                    default_client.get_error()
                    if default_client
                    else "No AI client available"
                )
                result = f"AI client not available: {error_msg}"
            else:
                topic = arguments.get("topic", "")
                context = arguments.get("context", "")
                result = (
                    default_client.brainstorm(topic, context)
                    if default_client
                    else "No AI client available"
                )

        else:
            raise ValueError(f"Unknown tool: {tool_name}")

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [{"type": "text", "text": format_ai_response(result)}]
            },
        }
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32603, "message": str(e)},
        }


def main() -> None:
    """Main server loop"""
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            request = json.loads(line.strip())
            method = request.get("method")
            request_id = request.get("id")
            params = request.get("params", {})

            if method == "initialize":
                response = handle_initialize(request_id)
            elif method == "tools/list":
                response = handle_tools_list(request_id)
            elif method == "tools/call":
                response = handle_tool_call(request_id, params)
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                }

            send_response(response)

        except json.JSONDecodeError:
            continue
        except EOFError:
            break
        except Exception as e:
            if "request_id" in locals():
                send_response(
                    {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": f"Internal error: {str(e)}",
                        },
                    }
                )


if __name__ == "__main__":
    main()
