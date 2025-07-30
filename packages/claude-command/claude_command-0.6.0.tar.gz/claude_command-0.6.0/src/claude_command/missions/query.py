"""Query mission for intelligence gathering across multiple AI providers"""

import json
import threading
from pathlib import Path
from typing import Any, Dict, Optional

from ..clients.factory import ClientFactory
from ..storage.manager import storage_manager
from ..storage.naming import extract_subject_from_prompt, generate_mission_filename
from ..streaming import (
    add_response_to_summary,
    create_provider_stream_file,
    create_summary_file,
    finalize_summary,
    generate_mission_timestamp,
    stream_to_provider_file,
    update_provider_question,
)


def execute_query(
    mission_prompt: str,
    providers: Optional[str] = None,
    temperature: Optional[float] = None,
    save_results: bool = True,
) -> Dict[str, Any]:
    """
    Execute intelligence gathering query across multiple AI providers.

    Each provider receives the same prompt with zero context or conversation history.
    This ensures unbiased, independent responses for comparison.
    All activity is streamed live to separate provider-specific files.

    Args:
        mission_prompt: The question/prompt to query across providers
        providers: Comma-separated list of providers ("gemini,openai") or None for all
        temperature: Temperature setting for responses
        save_results: Whether to save results to file

    Returns:
        Dict containing query results with responses from each provider and file paths
    """
    timestamp = generate_mission_timestamp()
    subject = extract_subject_from_prompt(mission_prompt)

    # Determine which providers to use
    target_providers = []
    if providers:
        target_providers = [p.strip().lower() for p in providers.split(",")]
    else:
        target_providers = ["gemini", "openai", "anthropic"]

    # Create summary file
    summary_file = create_summary_file(
        "query", subject, timestamp, mission_prompt, target_providers, temperature
    )

    # Create provider stream files
    provider_streams = {}
    for provider in target_providers:
        stream_file = create_provider_stream_file(
            "query", subject, timestamp, provider, mission_prompt, temperature
        )
        provider_streams[provider] = stream_file
        update_provider_question(stream_file, mission_prompt)

    # Initialize result structure
    results: Dict[str, Any] = {
        "mission": "query",
        "mission_prompt": mission_prompt,
        "timestamp": timestamp,
        "target_providers": target_providers,
        "results": {},
        "errors": {},
        "stream_files": provider_streams,
        "summary_file": summary_file,
        "success": True,
    }

    # Pre-initialize all clients in main thread to avoid gRPC threading issues
    clients = {}
    for provider in target_providers:
        client = ClientFactory.create_client(provider)
        if client and client.is_available():
            clients[provider] = client
        else:
            results["errors"][provider] = f"Provider {provider} not available"

    # Execute query across providers in parallel
    threads = []
    response_data: Dict[str, Any] = {}

    def query_provider(provider_name: str):
        """Query a single provider independently with live streaming to separate file"""
        stream_file = provider_streams[provider_name]

        try:
            # Use pre-initialized client
            client = clients.get(provider_name)
            if not client:
                error_msg = f"Provider {provider_name} not available"
                results["errors"][provider_name] = error_msg

                # Stream error to provider file
                stream_to_provider_file(stream_file, f"\n**ERROR**: {error_msg}\n")
                return

            # Execute independent query with streaming
            response = ""
            # For now, get the full response and simulate streaming
            # TODO: Implement true word-by-word streaming in client methods
            full_response = client.call_simple(mission_prompt, temperature)

            # Stream the response word by word (simulated for now)
            words = full_response.split()
            for i, word in enumerate(words):
                if i == 0:
                    stream_to_provider_file(stream_file, word)
                else:
                    stream_to_provider_file(stream_file, f" {word}")
                response += f" {word}" if i > 0 else word

            # Add final newline
            stream_to_provider_file(stream_file, "\n\n**QUERY COMPLETE**\n")

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

    # Launch parallel queries (only for providers with successful clients)
    for provider in clients.keys():
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
        summary = f"Query completed: {successful_responses}/{total_attempted} providers responded ({', '.join(provider_names)})"
    else:
        summary = (
            f"Query failed: No providers available out of {total_attempted} attempted"
        )

    # Finalize summary file
    errors_dict = dict(results["errors"]) if results["errors"] else None
    finalize_summary(summary_file, summary, errors_dict)

    # Save results if requested
    if save_results and successful_responses > 0:
        filepath = _save_query_results(results, subject, timestamp)
        results["json_file"] = filepath

        # Add to mission index for discoverability
        storage_manager.add_mission_to_index(
            mission_type="query",
            subject=subject.replace("-", " ").title(),
            subject_slug=subject,
            timestamp=timestamp,
            mission_prompt=mission_prompt,
            providers=target_providers,
            result_files={
                "main": filepath,
                "summary": summary_file,
                **provider_streams,
            },
        )

    return results


def _save_query_results(results: Dict[str, Any], subject: str, timestamp: str) -> str:
    """Save query results to file"""
    try:
        # Use session manager for consistent directory structure
        queries_dir = storage_manager.get_queries_directory()

        # Generate filename using unified naming pattern
        filename = generate_mission_filename("query", subject, timestamp, "json")
        filepath = Path(queries_dir) / filename

        # Save results
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        return str(filepath)

    except Exception as e:
        # Don't fail the whole operation if save fails
        return f"Failed to save query results: {str(e)}"


def format_query_output(results: Dict[str, Any]) -> str:
    """Format query results for display"""
    output = []

    output.append("=== INTELLIGENCE GATHERING ===")
    output.append(f"Query: {results['mission_prompt']}")
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

    output.append("=== QUERY COMPLETE ===")

    return "\n".join(output)
