"""Mission management for multi-provider conversation context"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..storage.manager import storage_manager


class MissionManager:
    """Manages mission context for multi-provider conversations (used by recon missions)"""

    def __init__(self) -> None:
        """Initialize mission manager"""
        self.mission_session_ids: Dict[str, str] = {}

    def _get_claude_cli_projects_dir(self) -> Path:
        """Get Claude CLI projects directory path"""
        return Path.home() / ".claude" / "projects"

    def _encode_project_path(self, cwd: str) -> str:
        """Convert current working directory to Claude CLI directory format"""
        return cwd.replace("/", "-")

    def _find_most_recent_session_file(self, project_dir: Path) -> Optional[Path]:
        """Find most recent JSONL session file in Claude CLI project directory"""
        if not project_dir.exists():
            return None

        jsonl_files = list(project_dir.glob("*.jsonl"))
        if not jsonl_files:
            return None

        # Sort by modification time, most recent first
        jsonl_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return jsonl_files[0]

    def detect_claude_cli_session(self) -> Optional[str]:
        """Detect current Claude CLI session UUID (non-dependency)"""
        try:
            # Get current working directory
            cwd = os.getcwd()

            # Generate Claude CLI project directory path
            projects_dir = self._get_claude_cli_projects_dir()
            cwd_encoded = self._encode_project_path(cwd)
            project_dir = projects_dir / cwd_encoded

            # Find most recent session file
            most_recent = self._find_most_recent_session_file(project_dir)
            if not most_recent:
                return None

            # Extract UUID from filename
            return most_recent.stem

        except Exception:
            # Never fail core functionality
            return None

    def generate_session_id(self, mission_type: Optional[str] = None) -> str:
        """Generate a new session ID with configurable pattern"""
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

        if mission_type:
            # API-style pattern: mission-{mission_type}-{timestamp}
            return f"mission-{mission_type}-{timestamp}"
        else:
            # Legacy pattern: mission-{timestamp}
            return f"mission-{timestamp}"

    def get_current_session_id(self, mission_type: Optional[str] = None) -> str:
        """Get or create current session ID for specific mission type"""
        if mission_type is None:
            # Legacy support - generate generic session ID
            mission_type = "generic"

        if mission_type not in self.mission_session_ids:
            self.mission_session_ids[mission_type] = self.generate_session_id(
                mission_type
            )

        return self.mission_session_ids[mission_type]

    def get_current_session_dir(self, mission_type: str) -> Path:
        """Get or create current session directory for specific mission type"""
        session_id = self.get_current_session_id(mission_type)
        session_dir = Path(storage_manager.get_missions_directory()) / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir

    def load_session_context(
        self, mission_type: str, provider: str = ""
    ) -> List[Dict[str, Any]]:
        """Load session context for specific mission and provider"""
        session_dir = self.get_current_session_dir(mission_type)

        if provider:
            # Provider-specific context: mission-{mission_type}-{timestamp}/{provider}-context.jsonl
            context_file = session_dir / f"{provider}-context.jsonl"
        else:
            # General mission context: mission-{mission_type}-{timestamp}/context.jsonl
            context_file = session_dir / "context.jsonl"

        return storage_manager.read_jsonl(str(context_file))

    def save_to_session_context(
        self, mission_type: str, provider: str, exchange: Dict[str, Any]
    ) -> bool:
        """Save exchange to session context"""
        session_dir = self.get_current_session_dir(mission_type)
        context_file = session_dir / f"{provider}-context.jsonl"
        return storage_manager.append_to_jsonl(str(context_file), exchange)

    def save_to_complete_history(
        self, mission_type: str, provider: str, exchange: Dict[str, Any]
    ) -> bool:
        """Save exchange to complete history archive"""
        histories_dir = storage_manager.get_histories_directory()
        if provider:
            history_file = (
                Path(histories_dir) / f"{mission_type}-{provider}-complete.jsonl"
            )
        else:
            history_file = Path(histories_dir) / f"{mission_type}-complete.jsonl"

        return storage_manager.append_to_jsonl(str(history_file), exchange)

    # Recon-specific methods
    def load_recon_conversation(self, provider_name: str) -> List[Dict[str, Any]]:
        """Load provider-specific recon conversation (private Claude ↔ AI conversation)"""
        # Load session context for this specific provider
        return self.load_session_context("recon", provider_name)

    def add_recon_exchange(
        self, provider_name: str, mission_prompt: str, response: str, model: str
    ) -> bool:
        """Add recon exchange to both session and complete history"""
        timestamp = datetime.now().isoformat()

        # Detect session IDs for metadata
        session_id_claude_command = self.get_current_session_id("recon")
        session_id_claude_cli = self.detect_claude_cli_session()

        # Create exchange data with session metadata
        user_exchange = {
            "timestamp": timestamp,
            "session_id_claude_command": session_id_claude_command,
            "session_id_claude_cli": session_id_claude_cli
            if session_id_claude_cli
            else "not_detected",
            "role": "user",
            "content": mission_prompt,
        }

        assistant_exchange = {
            "timestamp": timestamp,
            "session_id_claude_command": session_id_claude_command,
            "session_id_claude_cli": session_id_claude_cli
            if session_id_claude_cli
            else "not_detected",
            "role": "assistant",
            "content": response,
            "model": model,
        }

        # Save to both session context (for private conversations) AND complete history (for archive)
        # Session context: Private Claude <-> AI conversation
        session_success1 = self.save_to_session_context(
            "recon", provider_name, user_exchange
        )
        session_success2 = self.save_to_session_context(
            "recon", provider_name, assistant_exchange
        )

        # Complete history: Permanent archive
        history_success1 = self.save_to_complete_history(
            "recon", provider_name, user_exchange
        )
        history_success2 = self.save_to_complete_history(
            "recon", provider_name, assistant_exchange
        )

        return all(
            [session_success1, session_success2, history_success1, history_success2]
        )

    # Review-specific methods
    def load_review_conversation(self, provider_name: str) -> List[Dict[str, Any]]:
        """Load provider-specific review conversation for iterative code feedback"""
        # Load session context for this specific provider
        return self.load_session_context("review", provider_name)

    def add_review_exchange(
        self, provider_name: str, code: str, focus: str, response: str, model: str
    ) -> bool:
        """Add review exchange to both session and complete history"""
        timestamp = datetime.now().isoformat()

        # Detect session IDs for metadata
        session_id_claude_command = self.get_current_session_id("review")
        session_id_claude_cli = self.detect_claude_cli_session()

        # Create review prompt
        review_prompt = f"Code Review - Focus: {focus}\n\nCode:\n{code}"

        # Create exchange data with session metadata
        user_exchange = {
            "timestamp": timestamp,
            "session_id_claude_command": session_id_claude_command,
            "session_id_claude_cli": session_id_claude_cli
            if session_id_claude_cli
            else "not_detected",
            "role": "user",
            "content": review_prompt,
        }

        assistant_exchange = {
            "timestamp": timestamp,
            "session_id_claude_command": session_id_claude_command,
            "session_id_claude_cli": session_id_claude_cli
            if session_id_claude_cli
            else "not_detected",
            "role": "assistant",
            "content": response,
            "model": model,
        }

        # Save to both session context and complete history
        session_success1 = self.save_to_session_context(
            "review", provider_name, user_exchange
        )
        session_success2 = self.save_to_session_context(
            "review", provider_name, assistant_exchange
        )

        history_success1 = self.save_to_complete_history(
            "review", provider_name, user_exchange
        )
        history_success2 = self.save_to_complete_history(
            "review", provider_name, assistant_exchange
        )

        return all(
            [session_success1, session_success2, history_success1, history_success2]
        )


# Global instance
mission_manager = MissionManager()
