"""Claude Command MCP Server - Real-time AI collaboration with fastMCP"""

import os
from typing import Any, Dict

from fastmcp import FastMCP

from .clients.factory import ClientFactory, create_available_clients, get_primary_client
from .missions import (
    execute_brainstorm,
    execute_conversation,
    execute_query,
    execute_recon,
    execute_review,
    format_recon_output,
)
from .sessions import session_manager
from .settings import settings

# Create the main MCP server
mcp: FastMCP = FastMCP(
    "Claude Command", dependencies=["google-generativeai", "fastmcp"]
)


def get_default_client():
    """Get the primary available AI client"""
    return get_primary_client()


def get_client_by_provider(provider: str = ""):
    """Get AI client by provider name, fallback to default if not specified or unavailable"""
    if provider:
        # Try to get the specific provider
        client = ClientFactory.create_client(provider.lower())
        if client and client.is_available():
            return client
        # If specific provider failed, fall back to default

    # Return default client
    return get_default_client()


@mcp.tool
def claude_command_query(
    prompt: str,
    conversation_id: str = "",
    temperature: float = 0.7,
    provider: str = "",
    providers: str = "",
    save_results: bool = True,
) -> Dict[str, Any]:
    """Claude Command: Execute live multi-provider AI conversations with real-time streaming across Gemini, OpenAI, and Anthropic."""

    try:
        # If providers parameter is used, delegate to query mission
        if providers:
            return execute_query(prompt, providers, temperature, save_results)

        # Single provider logic - delegate to conversation mission
        return execute_conversation(
            prompt, conversation_id, provider, temperature, save_results
        )

    except Exception as e:
        return {"error": f"Error during query: {str(e)}", "success": False}


@mcp.tool
def claude_command_conversation_history(conversation_id: str = "") -> Dict[str, Any]:
    """Claude Command: Retrieve formatted conversation history from saved multi-provider AI sessions."""

    try:
        if conversation_id:
            # Use specified conversation ID
            conversation_file = session_manager.get_conversation_file_path(
                conversation_id
            )
        else:
            # Get most recent conversation file
            recent_conversation = session_manager.get_most_recent_conversation()
            if recent_conversation is None:
                return {"error": "No conversations found.", "success": False}
            conversation_file = recent_conversation
            conversation_id = os.path.basename(conversation_file)

        if not os.path.exists(conversation_file):
            return {
                "error": f"Conversation file not found: {conversation_id}",
                "success": False,
            }

        formatted_history = session_manager.format_conversation_history(
            conversation_file
        )

        return {
            "conversation_history": formatted_history,
            "conversation_id": conversation_id,
            "success": True,
        }

    except Exception as e:
        return {
            "error": f"Error retrieving conversation history: {str(e)}",
            "success": False,
        }


@mcp.tool
def claude_command_review(
    code: str,
    focus: str = "general",
    provider: str = "",
    providers: str = "",
    temperature: float = 0.3,
    save_results: bool = True,
) -> Dict[str, Any]:
    """Claude Command: Get multi-provider code analysis with structured focus areas like security, performance, and best practices."""

    try:
        # If providers parameter is used, delegate to review mission
        if providers:
            return execute_review(code, focus, providers, temperature, save_results)

        # Single provider logic (existing behavior)
        client = get_client_by_provider(provider)
        if not client or not client.is_available():
            error_msg = client.get_error() if client else "No AI client available"
            return {"error": f"AI client not available: {error_msg}", "success": False}

        try:
            # Use same multi-file streaming as other tools
            from .streaming import (
                create_provider_stream_file,
                generate_operation_timestamp,
                stream_to_provider_file,
            )

            timestamp = generate_operation_timestamp()
            provider_name = client.get_display_name().lower().replace(" ", "-")

            # Create review prompt for streaming
            review_prompt = f"Code Review - Focus: {focus}\n\nCode:\n{code}"

            # Create stream file
            streaming_file = create_provider_stream_file(
                "review", timestamp, provider_name, review_prompt, temperature
            )

            # Get review result
            review_result = client.review_code(code, focus)

            # Stream the response word by word
            words = review_result.split()
            for i, word in enumerate(words):
                if i == 0:
                    stream_to_provider_file(streaming_file, word)
                else:
                    stream_to_provider_file(streaming_file, f" {word}")

            # Add completion marker
            stream_to_provider_file(streaming_file, "\n\n**CODE REVIEW COMPLETE**\n")

            return {
                "code_review": review_result,
                "focus_area": focus,
                "reviewer": client.get_display_name(),
                "model": client.get_model_name(),
                "streaming_file": streaming_file,
                "watch_command": f"tail -f {streaming_file}",
                "success": True,
            }

        except Exception as e:
            return {"error": f"Error during code review: {str(e)}", "success": False}

    except Exception as e:
        return {"error": f"Error during code review: {str(e)}", "success": False}


