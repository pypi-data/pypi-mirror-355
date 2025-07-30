"""Single-provider conversation management with context and history"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from ..clients.factory import ClientFactory
from ..storage.manager import storage_manager
from ..streaming import (
    create_provider_stream_file,
    generate_mission_timestamp,
    stream_to_provider_file,
    update_provider_question,
)


class SingleProviderSession:
    """Manages single-provider conversation sessions with context"""

    def __init__(self) -> None:
        """Initialize single provider session manager"""
        self.current_session_file: Optional[str] = None

    def initialize_session(self) -> str:
        """Initialize a new session conversation file"""
        session_filename = storage_manager.generate_session_filename()
        session_file_path = str(
            Path(storage_manager.get_conversations_directory()) / session_filename
        )

        # Create empty conversation file
        if storage_manager.save_conversation(session_file_path, []):
            self.current_session_file = session_file_path
            return session_file_path
        else:
            raise RuntimeError(f"Failed to create session file: {session_file_path}")

    def get_current_session_file(self) -> Optional[str]:
        """Get the current session file path"""
        return self.current_session_file

    def set_current_session_file(self, session_file: str) -> None:
        """Set the current session file path"""
        self.current_session_file = session_file


# Global instance for backward compatibility
single_provider_session = SingleProviderSession()


def execute_conversation(
    mission_prompt: str,
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
        mission_prompt: The message/prompt for the conversation
        conversation_id: Specific conversation to continue (optional)
        provider: AI provider to use (gemini, openai, anthropic)
        temperature: Temperature setting for responses
        save_results: Whether to save results to file

    Returns:
        Dict containing conversation result with response and file paths
    """

    timestamp = generate_mission_timestamp()

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
        conversation_file = storage_manager.get_conversation_file_path(conversation_id)
    else:
        current_session = single_provider_session.get_current_session_file()
        if current_session is None:
            conversation_file = single_provider_session.initialize_session()
        else:
            conversation_file = current_session

    # Get conversation history
    conversation_history = storage_manager.load_conversation(conversation_file)

    # Create stream file
    stream_file = create_provider_stream_file(
        "conversation", timestamp, provider_name, mission_prompt, temperature
    )
    update_provider_question(stream_file, mission_prompt)

    # Initialize result structure
    results = {
        "mission": "conversation",
        "mission_prompt": mission_prompt,
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
            mission_prompt, conversation_history, "/dev/null", temperature
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
        storage_manager.add_exchange_to_conversation(
            conversation_file, mission_prompt, ai_response, client.get_model_name()
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
        # Use storage manager for consistent directory structure
        conversations_dir = storage_manager.get_conversations_directory()

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
    output.append(f"Prompt: {results['mission_prompt']}")
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
