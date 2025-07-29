#!/usr/bin/env python3
"""
Session management module for Claude-Gemini MCP Server
Handles conversation sessions, storage, and file I/O operations
"""

import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from .config import (
    CONVERSATION_FILE_PREFIX,
    LIVE_STREAM_FILENAME,
    SESSION_FILE_PREFIX,
    get_conversations_dir,
)


class SessionManager:
    """Manages conversation storage, sessions, and file operations"""

    def __init__(self):
        """Initialize conversation manager"""
        self.conversations_dir = self._ensure_conversations_dir()
        self.current_session_file: Optional[str] = None

    def _ensure_conversations_dir(self) -> str:
        """Ensure conversations directory exists and return path"""
        conversations_dir = get_conversations_dir()
        os.makedirs(conversations_dir, exist_ok=True)
        return conversations_dir

    def get_conversations_directory(self) -> str:
        """Get the conversations directory path"""
        return self.conversations_dir

    def get_live_stream_path(self) -> str:
        """Get the path to the live stream file"""
        return os.path.join(self.conversations_dir, LIVE_STREAM_FILENAME)

    def generate_session_filename(self) -> str:
        """Generate unique session filename with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"{SESSION_FILE_PREFIX}_{timestamp}_{unique_id}.json"

    def generate_conversation_filename(self) -> str:
        """Generate unique conversation filename with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"{CONVERSATION_FILE_PREFIX}_{timestamp}_{unique_id}.json"

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
        self, conversation_file: str, claude_message: str, gemini_response: str
    ) -> bool:
        """Add a complete Claude-Gemini exchange to conversation"""
        conversation_history = self.load_conversation(conversation_file)

        # Add Claude's message
        claude_msg = {
            "timestamp": datetime.now().isoformat(),
            "role": "claude",
            "content": claude_message,
        }
        conversation_history.append(claude_msg)

        # Add Gemini's response
        gemini_msg = {
            "timestamp": datetime.now().isoformat(),
            "role": "gemini",
            "content": gemini_response,
        }
        conversation_history.append(gemini_msg)

        return self.save_conversation(conversation_file, conversation_history)

    def initialize_session(self) -> str:
        """Initialize a new session conversation file"""
        session_filename = self.generate_session_filename()
        session_file_path = os.path.join(self.conversations_dir, session_filename)

        # Create empty conversation file
        if self.save_conversation(session_file_path, []):
            self.current_session_file = session_file_path

            # Initialize streaming file for new session
            self._initialize_streaming_file(session_filename)

            return session_file_path
        else:
            raise RuntimeError(f"Failed to create session file: {session_file_path}")

    def _initialize_streaming_file(self, session_filename: str) -> None:
        """Initialize the live streaming file for a new session"""
        streaming_file = self.get_live_stream_path()
        try:
            with open(streaming_file, "w", encoding="utf-8") as f:
                f.write(f"NEW SESSION STARTED - {session_filename}\n")
                f.write("=" * 70 + "\n\n")
        except IOError:
            pass  # Fail silently if we can't write to streaming file

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
        return os.path.join(self.conversations_dir, conversation_id)

    def list_conversation_files(self) -> List[str]:
        """List all conversation JSON files in the directory"""
        try:
            json_files = [
                f for f in os.listdir(self.conversations_dir) if f.endswith(".json")
            ]
            # Sort by modification time, most recent first
            json_files.sort(
                key=lambda x: os.path.getmtime(os.path.join(self.conversations_dir, x)),
                reverse=True,
            )
            return json_files
        except OSError:
            return []

    def get_most_recent_conversation(self) -> Optional[str]:
        """Get the path to the most recent conversation file"""
        conversation_files = self.list_conversation_files()
        if conversation_files:
            return os.path.join(self.conversations_dir, conversation_files[0])
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
            formatted_messages.append(f"{role}:\n{content}")

        return f"""
CONVERSATION HISTORY - {os.path.basename(conversation_file)}
========================================================================

{chr(10).join(formatted_messages)}

========================================================================
Total messages: {len(conversation_history)}
"""

    def export_conversation(
        self, conversation_file: str, format_type: str = "txt"
    ) -> Optional[str]:
        """Export conversation to different format"""
        if not os.path.exists(conversation_file):
            return None

        conversation_history = self.load_conversation(conversation_file)
        if not conversation_history:
            return None

        base_name = os.path.splitext(os.path.basename(conversation_file))[0]

        if format_type.lower() == "txt":
            export_file = os.path.join(self.conversations_dir, f"{base_name}.txt")
            try:
                with open(export_file, "w", encoding="utf-8") as f:
                    f.write(f"Conversation Export: {base_name}\n")
                    f.write("=" * 50 + "\n\n")

                    for msg in conversation_history:
                        timestamp = msg.get("timestamp", "")
                        role = msg.get("role", "unknown")
                        content = msg.get("content", "")

                        f.write(f"[{timestamp}] {role.upper()}:\n")
                        f.write(f"{content}\n\n")
                        f.write("-" * 30 + "\n\n")

                return export_file
            except IOError:
                return None

        # Add other format types (markdown, etc.) as needed
        return None

    def cleanup_old_conversations(self, keep_count: int = 50) -> int:
        """Clean up old conversation files, keeping only the most recent ones"""
        conversation_files = self.list_conversation_files()

        if len(conversation_files) <= keep_count:
            return 0

        files_to_delete = conversation_files[keep_count:]
        deleted_count = 0

        for filename in files_to_delete:
            file_path = os.path.join(self.conversations_dir, filename)
            try:
                os.remove(file_path)
                deleted_count += 1
            except OSError:
                continue

        return deleted_count


# Global instance (to be replaced with dependency injection later)
session_manager = SessionManager()
