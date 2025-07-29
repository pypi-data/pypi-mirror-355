"""Multi-file streaming infrastructure for thread-safe parallel AI responses"""

import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .sessions import session_manager

# Global file locks to prevent threading collisions
_file_locks: Dict[str, threading.Lock] = {}
_locks_lock = threading.Lock()


def _get_file_lock(filepath: str) -> threading.Lock:
    """Get or create a thread lock for a specific file"""
    with _locks_lock:
        if filepath not in _file_locks:
            _file_locks[filepath] = threading.Lock()
        return _file_locks[filepath]


def _format_yaml_list(items: List[str]) -> str:
    """Format a Python list as proper YAML list"""
    if not items:
        return "  []\n"
    return "".join(f"  - {item}\n" for item in items)


def _format_yaml_dict(d: Dict[str, str]) -> str:
    """Format a Python dict as proper YAML dict"""
    if not d:
        return "  {}\n"
    return "".join(f"  {key}: {value}\n" for key, value in d.items())


def parse_providers_parameter(providers: Optional[str] = None) -> List[str]:
    """Parse providers parameter and return list of target providers"""
    if providers:
        return [p.strip().lower() for p in providers.split(",")]
    else:
        return ["gemini", "openai", "anthropic"]


def generate_operation_timestamp() -> str:
    """Generate timestamp for operation files"""
    return datetime.now().strftime("%Y-%m-%d-%H-%M-%S")


def create_provider_stream_file(
    operation: str,
    timestamp: str,
    provider: str,
    survey_prompt: str = "",
    temperature: Optional[float] = None,
) -> str:
    """Create and initialize a provider-specific stream file with front matter"""
    filename = f"{operation}-{timestamp}-{provider}.md"
    filepath = Path(session_manager.get_live_streams_directory()) / filename

    # Provider metadata
    provider_metadata = {
        "gemini": {"display_name": "Gemini 2.0 Flash", "model": "gemini-2.0-flash-exp"},
        "openai": {"display_name": "GPT-4", "model": "gpt-4"},
        "anthropic": {
            "display_name": "Claude 3.5 Sonnet",
            "model": "claude-3-5-sonnet-20241022",
        },
    }

    metadata = provider_metadata.get(
        provider, {"display_name": provider.title(), "model": "unknown"}
    )
    display_name = metadata["display_name"]
    model = metadata["model"]

    # Parse timestamp for front matter
    from datetime import datetime

    # Convert timestamp format: 2025-06-15-01-13-13 -> 2025-06-15T01:13:13
    timestamp_iso = timestamp[:10] + "T" + timestamp[11:].replace("-", ":")
    dt = datetime.fromisoformat(timestamp_iso)
    date_str = dt.strftime("%Y-%m-%d")
    time_str = dt.strftime("%H:%M:%S")

    with _get_file_lock(str(filepath)):
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"""---
# Operation Metadata
operation: "{operation}"
commander: "Claude Code"
timestamp: "{dt.isoformat()}"
date: "{date_str}"
time: "{time_str}"
session_id: "{operation}-{timestamp}"

# Provider Details
provider: "{provider}"
model: "{model}"
display_name: "{display_name}"

# Survey Details
survey_prompt: "{survey_prompt}"
temperature: {temperature}

# File Details
file_type: "provider_stream"
streaming: true
file_format: "markdown"
---

# {display_name} - {operation.title()}

## Survey Question
Loading...

## Response

""")
            f.flush()

    return str(filepath)


def update_provider_question(filepath: str, question: str) -> None:
    """Update the survey question in provider stream file"""
    with _get_file_lock(filepath):
        # Read current content
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Replace the loading placeholder
        content = content.replace("Loading...", question)

        # Write back updated content
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()


def stream_to_provider_file(filepath: str, content: str) -> None:
    """Stream content to provider-specific file (word by word streaming)"""
    with _get_file_lock(filepath):
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(content)
            f.flush()


def create_summary_file(
    operation: str,
    timestamp: str,
    question: str,
    providers: Optional[List[str]] = None,
    temperature: Optional[float] = None,
) -> str:
    """Create and initialize summary file with comprehensive front matter"""
    filename = f"{operation}-{timestamp}-summary.md"
    filepath = Path(session_manager.get_live_streams_directory()) / filename

    # Parse timestamp for front matter
    from datetime import datetime

    # Convert timestamp format: 2025-06-15-01-13-13 -> 2025-06-15T01:13:13
    timestamp_iso = timestamp[:10] + "T" + timestamp[11:].replace("-", ":")
    dt = datetime.fromisoformat(timestamp_iso)
    date_str = dt.strftime("%Y-%m-%d")
    time_str = dt.strftime("%H:%M:%S")

    # Generate tmux helper command for actual providers used
    tmux_helper = generate_tmux_helper(operation, timestamp, providers)

    # Providers metadata
    provider_models = {
        "gemini": "gemini-2.0-flash-exp",
        "openai": "gpt-4",
        "anthropic": "claude-3-5-sonnet-20241022",
    }

    providers_with_models = []
    for provider in providers or []:
        model = provider_models.get(provider, "unknown")
        providers_with_models.append({"provider": provider, "model": model})

    with _get_file_lock(str(filepath)):
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"""---
# Operation Metadata
operation: "{operation}"
commander: "Claude Code"
timestamp: "{dt.isoformat()}"
date: "{date_str}"
time: "{time_str}"
session_id: "{operation}-{timestamp}"

# Survey Details
survey_prompt: "{question}"
temperature: {temperature}

# Provider Configuration
providers_requested:
{_format_yaml_list(providers or [])}total_providers_requested: {len(providers) if providers else 0}
provider_models:
{_format_yaml_dict(provider_models)}

# Execution Details
file_type: "summary"
streaming: true
file_format: "markdown"
multi_pane_viewing: true

# Results (to be updated)
providers_responded: []
successful_responses: 0
failed_responses: 0
response_rate: "0%"
execution_status: "in_progress"
---

# {operation.title()} - {timestamp}

## Survey Question
{question}

## Multi-Pane Viewing (Optional)
To watch all provider responses in real-time, copy and paste this command:

```bash
{tmux_helper}
```

## Provider Responses

""")
            f.flush()

    return str(filepath)


