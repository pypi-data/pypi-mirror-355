"""Review mission for code inspection across multiple AI providers"""

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


def execute_review(
    code: str,
    focus: str = "general",
    providers: Optional[str] = None,
    temperature: Optional[float] = None,
    save_results: bool = True,
) -> Dict[str, Any]:
    """
    Execute code review inspection across multiple AI providers.

    Each provider receives the same code and focus area independently.
    This ensures diverse review perspectives without cross-contamination.
    All activity is streamed live to separate provider-specific files.

    Args:
        code: The code to review
        focus: Focus area for the review (general, security, performance, etc.)
        providers: Comma-separated list of providers ("gemini,openai") or None for all
        temperature: Temperature setting for responses
        save_results: Whether to save results to file

    Returns:
        Dict containing review results with responses from each provider and file paths
    """
    timestamp = generate_operation_timestamp()

    # Determine which providers to use
    target_providers = []
    if providers:
        target_providers = [p.strip().lower() for p in providers.split(",")]
    else:
        target_providers = ["gemini", "openai", "anthropic"]

    # Create review prompt
    review_prompt = f"Code Review - Focus: {focus}\n\nCode:\n{code}"

    # Create summary file
    summary_file = create_summary_file(
        "review", timestamp, review_prompt, target_providers, temperature
    )

    # Create provider stream files
    provider_streams = {}
    for provider in target_providers:
        stream_file = create_provider_stream_file(
            "review", timestamp, provider, review_prompt, temperature
        )
        provider_streams[provider] = stream_file
        update_provider_question(stream_file, review_prompt)

    # Initialize result structure
    results: Dict[str, Any] = {
        "operation": "review",
        "code": code,
        "focus": focus,
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
            full_response = client.review_code(code, focus)

            # Stream the response word by word (simulated for now)
            words = full_response.split()
            for i, word in enumerate(words):
                if i == 0:
                    stream_to_provider_file(stream_file, word)
                else:
                    stream_to_provider_file(stream_file, f" {word}")
                response += f" {word}" if i > 0 else word

            # Add final newline
            stream_to_provider_file(stream_file, "\n\n**CODE REVIEW COMPLETE**\n")

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
        summary = f"Code review completed: {successful_responses}/{total_attempted} providers responded ({', '.join(provider_names)})"
    else:
        summary = f"Code review failed: No providers available out of {total_attempted} attempted"

    # Finalize summary file
    errors_dict = dict(results["errors"]) if results["errors"] else None
    finalize_summary(summary_file, summary, errors_dict)

    # Save results if requested
    if save_results and successful_responses > 0:
        filepath = _save_review_results(results)
        results["json_file"] = filepath

    return results


def _save_review_results(results: Dict[str, Any]) -> str:
    """Save review results to file"""
    try:
        # Use session manager for consistent directory structure
        reviews_dir = session_manager.get_reviews_directory()

        # Generate filename using the timestamp from results
        timestamp = results.get(
            "timestamp", datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        )
        # Clean up timestamp for filename (remove colons and microseconds)
        clean_timestamp = timestamp.replace(":", "-").split(".")[0]
        filename = f"review-{clean_timestamp}.json"
        filepath = Path(reviews_dir) / filename

        # Save results
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        return str(filepath)

    except Exception as e:
        # Don't fail the whole operation if save fails
        return f"Failed to save review results: {str(e)}"


def format_review_output(results: Dict[str, Any]) -> str:
    """Format review results for display"""
    output = []

    output.append("=== CODE INSPECTION ===")
    output.append(f"Focus: {results['focus']}")
    output.append(f"Code Length: {len(results['code'])} characters")
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

    output.append("=== CODE REVIEW COMPLETE ===")

    return "\n".join(output)
