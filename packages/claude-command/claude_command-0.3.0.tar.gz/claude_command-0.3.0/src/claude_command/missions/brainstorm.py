"""Brainstorm mission for strategic planning across multiple AI providers"""

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from ..clients.factory import ClientFactory
from ..sessions import session_manager
from ..streaming import (
    add_response_to_summary,
    create_provider_stream_file,
    create_summary_file,
    finalize_summary,
    generate_operation_timestamp,
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
    Execute strategic brainstorming across multiple AI providers.

    Each provider receives the same brainstorming prompt independently.
    This ensures diverse perspectives and creative approaches without cross-contamination.
    All activity is streamed live to separate provider-specific files.

    Args:
        topic: The brainstorming topic
        context: Additional context for the brainstorming session
        providers: Comma-separated list of providers ("gemini,openai") or None for all
        temperature: Temperature setting for responses
        save_results: Whether to save results to file

    Returns:
        Dict containing brainstorm results with responses from each provider and file paths
    """
    timestamp = generate_operation_timestamp()

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
        "operation": "brainstorm",
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

    # Execute recon across providers in parallel
    threads = []
    response_data: Dict[str, Any] = {}

    def query_provider(provider_name: str):
        """Query a single provider independently with live streaming to separate file"""
        stream_file = provider_streams[provider_name]

        try:
            client = ClientFactory.create_client(provider_name)
            if not client or not client.is_available():
                error_msg = f"Provider {provider_name} not available"
                results["errors"][provider_name] = error_msg

                # Stream error to provider file
                stream_to_provider_file(stream_file, f"\n**ERROR**: {error_msg}\n")
                return

            # Execute independent query with streaming
            response = ""
            # For now, get the full response and simulate streaming
            # TODO: Implement true word-by-word streaming in client methods
            full_response = client.brainstorm(topic, context)

            # Stream the response word by word (simulated for now)
            words = full_response.split()
            for i, word in enumerate(words):
                if i == 0:
                    stream_to_provider_file(stream_file, word)
                else:
                    stream_to_provider_file(stream_file, f" {word}")
                response += f" {word}" if i > 0 else word

            # Add final newline
            stream_to_provider_file(stream_file, "\n\n**BRAINSTORMING COMPLETE**\n")

            response_data[provider_name] = {
                "content": full_response,
                "model": client.get_model_name(),
                "display_name": client.get_display_name(),
            }

            # Add to summary file
            add_response_to_summary(
                summary_file, provider_name, full_response, client.get_model_name()
            )

        except Exception as e:
            error_msg = f"Error querying {provider_name}: {str(e)}"
            results["errors"][provider_name] = error_msg

            # Stream error to provider file
            stream_to_provider_file(stream_file, f"\n**ERROR**: {error_msg}\n")

    # Launch parallel queries
    for provider in target_providers:
        thread = threading.Thread(target=query_provider, args=(provider,))
        thread.start()
        threads.append(thread)

    # Wait for all queries to complete
    for thread in threads:
        thread.join()

    # Compile results
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


def _save_brainstorm_results(results: Dict[str, Any]) -> str:
    """Save brainstorm results to file"""
    try:
        # Use session manager for consistent directory structure
        brainstorm_dir = session_manager.get_brainstorm_directory()

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
