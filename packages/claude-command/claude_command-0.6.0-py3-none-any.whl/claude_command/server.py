"""Claude Command MCP Server - Real-time AI Command Center with fastMCP"""

import os
from importlib.metadata import version
from typing import Any, Dict

from fastmcp import FastMCP

from .clients.factory import ClientFactory, create_available_clients, get_primary_client
from .dialog.single import execute_topic
from .missions import (
    execute_brainstorm,
    execute_query,
    execute_recon,
    execute_review,
    format_recon_output,
)
from .settings import settings
from .storage.manager import storage_manager
from .storage.naming import extract_subject_from_prompt

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
    mission_prompt: str,
    topic_id: str = "",
    temperature: float = 0.7,
    provider: str = "",
    providers: str = "",
    save_results: bool = True,
) -> Dict[str, Any]:
    """Claude Command: Execute live multi-provider AI conversations with real-time streaming across Gemini, OpenAI, and Anthropic."""

    try:
        # If providers parameter is used, delegate to query mission
        if providers:
            return execute_query(mission_prompt, providers, temperature, save_results)

        # Single provider logic - delegate to topic mission
        return execute_topic(
            mission_prompt, topic_id, provider, temperature, save_results
        )

    except Exception as e:
        return {"error": f"Error during query: {str(e)}", "success": False}


@mcp.tool
def claude_command_topic_history(topic_id: str = "") -> Dict[str, Any]:
    """Claude Command: Retrieve formatted topic history from saved multi-provider AI sessions."""

    try:
        if topic_id:
            # Use specified topic ID
            topic_file = storage_manager.get_topic_file_path(topic_id)
        else:
            # Get most recent topic file
            recent_topic = storage_manager.get_most_recent_topic()
            if recent_topic is None:
                return {"error": "No topics found.", "success": False}
            topic_file = recent_topic
            topic_id = os.path.basename(topic_file)

        if not os.path.exists(topic_file):
            return {
                "error": f"Topic file not found: {topic_id}",
                "success": False,
            }

        formatted_history = storage_manager.format_topic_history(topic_file)

        return {
            "topic_history": formatted_history,
            "topic_id": topic_id,
            "success": True,
        }

    except Exception as e:
        return {
            "error": f"Error retrieving topic history: {str(e)}",
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
                generate_mission_timestamp,
                stream_to_provider_file,
            )

            timestamp = generate_mission_timestamp()
            subject = extract_subject_from_prompt(f"Code review: {focus}")
            provider_name = client.get_display_name().lower().replace(" ", "-")

            # Create review prompt for streaming
            review_prompt = f"Code Review - Focus: {focus}\n\nCode:\n{code}"

            # Create stream file
            streaming_file = create_provider_stream_file(
                "review", subject, timestamp, provider_name, review_prompt, temperature
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
                generate_mission_timestamp,
                stream_to_provider_file,
            )

            timestamp = generate_mission_timestamp()
            subject = extract_subject_from_prompt(topic)
            provider_name = client.get_display_name().lower().replace(" ", "-")

            # Create brainstorm prompt for streaming
            brainstorm_prompt = f"Topic: {topic}"
            if context:
                brainstorm_prompt += f"\nContext: {context}"

            # Create stream file
            streaming_file = create_provider_stream_file(
                "brainstorm",
                subject,
                timestamp,
                provider_name,
                brainstorm_prompt,
                temperature,
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
            "server_version": version("claude-command"),
            "status": "running",
            "default_client": default_client.get_display_name()
            if default_client
            else None,
            "available_clients": client_info,
            "total_clients": len(clients),
            "topics_directory": storage_manager.get_topics_directory(),
            "streams_directory": storage_manager.get_streams_directory(),
            "has_api_keys": settings.has_valid_api_key(),
            "settings": {
                "topics_dir": settings.topics_dir,
                "default_temperature": settings.default_temperature,
                "max_history_length": settings.max_history_length,
                "user_name": settings.user_name,
            },
            "success": True,
        }

    except Exception as e:
        return {"error": f"Error getting server status: {str(e)}", "success": False}


