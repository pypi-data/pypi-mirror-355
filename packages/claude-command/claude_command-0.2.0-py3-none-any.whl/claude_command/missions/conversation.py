"""Conversation mission for live AI conversations with context and history"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from ..clients.factory import ClientFactory
from ..sessions import session_manager
from ..streaming import (
    create_provider_stream_file,
    generate_operation_timestamp,
    stream_to_provider_file,
    update_provider_question,
)


def execute_conversation(
    prompt: str,
    conversation_id: str = "",
    provider: Optional[str] = None,
    temperature: Optional[float] = None,
    save_results: bool = True,
) -> Dict[str, Any]:
    """
    Execute live conversation with AI provider including context and history.

    This maintains conversation context and saves the full exchange.
    All activity is streamed live to a provider-specific file.

    Args:
        prompt: The message/prompt for the conversation
        conversation_id: Specific conversation to continue (optional)
        provider: AI provider to use (gemini, openai, anthropic)
        temperature: Temperature setting for responses
        save_results: Whether to save results to file

    Returns:
        Dict containing conversation result with response and file paths
    """

    timestamp = generate_operation_timestamp()

    # Get the specific provider client
    client = ClientFactory.create_client(provider or "gemini")
    if not client or not client.is_available():
        return {
            "error": f"Provider {provider or 'default'} not available: {client.get_error() if client else 'No client'}",
            "success": False,
        }

    provider_name = client.get_display_name().lower().replace(" ", "-")

    # Handle conversation file
    if conversation_id:
        conversation_file = session_manager.get_conversation_file_path(conversation_id)
    else:
        current_session = session_manager.get_current_session_file()
        if current_session is None:
            conversation_file = session_manager.initialize_session()
        else:
            conversation_file = current_session

    # Get conversation history
    conversation_history = session_manager.load_conversation(conversation_file)

    # Create stream file
    stream_file = create_provider_stream_file(
        "conversation", timestamp, provider_name, prompt, temperature
    )
    update_provider_question(stream_file, prompt)

    # Initialize result structure
    results = {
        "operation": "conversation",
        "prompt": prompt,
        "timestamp": timestamp,
        "provider": provider_name,
        "conversation_file": conversation_file,
        "stream_file": stream_file,
        "response": "",
        "success": True,
    }

    # Execute conversation with streaming
    try:
        # Use call_with_streaming but redirect to /dev/null to avoid old behavior
        ai_response = client.call_with_streaming(
            prompt, conversation_history, "/dev/null", temperature
        )

        # Stream the response word by word (simulated for now)
        words = ai_response.split()
        for i, word in enumerate(words):
            if i == 0:
                stream_to_provider_file(stream_file, word)
            else:
                stream_to_provider_file(stream_file, f" {word}")

        # Add final newline
        stream_to_provider_file(stream_file, "\n\n**CONVERSATION COMPLETE**\n")

        # Save the exchange to conversation file
        session_manager.add_exchange_to_conversation(
            conversation_file, prompt, ai_response, client.get_model_name()
        )

        # Update results
        results["response"] = ai_response

    except Exception as e:
        error_msg = f"Error in conversation: {str(e)}"
        results["error"] = error_msg
        results["success"] = False

        # Stream error to provider file
        stream_to_provider_file(stream_file, f"\n**ERROR**: {error_msg}\n")

    # Save results if requested
    if save_results and results["success"]:
        filepath = _save_conversation_results(results)
        results["json_file"] = filepath

    return results


def _save_conversation_results(results: Dict[str, Any]) -> str:
    """Save conversation results to file"""
    try:
        # Use session manager for consistent directory structure
        conversations_dir = session_manager.get_conversations_directory()

        # Generate filename using the timestamp from results
        timestamp = results.get(
            "timestamp", datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        )
        # Clean up timestamp for filename (remove colons and microseconds)
        clean_timestamp = timestamp.replace(":", "-").split(".")[0]
        filename = f"conversation-{clean_timestamp}.json"
        filepath = Path(conversations_dir) / filename

        # Save results
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        return str(filepath)

    except Exception as e:
        # Don't fail the whole operation if save fails
        return f"Failed to save conversation results: {str(e)}"


def format_conversation_output(results: Dict[str, Any]) -> str:
    """Format conversation results for display"""
    output = []

    output.append("=== LIVE CONVERSATION ===")
    output.append(f"Prompt: {results['prompt']}")
    output.append(f"Provider: {results['provider']}")
    output.append(f"Time: {results['timestamp']}")
    output.append("")

    # Display response
    if results.get("response"):
        output.append("--- AI Response ---")
        output.append(results["response"])
        output.append("")

    # Display error if any
    if results.get("error"):
        output.append("--- ERROR ---")
        output.append(results["error"])
        output.append("")

    output.append("=== CONVERSATION COMPLETE ===")

    return "\n".join(output)
