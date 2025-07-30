"""Brainstorm mission for strategic planning across multiple AI providers"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from ..clients.factory import ClientFactory
from ..storage.manager import storage_manager
from ..streaming import (
    add_response_to_summary,
    create_provider_stream_file,
    create_summary_file,
    finalize_summary,
    generate_mission_timestamp,
    stream_to_provider_file,
    update_provider_question,
)


def execute_brainstorm(
    topic: str,
    context: str = "",
    providers: Optional[str] = None,
    temperature: Optional[float] = None,
    save_results: bool = True,
) -> Dict[str, Any]:
    """
    Execute strategic brainstorming as a group forum conversation.

    Creates a shared conversation where all AIs can hear each other's responses.
    Functions like "4 AIs in a room" with full context sharing and group dynamics.
    All activity is streamed live to separate provider-specific files and shared conversation.

    Args:
        topic: The brainstorming topic for group discussion
        context: Additional context for the brainstorming session
        providers: Comma-separated list of providers ("gemini,openai") or None for all
        temperature: Temperature setting for responses
        save_results: Whether to save results to file

    Returns:
        Dict containing brainstorm results with group conversation and file paths
    """
    timestamp = generate_mission_timestamp()

    # Determine which providers to use
    target_providers = []
    if providers:
        target_providers = [p.strip().lower() for p in providers.split(",")]
    else:
        target_providers = ["gemini", "openai", "anthropic"]

    # Create brainstorm prompt
    brainstorm_prompt = f"Topic: {topic}"
    if context:
        brainstorm_prompt += f"\nContext: {context}"

    # Create or load shared conversation file for this brainstorm topic (JSONL)
    conversation_file = _get_brainstorm_conversation_file(topic)
    conversation_history = storage_manager.read_jsonl(conversation_file)

    # Add initial topic to conversation if this is the first round
    if not conversation_history:
        initial_message = {
            "timestamp": datetime.now().isoformat(),
            "role": "system",
            "content": f"Brainstorm Topic: {topic}"
            + (f"\nContext: {context}" if context else ""),
        }
        storage_manager.append_to_jsonl(conversation_file, initial_message)
        conversation_history = [initial_message]

    # Create summary file
    summary_file = create_summary_file(
        "brainstorm", timestamp, brainstorm_prompt, target_providers, temperature
    )

    # Create provider stream files
    provider_streams = {}
    for provider in target_providers:
        stream_file = create_provider_stream_file(
            "brainstorm", timestamp, provider, brainstorm_prompt, temperature
        )
        provider_streams[provider] = stream_file
        update_provider_question(stream_file, brainstorm_prompt)

    # Initialize result structure
    results: Dict[str, Any] = {
        "mission": "brainstorm",
        "topic": topic,
        "context": context,
        "timestamp": timestamp,
        "target_providers": target_providers,
        "results": {},
        "errors": {},
        "stream_files": provider_streams,
        "summary_file": summary_file,
        "success": True,
    }

    # Execute group forum conversation - simultaneous initial responses
    response_data: Dict[str, Any] = {}

    # Phase 1: Get initial responses from all AIs simultaneously (parallel)
    initial_responses = _execute_initial_ai_panel(
        target_providers,
        brainstorm_prompt,
        conversation_history,
        provider_streams,
        temperature,
    )

    # Add initial responses to conversation file and response data
    for provider_name, response_info in initial_responses.items():
        if "error" not in response_info:
            # Add AI response to shared conversation (JSONL append)
            ai_message = {
                "timestamp": datetime.now().isoformat(),
                "role": f"assistant_{provider_name}",
                "content": response_info["content"],
                "model": response_info["model"],
            }
            storage_manager.append_to_jsonl(conversation_file, ai_message)
            response_data[provider_name] = response_info

            # Add to summary file
            add_response_to_summary(
                summary_file,
                provider_name,
                response_info["content"],
                response_info["model"],
            )
        else:
            results["errors"][provider_name] = response_info["error"]

    # Store conversation file path and compile results
    results["conversation_file"] = conversation_file
    results["results"] = response_data

    # Generate summary
    successful_responses = len(response_data)
    total_attempted = len(target_providers)

    if successful_responses > 0:
        provider_names = list(response_data.keys())
        summary = f"Brainstorming completed: {successful_responses}/{total_attempted} providers responded ({', '.join(provider_names)})"
    else:
        summary = f"Brainstorming failed: No providers available out of {total_attempted} attempted"

    # Finalize summary file
    errors_dict = dict(results["errors"]) if results["errors"] else None
    finalize_summary(summary_file, summary, errors_dict)

    # Save results if requested
    if save_results and successful_responses > 0:
        filepath = _save_brainstorm_results(results)
        results["json_file"] = filepath

    return results


def _get_brainstorm_conversation_file(topic: str) -> str:
    """Get or create shared conversation file for brainstorm topic (JSONL for efficient appending)"""
    # Create topic slug for filename (NO timestamp - same topic = same conversation)
    topic_slug = topic.lower().replace(" ", "-").replace("_", "-")
    # Remove special characters
    topic_slug = re.sub(r"[^a-z0-9-]", "", topic_slug)[:50]  # Limit length

    filename = f"brainstorm-{topic_slug}.jsonl"

    # Use StorageManager to handle conversation file creation
    filepath = storage_manager.create_conversation_file(filename)

    return filepath


def _execute_initial_ai_panel(
    providers: list,
    prompt: str,
    conversation_history: list,
    provider_streams: dict,
    temperature: Optional[float],
) -> Dict[str, Any]:
    """Execute initial AI panel responses simultaneously"""
    import threading

    responses = {}
    threads = []

    def get_ai_response(provider_name: str):
        """Get response from a single AI provider"""
        stream_file = provider_streams[provider_name]

        try:
            client = ClientFactory.create_client(provider_name)
            if not client or not client.is_available():
                responses[provider_name] = {
                    "error": f"Provider {provider_name} not available"
                }
                stream_to_provider_file(
                    stream_file, "\n**ERROR**: Provider not available\n"
                )
                return

            # Use conversation context (group forum style)
            full_response = client.call_with_conversation(
                prompt, conversation_history, temperature
            )

            # Stream the response word by word
            words = full_response.split()
            for i, word in enumerate(words):
                if i == 0:
                    stream_to_provider_file(stream_file, word)
                else:
                    stream_to_provider_file(stream_file, f" {word}")

            stream_to_provider_file(stream_file, "\n\n**BRAINSTORM PANEL COMPLETE**\n")

            responses[provider_name] = {
                "content": full_response,
                "model": client.get_model_name(),
                "display_name": client.get_display_name(),
            }

        except Exception as e:
            error_msg = f"Error querying {provider_name}: {str(e)}"
            responses[provider_name] = {"error": error_msg}
            stream_to_provider_file(stream_file, f"\n**ERROR**: {error_msg}\n")

    # Launch parallel requests
    for provider in providers:
        thread = threading.Thread(target=get_ai_response, args=(provider,))
        thread.start()
        threads.append(thread)

    # Wait for all to complete
    for thread in threads:
        thread.join()

    return responses


def _save_brainstorm_results(results: Dict[str, Any]) -> str:
    """Save brainstorm results to file"""
    try:
        # Use session manager for consistent directory structure
        brainstorm_dir = storage_manager.get_brainstorms_directory()

        # Generate filename using the timestamp from results
        timestamp = results.get(
            "timestamp", datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        )
        # Clean up timestamp for filename (remove colons and microseconds)
        clean_timestamp = timestamp.replace(":", "-").split(".")[0]
        filename = f"brainstorm-{clean_timestamp}.json"
        filepath = Path(brainstorm_dir) / filename

        # Save results
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        return str(filepath)

    except Exception as e:
        # Don't fail the whole operation if save fails
        return f"Failed to save brainstorm results: {str(e)}"


def format_brainstorm_output(results: Dict[str, Any]) -> str:
    """Format brainstorm results for display"""
    output = []

    output.append("=== STRATEGIC BRAINSTORMING ===")
    output.append(f"Topic: {results['topic']}")
    if results.get("context"):
        output.append(f"Context: {results['context']}")
    output.append(f"Time: {results['timestamp']}")
    output.append("")

    # Display responses
    for provider, response_data in results["results"].items():
        display_name = response_data.get("display_name", provider.upper())
        model = response_data.get("model", "unknown")
        content = response_data.get("content", "")

        output.append(f"--- {display_name} ({model}) ---")
        output.append(content)
        output.append("")

    # Display errors if any
    if results["errors"]:
        output.append("--- ERRORS ---")
        for provider, error in results["errors"].items():
            output.append(f"{provider}: {error}")
        output.append("")

    output.append("=== BRAINSTORMING COMPLETE ===")

    return "\n".join(output)
