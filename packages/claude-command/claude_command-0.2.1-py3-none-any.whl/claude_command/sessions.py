"""Session management for conversation storage and file operations"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .settings import settings


class SessionManager:
    """Manages conversation storage, sessions, and file operations"""

    def __init__(self):
        """Initialize session manager"""
        self.base_dir = self._ensure_base_dir()
        self.conversations_dir = self._ensure_subdir("conversations")
        self.recon_dir = self._ensure_subdir("recon")
        self.brainstorm_dir = self._ensure_subdir("brainstorm")
        self.queries_dir = self._ensure_subdir("queries")
        self.reviews_dir = self._ensure_subdir("reviews")
        self.live_streams_dir = self._ensure_subdir("live-streams")
        self.current_session_file: Optional[str] = None

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

    def get_conversations_directory(self) -> str:
        """Get the conversations directory path"""
        return str(self.conversations_dir)

    def get_recon_directory(self) -> str:
        """Get the reconnaissance directory path"""
        return str(self.recon_dir)

    def get_brainstorm_directory(self) -> str:
        """Get the brainstorm directory path"""
        return str(self.brainstorm_dir)

    def get_queries_directory(self) -> str:
        """Get the queries directory path"""
        return str(self.queries_dir)

    def get_reviews_directory(self) -> str:
        """Get the reviews directory path"""
        return str(self.reviews_dir)

    def get_live_streams_directory(self) -> str:
        """Get the live streams directory path"""
        return str(self.live_streams_dir)

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

    def initialize_session(self) -> str:
        """Initialize a new session conversation file"""
        session_filename = self.generate_session_filename()
        session_file_path = str(self.conversations_dir / session_filename)

        # Create empty conversation file
        if self.save_conversation(session_file_path, []):
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

    def get_most_recent_conversation(self) -> Optional[str]:
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
            formatted_messages.append(f"{role}{model_info}:\n{content}")

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

    def get_recon_conversation_file(self, provider_name: str) -> str:
        """Get conversation file path for specific provider in recon mode"""
        filename = f"recon-{provider_name}-conversation.json"
        return str(self.recon_dir / "conversations" / filename)

    def _ensure_recon_conversations_dir(self) -> Path:
        """Ensure recon conversations subdirectory exists"""
        recon_conversations_dir = self.recon_dir / "conversations"
        recon_conversations_dir.mkdir(parents=True, exist_ok=True)
        return recon_conversations_dir

    def load_recon_conversation(self, provider_name: str) -> List[Dict[str, Any]]:
        """Load conversation history for specific provider"""
        self._ensure_recon_conversations_dir()
        conversation_file = self.get_recon_conversation_file(provider_name)

        if not os.path.exists(conversation_file):
            return []

        try:
            with open(conversation_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("messages", [])
        except (json.JSONDecodeError, IOError, UnicodeDecodeError):
            return []

    def save_recon_conversation(
        self, provider_name: str, conversation: List[Dict[str, Any]]
    ) -> bool:
        """Save conversation history for specific provider"""
        try:
            self._ensure_recon_conversations_dir()
            conversation_file = self.get_recon_conversation_file(provider_name)

            conversation_data = {
                "provider": provider_name,
                "conversation_id": f"recon-{provider_name}",
                "created": datetime.now().isoformat()
                if not os.path.exists(conversation_file)
                else None,
                "updated": datetime.now().isoformat(),
                "messages": conversation,
            }

            # If file exists, preserve the created timestamp
            if os.path.exists(conversation_file):
                try:
                    with open(conversation_file, "r", encoding="utf-8") as f:
                        existing_data = json.load(f)
                        conversation_data["created"] = existing_data.get("created")
                except (json.JSONDecodeError, IOError):
                    pass

            with open(conversation_file, "w", encoding="utf-8") as f:
                json.dump(conversation_data, f, indent=2, ensure_ascii=False)
            return True
        except IOError:
            return False

    def add_recon_exchange(
        self, provider_name: str, prompt: str, response: str, model: str
    ) -> bool:
        """Add prompt-response exchange to provider's conversation history"""
        conversation_history = self.load_recon_conversation(provider_name)

        # Add user message
        user_message = {
            "timestamp": datetime.now().isoformat(),
            "role": "user",
            "content": prompt,
        }
        conversation_history.append(user_message)

        # Add assistant response
        assistant_message = {
            "timestamp": datetime.now().isoformat(),
            "role": "assistant",
            "content": response,
            "model": model,
        }
        conversation_history.append(assistant_message)

        return self.save_recon_conversation(provider_name, conversation_history)


# Global instance
session_manager = SessionManager()