def add_response_to_summary(
    summary_filepath: str, provider: str, response: str, model: str
) -> None:
    """Add completed response to summary file with Markdown formatting"""
    provider_display_names = {
        "gemini": "Gemini 2.0 Flash",
        "openai": "GPT-4",
        "anthropic": "Claude 3.5 Sonnet",
    }

    display_name = provider_display_names.get(provider, provider.title())

    with _get_file_lock(summary_filepath):
        with open(summary_filepath, "a", encoding="utf-8") as f:
            f.write(f"### {display_name} ({model})\n")
            f.write("<details>\n")
            f.write("<summary>Click to expand response</summary>\n\n")
            f.write(f"{response}\n\n")
            f.write("</details>\n\n")
            f.flush()


def finalize_summary(
    summary_filepath: str, status: str, errors: Optional[Dict[str, str]] = None
) -> None:
    """Add final summary section to summary file"""
    with _get_file_lock(summary_filepath):
        with open(summary_filepath, "a", encoding="utf-8") as f:
            f.write("## Reconnaissance Summary\n")
            f.write(f"- **Status**: {status}\n")

            if errors:
                f.write(f"- **Errors**: {len(errors)} encountered\n")
                for provider, error in errors.items():
                    f.write(f"  - {provider}: {error}\n")

            f.write("\n---\n")
            f.flush()


def generate_tmux_helper(
    operation: str, timestamp: str, providers: Optional[List[str]] = None
) -> str:
    """Generate tmux command for user documentation (not execution)"""
    streams_dir = session_manager.get_live_streams_directory()
    session_name = f"{operation}_{timestamp}"

    # Use provided providers or default to all
    if not providers:
        providers = ["gemini", "openai", "anthropic"]

    # Generate pane commands for actual providers used
    pane_commands = []
    for i, provider in enumerate(providers):
        pane_commands.append(
            f"  send-keys -t {i} 'tail -f {streams_dir}/{operation}-{timestamp}-{provider}.md' Enter"
        )

    # Add summary pane
    summary_pane = len(providers)
    pane_commands.append(
        f"  send-keys -t {summary_pane} 'tail -f {streams_dir}/{operation}-{timestamp}-summary.md' Enter"
    )

    # Generate split commands based on number of providers
    # Always need at least one split for the summary pane
    split_commands = []

    if len(providers) == 1:
        # Single provider: just split horizontally for summary
        split_commands.append("  split-window -h")
    elif len(providers) == 2:
        # Two providers + summary = 3 panes
        split_commands.append("  split-window -h")
        split_commands.append("  select-pane -t 0")
        split_commands.append("  split-window -v")
    elif len(providers) >= 3:
        # Three providers + summary = 4 panes (2x2 grid)
        split_commands.append("  split-window -h")
        split_commands.append("  split-window -v")
        split_commands.append("  select-pane -t 0")
        split_commands.append("  split-window -v")

    # Build the command with proper line continuations
    split_cmd_str = " \\; \\\n".join(split_commands) if split_commands else ""
    pane_cmd_str = " \\; \\\n".join(pane_commands)

    cmd = f"""tmux kill-session -t {session_name} 2>/dev/null || true && \\
tmux new-session -s {session_name}"""

    if split_commands:
        cmd += f" \\; \\\n{split_cmd_str}"

    cmd += f" \\; \\\n{pane_cmd_str}"

    cmd += f"""

# If session already exists, attach to it:
# tmux attach-session -t {session_name}"""

    return cmd


def cleanup_old_streams(operation: str, keep_count: int = 10) -> int:
    """Clean up old stream files for a specific operation"""
    streams_dir = Path(session_manager.get_live_streams_directory())

    # Find all files for this operation
    pattern = f"{operation}_*"
    files = list(streams_dir.glob(pattern))

    if len(files) <= keep_count * 4:  # 4 files per operation (3 providers + summary)
        return 0

    # Sort by modification time, oldest first
    files.sort(key=lambda x: x.stat().st_mtime)

    # Keep the most recent operations
    files_to_delete = files[: -keep_count * 4]
    deleted_count = 0

    for file_path in files_to_delete:
        try:
            file_path.unlink()
            deleted_count += 1
        except OSError:
            continue

    return deleted_count