@mcp.tool
def claude_command_brainstorm(
    topic: str,
    context: str = "",
    provider: str = "",
    providers: str = "",
    temperature: float = 0.8,
    save_results: bool = True,
) -> Dict[str, Any]:
    """Claude Command: Collaborate with multiple AI providers simultaneously for diverse creative problem-solving perspectives."""

    try:
        # If providers parameter is used, delegate to brainstorm mission
        if providers:
            return execute_brainstorm(
                topic, context, providers, temperature, save_results
            )

        # Single provider logic (existing behavior)
        client = get_client_by_provider(provider)
        if not client or not client.is_available():
            error_msg = client.get_error() if client else "No AI client available"
            return {"error": f"AI client not available: {error_msg}", "success": False}

        try:
            # Use same multi-file streaming as other tools
            from .streaming import (
                create_provider_stream_file,
                generate_operation_timestamp,
                stream_to_provider_file,
            )

            timestamp = generate_operation_timestamp()
            provider_name = client.get_display_name().lower().replace(" ", "-")

            # Create brainstorm prompt for streaming
            brainstorm_prompt = f"Topic: {topic}"
            if context:
                brainstorm_prompt += f"\nContext: {context}"

            # Create stream file
            streaming_file = create_provider_stream_file(
                "brainstorm", timestamp, provider_name, brainstorm_prompt, temperature
            )

            # Get brainstorm result
            brainstorm_result = client.brainstorm(topic, context)

            # Stream the response word by word
            words = brainstorm_result.split()
            for i, word in enumerate(words):
                if i == 0:
                    stream_to_provider_file(streaming_file, word)
                else:
                    stream_to_provider_file(streaming_file, f" {word}")

            # Add completion marker
            stream_to_provider_file(streaming_file, "\n\n**BRAINSTORMING COMPLETE**\n")

            return {
                "brainstorming_ideas": brainstorm_result,
                "topic": topic,
                "context": context,
                "contributor": client.get_display_name(),
                "model": client.get_model_name(),
                "streaming_file": streaming_file,
                "watch_command": f"tail -f {streaming_file}",
                "success": True,
            }

        except Exception as e:
            return {"error": f"Error during brainstorming: {str(e)}", "success": False}

    except Exception as e:
        return {"error": f"Error during brainstorming: {str(e)}", "success": False}


@mcp.tool
def claude_command_status() -> Dict[str, Any]:
    """Claude Command: Get multi-provider AI client status, configuration, and session management information."""

    try:
        clients = create_available_clients()
        default_client = get_default_client()

        # Get client status information
        client_info = []
        for client in clients:
            client_info.append(
                {
                    "name": client.get_model_name(),
                    "display_name": client.get_display_name(),
                    "available": client.is_available(),
                    "error": client.get_error() if not client.is_available() else None,
                }
            )

        return {
            "server_version": "0.1.6",
            "status": "running",
            "default_client": default_client.get_display_name()
            if default_client
            else None,
            "available_clients": client_info,
            "total_clients": len(clients),
            "conversations_directory": session_manager.get_conversations_directory(),
            "live_streams_directory": session_manager.get_live_streams_directory(),
            "has_api_keys": settings.has_valid_api_key(),
            "settings": {
                "conversations_dir": settings.conversations_dir,
                "default_temperature": settings.default_temperature,
                "max_history_length": settings.max_history_length,
                "user_name": settings.user_name,
            },
            "success": True,
        }

    except Exception as e:
        return {"error": f"Error getting server status: {str(e)}", "success": False}


@mcp.tool
def claude_command_conversations_list() -> Dict[str, Any]:
    """Claude Command: List all saved multi-provider conversation files with timestamps and metadata."""

    try:
        conversation_files = session_manager.list_conversation_files()

        return {
            "conversation_files": conversation_files,
            "total_conversations": len(conversation_files),
            "conversations_directory": session_manager.get_conversations_directory(),
            "success": True,
        }

    except Exception as e:
        return {"error": f"Error listing conversations: {str(e)}", "success": False}


@mcp.tool
def claude_command_conversations_cleanup(keep_count: int = 50) -> Dict[str, Any]:
    """Claude Command: Remove old conversation files while preserving recent multi-provider session data."""

    try:
        deleted_count = session_manager.cleanup_old_conversations(keep_count)

        return {
            "deleted_conversations": deleted_count,
            "kept_conversations": keep_count,
            "success": True,
        }

    except Exception as e:
        return {"error": f"Error cleaning up conversations: {str(e)}", "success": False}


@mcp.tool
def claude_command_recon(
    survey_prompt: str,
    providers: str = "gemini,openai,anthropic",
    temperature: float = 0.5,
    save_results: bool = True,
) -> Dict[str, Any]:
    """Claude Command: Survey multiple AI providers independently to gather unbiased comparative intelligence for your analysis."""

    try:
        # Execute the reconnaissance
        results = execute_recon(survey_prompt, providers, temperature, save_results)

        # Format output for display
        formatted_output = format_recon_output(results)

        return {
            "survey_prompt": survey_prompt,
            "recon_results": results,
            "formatted_output": formatted_output,
            "success": True,
        }

    except Exception as e:
        return {"error": f"Error during reconnaissance: {str(e)}", "success": False}


def main():
    """Main entry point for the Claude Command MCP server"""
    mcp.run()


if __name__ == "__main__":
    main()