@mcp.tool
def claude_command_topics_list() -> Dict[str, Any]:
    """Claude Command: List all saved multi-provider topic files with timestamps and metadata."""

    try:
        topic_files = storage_manager.list_topic_files()

        return {
            "topic_files": topic_files,
            "total_topics": len(topic_files),
            "topics_directory": storage_manager.get_topics_directory(),
            "success": True,
        }

    except Exception as e:
        return {"error": f"Error listing topics: {str(e)}", "success": False}


@mcp.tool
def claude_command_topics_cleanup(keep_count: int = 50) -> Dict[str, Any]:
    """Claude Command: Remove old topic files while preserving recent multi-provider session data."""

    try:
        deleted_count = storage_manager.cleanup_old_topics(keep_count)

        return {
            "deleted_topics": deleted_count,
            "kept_topics": keep_count,
            "success": True,
        }

    except Exception as e:
        return {"error": f"Error cleaning up topics: {str(e)}", "success": False}


@mcp.tool
def claude_command_topics_search(query: str) -> Dict[str, Any]:
    """Claude Command: Search within topic files for accumulated knowledge across all missions."""

    try:
        matching_topics = storage_manager.search_topics(query)

        return {
            "matching_topics": matching_topics,
            "search_query": query,
            "total_matches": len(matching_topics),
            "success": True,
        }

    except Exception as e:
        return {"error": f"Error searching topics: {str(e)}", "success": False}


@mcp.tool
def claude_command_missions_list(mission_type: str = "") -> Dict[str, Any]:
    """Claude Command: List all saved mission runs with metadata, optionally filtered by mission type (recon, brainstorm, review, query)."""

    try:
        if mission_type:
            missions = storage_manager.list_missions_by_type(mission_type.lower())
            return {
                "missions": missions,
                "mission_type_filter": mission_type.lower(),
                "total_missions": len(missions),
                "success": True,
            }
        else:
            missions = storage_manager.list_missions_by_type()
            return {
                "missions": missions,
                "total_missions": len(missions),
                "success": True,
            }

    except Exception as e:
        return {"error": f"Error listing mission runs: {str(e)}", "success": False}


@mcp.tool
def claude_command_missions_search(
    query: str, search_content: bool = True
) -> Dict[str, Any]:
    """Claude Command: Search mission runs by subject, mission prompt content, and optionally response content."""

    try:
        matching_missions = storage_manager.search_missions(query, search_content)

        return {
            "matching_missions": matching_missions,
            "search_query": query,
            "search_content": search_content,
            "total_matches": len(matching_missions),
            "success": True,
        }

    except Exception as e:
        return {"error": f"Error searching mission runs: {str(e)}", "success": False}


@mcp.tool
def claude_command_missions_rebuild_index() -> Dict[str, Any]:
    """Claude Command: Rebuild the mission index by scanning all mission directories."""

    try:
        mission_count = storage_manager.rebuild_missions_index()

        return {
            "rebuilt_missions": mission_count,
            "message": f"Mission index rebuilt with {mission_count} mission runs",
            "success": True,
        }

    except Exception as e:
        return {"error": f"Error rebuilding mission index: {str(e)}", "success": False}


@mcp.tool
def claude_command_recon(
    mission_prompt: str,
    providers: str = "gemini,openai,anthropic",
    temperature: float = 0.5,
    save_results: bool = True,
) -> Dict[str, Any]:
    """Claude Command: Survey multiple AI providers independently to gather unbiased comparative intelligence for your analysis."""

    try:
        # Execute the reconnaissance
        results = execute_recon(mission_prompt, providers, temperature, save_results)

        # Format output for display
        formatted_output = format_recon_output(results)

        return {
            "mission_prompt": mission_prompt,
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
