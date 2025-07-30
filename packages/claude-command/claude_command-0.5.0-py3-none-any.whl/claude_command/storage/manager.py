"""File system management and storage operations for Claude Command"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from ..settings import settings


class StorageManager:
    """Manages file system operations, directories, and file I/O"""

    def __init__(self) -> None:
        """Initialize storage manager"""
        self.base_dir = self._ensure_base_dir()
        self.conversations_dir = self._ensure_subdir("conversations")
        self.recons_dir = self._ensure_subdir("recons")
        self.brainstorms_dir = self._ensure_subdir("brainstorms")
        self.queries_dir = self._ensure_subdir("queries")
        self.reviews_dir = self._ensure_subdir("reviews")
        self.streams_dir = self._ensure_subdir("streams")
        self.histories_dir = self._ensure_subdir("histories")
        self.sessions_dir = self._ensure_subdir("sessions")

    def _ensure_base_dir(self) -> Path:
        """Ensure base directory exists and return path"""
        base_dir = Path(settings.conversations_dir).expanduser()
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir

    def _ensure_subdir(self, subdir_name: str) -> Path:
        """Ensure subdirectory exists and return path"""
        subdir = self.base_dir / subdir_name
        subdir.mkdir(parents=True, exist_ok=True)
        return subdir

    # Directory getters
    def get_conversations_directory(self) -> str:
        """Get the conversations directory path"""
        return str(self.conversations_dir)

    def get_recons_directory(self) -> str:
        """Get the reconnaissance directory path"""
        return str(self.recons_dir)

    def get_brainstorms_directory(self) -> str:
        """Get the brainstorms directory path"""
        return str(self.brainstorms_dir)

    def get_queries_directory(self) -> str:
        """Get the queries directory path"""
        return str(self.queries_dir)

    def get_reviews_directory(self) -> str:
        """Get the reviews directory path"""
        return str(self.reviews_dir)

    def get_streams_directory(self) -> str:
        """Get the streams directory path"""
        return str(self.streams_dir)

    def get_histories_directory(self) -> str:
        """Get the histories directory path"""
        return str(self.histories_dir)

    def get_sessions_directory(self) -> str:
        """Get the sessions directory path"""
        return str(self.sessions_dir)

    # File operations
    def append_to_jsonl(self, filepath: str, data: Dict[str, Any]) -> bool:
        """Append data to JSONL file"""
        try:
            with open(filepath, "a", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
                f.write("\n")
            return True
        except IOError:
            return False

    def read_jsonl(self, filepath: str) -> List[Dict[str, Any]]:
        """Read JSONL file and return list of entries"""
        if not os.path.exists(filepath):
            return []

        try:
            entries = []
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        entries.append(json.loads(line))
            return entries
        except (json.JSONDecodeError, IOError):
            return []

    def create_conversation_file(self, filename: str) -> str:
        """Create or ensure existence of a conversation file in conversations directory"""
        conversations_dir = self.get_conversations_directory()
        filepath = Path(conversations_dir) / filename

        # Create empty file if it doesn't exist
        if not filepath.exists():
            filepath.touch()

        return str(filepath)

    # Filename generation
    def generate_session_filename(self) -> str:
        """Generate unique session filename with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"session_{timestamp}_{unique_id}.json"

    def generate_conversation_filename(self) -> str:
        """Generate unique conversation filename with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"conversation_{timestamp}_{unique_id}.json"

    # Conversation file operations
    def load_conversation(self, conversation_file: str) -> List[Dict[str, Any]]:
        """Load conversation history from file"""
        if not os.path.exists(conversation_file):
            return []

        try:
            with open(conversation_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError, UnicodeDecodeError):
            return []

    def save_conversation(
        self, conversation_file: str, conversation_history: List[Dict[str, Any]]
    ) -> bool:
        """Save conversation history to file"""
        try:
            with open(conversation_file, "w", encoding="utf-8") as f:
                json.dump(conversation_history, f, indent=2, ensure_ascii=False)
            return True
        except IOError:
            return False

    def add_message_to_conversation(
        self, conversation_file: str, role: str, content: str
    ) -> bool:
        """Add a new message to an existing conversation"""
        conversation_history = self.load_conversation(conversation_file)

        message = {
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content,
        }

        conversation_history.append(message)
        return self.save_conversation(conversation_file, conversation_history)

    def add_exchange_to_conversation(
        self,
        conversation_file: str,
        claude_message: str,
        ai_response: str,
        ai_model: str,
    ) -> bool:
        """Add a complete Claude-AI exchange to conversation"""
        conversation_history = self.load_conversation(conversation_file)

        # Add Claude's message
        claude_msg = {
            "timestamp": datetime.now().isoformat(),
            "role": "claude",
            "content": claude_message,
        }
        conversation_history.append(claude_msg)

        # Add AI's response
        ai_msg = {
            "timestamp": datetime.now().isoformat(),
            "role": "assistant",
            "content": ai_response,
            "model": ai_model,
        }
        conversation_history.append(ai_msg)

        return self.save_conversation(conversation_file, conversation_history)

    # Conversation file management
    def get_conversation_file_path(self, conversation_id: str) -> str:
        """Get full path for a conversation file by ID"""
        if not conversation_id.endswith(".json"):
            conversation_id += ".json"
        return str(self.conversations_dir / conversation_id)

    def list_conversation_files(self) -> List[str]:
        """List all conversation JSON files in the directory"""
        try:
            json_files = [f.name for f in self.conversations_dir.glob("*.json")]
            # Sort by modification time, most recent first
            json_files.sort(
                key=lambda x: os.path.getmtime(self.conversations_dir / x),
                reverse=True,
            )
            return json_files
        except OSError:
            return []

    def get_most_recent_conversation(self) -> str | None:
        """Get the path to the most recent conversation file"""
        conversation_files = self.list_conversation_files()
        if conversation_files:
            return str(self.conversations_dir / conversation_files[0])
        return None

    def format_conversation_history(self, conversation_file: str) -> str:
        """Format conversation history for display"""
        if not os.path.exists(conversation_file):
            return f"Conversation file not found: {os.path.basename(conversation_file)}"

        conversation_history = self.load_conversation(conversation_file)
        if not conversation_history:
            return f"Conversation {os.path.basename(conversation_file)} is empty or could not be loaded."

        # Format the conversation history
        formatted_messages = []
        for msg in conversation_history:
            role = msg.get("role", "unknown").upper()
            content = msg.get("content", "")
            model = msg.get("model", "")
            model_info = f" ({model})" if model else ""
            formatted_messages.append(f"{role}{model_info}:\\n{content}")

        return f"""
CONVERSATION HISTORY - {os.path.basename(conversation_file)}
========================================================================

{chr(10).join(formatted_messages)}

========================================================================
Total messages: {len(conversation_history)}
"""

    def cleanup_old_conversations(self, keep_count: int = 50) -> int:
        """Clean up old conversation files, keeping only the most recent ones"""
        conversation_files = self.list_conversation_files()

        if len(conversation_files) <= keep_count:
            return 0

        files_to_delete = conversation_files[keep_count:]
        deleted_count = 0

        for filename in files_to_delete:
            file_path = self.conversations_dir / filename
            try:
                file_path.unlink()
                deleted_count += 1
            except OSError:
                continue

        return deleted_count


# Global instance
storage_manager = StorageManager()
