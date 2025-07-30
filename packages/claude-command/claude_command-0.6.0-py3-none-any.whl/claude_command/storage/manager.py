"""File system management and storage operations for Claude Command"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..settings import settings
from .naming import is_legacy_filename, parse_mission_filename


class StorageManager:
    """Manages file system operations, directories, and file I/O"""

    def __init__(self) -> None:
        """Initialize storage manager"""
        self.base_dir = self._ensure_base_dir()
        self.topics_dir = self._ensure_subdir("topics")
        self.recons_dir = self._ensure_subdir("recons")
        self.brainstorms_dir = self._ensure_subdir("brainstorms")
        self.queries_dir = self._ensure_subdir("queries")
        self.reviews_dir = self._ensure_subdir("reviews")
        self.streams_dir = self._ensure_subdir("streams")
        self.histories_dir = self._ensure_subdir("histories")
        self.missions_dir = self._ensure_subdir("missions")

        # Mission index for unified mission discovery (JSONL for easy append)
        self.missions_index_file = self.base_dir / "index.jsonl"

    def _ensure_base_dir(self) -> Path:
        """Ensure base directory exists and return path"""
        base_dir = Path(settings.topics_dir).expanduser()
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir

    def _ensure_subdir(self, subdir_name: str) -> Path:
        """Ensure subdirectory exists and return path"""
        subdir = self.base_dir / subdir_name
        subdir.mkdir(parents=True, exist_ok=True)
        return subdir

    # Directory getters
    def get_topics_directory(self) -> str:
        """Get the topics directory path"""
        return str(self.topics_dir)

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

    def get_missions_directory(self) -> str:
        """Get the missions directory path"""
        return str(self.missions_dir)

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

    def create_topic_file(self, filename: str) -> str:
        """Create or ensure existence of a topic file in topics directory"""
        topics_dir = self.get_topics_directory()
        filepath = Path(topics_dir) / filename

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

    def generate_topic_filename(self) -> str:
        """Generate unique topic filename with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"topic_{timestamp}_{unique_id}.json"

    # Topic file operations
    def load_topic(self, topic_file: str) -> List[Dict[str, Any]]:
        """Load topic history from file (JSON or JSONL)"""
        if not os.path.exists(topic_file):
            return []

        try:
            # Handle JSONL files
            if topic_file.endswith(".jsonl"):
                return self.read_jsonl(topic_file)

            # Handle JSON files
            with open(topic_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError, UnicodeDecodeError):
            return []

    def save_topic(self, topic_file: str, topic_history: List[Dict[str, Any]]) -> bool:
        """Save topic history to file"""
        try:
            with open(topic_file, "w", encoding="utf-8") as f:
                json.dump(topic_history, f, indent=2, ensure_ascii=False)
            return True
        except IOError:
            return False

    def add_message_to_topic(self, topic_file: str, role: str, content: str) -> bool:
        """Add a new message to an existing topic"""
        topic_history = self.load_topic(topic_file)

        message = {
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content,
        }

        topic_history.append(message)
        return self.save_topic(topic_file, topic_history)

    def add_exchange_to_topic(
        self,
        topic_file: str,
        claude_message: str,
        ai_response: str,
        ai_model: str,
    ) -> bool:
        """Add a complete Claude-AI exchange to topic"""
        topic_history = self.load_topic(topic_file)

        # Add Claude's message
        claude_msg = {
            "timestamp": datetime.now().isoformat(),
            "role": "claude",
            "content": claude_message,
        }
        topic_history.append(claude_msg)

        # Add AI's response
        ai_msg = {
            "timestamp": datetime.now().isoformat(),
            "role": "assistant",
            "content": ai_response,
            "model": ai_model,
        }
        topic_history.append(ai_msg)

        return self.save_topic(topic_file, topic_history)

    # Topic file management
    def get_topic_file_path(self, topic_id: str) -> str:
        """Get full path for a topic file by ID"""
        # If already has extension, use as-is
        if topic_id.endswith((".json", ".jsonl")):
            return str(self.topics_dir / topic_id)

        # Try to find existing file with either extension
        json_path = self.topics_dir / f"{topic_id}.json"
        jsonl_path = self.topics_dir / f"{topic_id}.jsonl"

        if jsonl_path.exists():
            return str(jsonl_path)
        elif json_path.exists():
            return str(json_path)
        else:
            # Default to .json for new files
            return str(json_path)

    def list_topic_files(self) -> List[str]:
        """List all topic files (JSON and JSONL) in the directory"""
        try:
            # Get both JSON and JSONL files
            json_files = [f.name for f in self.topics_dir.glob("*.json")]
            jsonl_files = [f.name for f in self.topics_dir.glob("*.jsonl")]
            all_files = json_files + jsonl_files

            # Sort by modification time, most recent first
            all_files.sort(
                key=lambda x: os.path.getmtime(self.topics_dir / x),
                reverse=True,
            )
            return all_files
        except OSError:
            return []

    def get_most_recent_topic(self) -> str | None:
        """Get the path to the most recent topic file"""
        topic_files = self.list_topic_files()
        if topic_files:
            return str(self.topics_dir / topic_files[0])
        return None

    def format_topic_history(self, topic_file: str) -> str:
        """Format topic history for display"""
        if not os.path.exists(topic_file):
            return f"Topic file not found: {os.path.basename(topic_file)}"

        topic_history = self.load_topic(topic_file)
        if not topic_history:
            return (
                f"Topic {os.path.basename(topic_file)} is empty or could not be loaded."
            )

        # Format the topic history
        formatted_messages = []
        for msg in topic_history:
            role = msg.get("role", "unknown").upper()
            content = msg.get("content", "")
            model = msg.get("model", "")
            model_info = f" ({model})" if model else ""
            formatted_messages.append(f"{role}{model_info}:\\n{content}")

        return f"""
TOPIC HISTORY - {os.path.basename(topic_file)}
========================================================================

{chr(10).join(formatted_messages)}

========================================================================
Total messages: {len(topic_history)}
"""

    def cleanup_old_topics(self, keep_count: int = 50) -> int:
        """Clean up old topic files, keeping only the most recent ones"""
        topic_files = self.list_topic_files()

        if len(topic_files) <= keep_count:
            return 0

        files_to_delete = topic_files[keep_count:]
        deleted_count = 0

        for filename in files_to_delete:
            file_path = self.topics_dir / filename
            try:
                file_path.unlink()
                deleted_count += 1
            except OSError:
                continue

        return deleted_count

    # Mission Index System
    def load_missions_index(self) -> List[Dict[str, Any]]:
        """Load all mission runs from JSONL index file"""
        if not self.missions_index_file.exists():
            return []

        sessions = []
        try:
            with open(self.missions_index_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        sessions.append(json.loads(line))
        except (json.JSONDecodeError, IOError):
            return []

        # Sort by timestamp, newest first
        sessions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return sessions

    def append_mission_to_index(self, mission_entry: Dict[str, Any]) -> None:
        """Append a new mission run to the JSONL index file"""
        try:
            with open(self.missions_index_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(mission_entry, ensure_ascii=False) + "\n")
                f.flush()
        except IOError:
            pass  # Silently fail if we can't write the index

    def add_mission_to_index(
        self,
        mission_type: str,
        subject: str,
        subject_slug: str,
        timestamp: str,
        mission_prompt: str,
        providers: Optional[List[str]] = None,
        result_files: Optional[Dict[str, str]] = None,
    ) -> None:
        """Add a new mission run to the JSONL index"""
        mission_entry = {
            "id": f"{mission_type}-{subject_slug}-{timestamp}",
            "mission_type": mission_type,
            "subject": subject,
            "subject_slug": subject_slug,
            "timestamp": timestamp,
            "datetime": self._parse_timestamp_to_iso(timestamp),
            "mission_prompt": mission_prompt,
            "providers": providers or [],
            "result_files": result_files or {},
            "created_at": datetime.now().isoformat(),
        }

        # Simply append to JSONL file (much more efficient)
        self.append_mission_to_index(mission_entry)

    def list_missions_by_type(
        self, mission_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List mission runs, optionally filtered by mission type"""
        missions = self.load_missions_index()

        if mission_type:
            missions = [m for m in missions if m.get("mission_type") == mission_type]

        return missions

    def search_missions(
        self, query: str, search_content: bool = True
    ) -> List[Dict[str, Any]]:
        """Search mission runs by subject, prompt content, and optionally response content"""
        missions = self.load_missions_index()

        query_lower = query.lower()
        matching_missions = []

        for mission in missions:
            # First, search in metadata (subject, prompt, ID)
            searchable_text = " ".join(
                [
                    mission.get("subject", ""),
                    mission.get("mission_prompt", ""),
                    mission.get("id", ""),
                ]
            ).lower()

            # Check if query matches metadata
            metadata_match = query_lower in searchable_text

            # If content search is enabled and no metadata match, search mission content
            content_match = False
            if search_content and not metadata_match:
                content_match = self._search_mission_content(mission, query_lower)

            if metadata_match or content_match:
                matching_missions.append(mission)

        return matching_missions

    def _search_mission_content(
        self, mission: Dict[str, Any], query_lower: str
    ) -> bool:
        """Search within mission response content"""
        try:
            # Get the main mission file path
            main_file = mission.get("result_files", {}).get("main")
            if not main_file or not os.path.exists(main_file):
                return False

            # Read the mission JSON file
            with open(main_file, "r", encoding="utf-8") as f:
                mission_data = json.load(f)

            # Search in all provider responses
            results = mission_data.get("results", {})
            for provider_data in results.values():
                content = provider_data.get("content", "")
                if query_lower in content.lower():
                    return True

            return False

        except (json.JSONDecodeError, IOError, KeyError):
            # If we can't read the file, skip content search for this mission
            return False

    def search_topics(self, query: str) -> List[Dict[str, Any]]:
        """Search within topic files for accumulated knowledge"""
        query_lower = query.lower()
        matching_topics = []
        topics_dir = Path(self.get_topics_directory())

        try:
            # Get all .jsonl files in topics directory
            topic_files = list(topics_dir.glob("*.jsonl"))

            for topic_file in topic_files:
                topic_name = topic_file.stem
                matches = []

                try:
                    # Read JSONL file line by line
                    with open(topic_file, "r", encoding="utf-8") as f:
                        for line_num, line in enumerate(f, 1):
                            line = line.strip()
                            if not line:
                                continue

                            try:
                                message = json.loads(line)
                                content = message.get("content", "")

                                # Search in message content
                                if query_lower in content.lower():
                                    matches.append(
                                        {
                                            "line_number": line_num,
                                            "role": message.get("role", "unknown"),
                                            "timestamp": message.get("timestamp", ""),
                                            "mission_type": message.get(
                                                "mission_type", ""
                                            ),
                                            "content_snippet": self._extract_snippet(
                                                content, query_lower
                                            ),
                                        }
                                    )

                            except json.JSONDecodeError:
                                # Skip malformed JSON lines
                                continue

                    # If we found matches in this topic file, add to results
                    if matches:
                        matching_topics.append(
                            {
                                "topic_name": topic_name,
                                "topic_file": str(topic_file),
                                "matches": matches,
                                "total_matches": len(matches),
                            }
                        )

                except (IOError, UnicodeDecodeError):
                    # Skip files we can't read
                    continue

            return matching_topics

        except Exception:
            # If anything goes wrong, return empty results
            return []

    def _extract_snippet(
        self, content: str, query_lower: str, context_chars: int = 150
    ) -> str:
        """Extract a snippet of text around the search query"""
        content_lower = content.lower()
        query_index = content_lower.find(query_lower)

        if query_index == -1:
            return (
                content[:context_chars] + "..."
                if len(content) > context_chars
                else content
            )

        # Calculate snippet boundaries
        start = max(0, query_index - context_chars // 2)
        end = min(len(content), query_index + len(query_lower) + context_chars // 2)

        snippet = content[start:end]

        # Add ellipsis if we truncated
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet

    def rebuild_missions_index(self) -> int:
        """Rebuild the mission index by scanning all mission directories"""
        # Remove existing index file to rebuild from scratch
        if self.missions_index_file.exists():
            self.missions_index_file.unlink()

        mission_count = 0

        # Scan all mission type directories
        mission_dirs = {
            "recon": self.recons_dir,
            "brainstorm": self.brainstorms_dir,
            "review": self.reviews_dir,
            "query": self.queries_dir,
        }

        for mission_type, directory in mission_dirs.items():
            if not directory.exists():
                continue

            for file_path in directory.glob("*.json"):
                filename = file_path.name

                # Try to parse new format first
                parsed = parse_mission_filename(filename)
                if parsed:
                    # New format - extract metadata from filename
                    mission_entry = {
                        "id": f"{parsed['mission_type']}-{parsed['subject_slug']}-{parsed['timestamp']}",
                        "mission_type": parsed["mission_type"],
                        "subject": parsed["subject_slug"].replace("-", " ").title(),
                        "subject_slug": parsed["subject_slug"],
                        "timestamp": parsed["timestamp"],
                        "datetime": self._parse_timestamp_to_iso(parsed["timestamp"]),
                        "mission_prompt": "[Legacy - prompt not indexed]",
                        "providers": [],
                        "result_files": {"main": str(file_path)},
                        "created_at": datetime.fromtimestamp(
                            file_path.stat().st_mtime
                        ).isoformat(),
                    }
                elif is_legacy_filename(filename):
                    # Legacy format - try to extract timestamp
                    timestamp_match = filename.split("-")[
                        1:-1
                    ]  # Extract timestamp parts
                    if len(timestamp_match) >= 6:
                        timestamp = "-".join(timestamp_match)
                        mission_entry = {
                            "id": f"{mission_type}-legacy-{timestamp}",
                            "mission_type": mission_type,
                            "subject": "[Legacy Mission]",
                            "subject_slug": "legacy-mission",
                            "timestamp": timestamp,
                            "datetime": self._parse_timestamp_to_iso(timestamp),
                            "mission_prompt": "[Legacy - prompt not indexed]",
                            "providers": [],
                            "result_files": {"main": str(file_path)},
                            "created_at": datetime.fromtimestamp(
                                file_path.stat().st_mtime
                            ).isoformat(),
                        }
                    else:
                        continue  # Skip malformed filenames
                else:
                    continue  # Skip unrecognized filenames

                # Append each mission to JSONL file
                self.append_mission_to_index(mission_entry)
                mission_count += 1

        return mission_count

    def _parse_timestamp_to_iso(self, timestamp: str) -> str:
        """Convert YYYY-MM-DD-HH-MM-SS timestamp to ISO format"""
        try:
            # Convert 2025-06-16-15-49-38 to 2025-06-16T15:49:38
            date_part, time_part = timestamp[:10], timestamp[11:]
            iso_time = time_part.replace("-", ":")
            return f"{date_part}T{iso_time}"
        except (ValueError, IndexError):
            return timestamp  # Return as-is if parsing fails


# Global instance
storage_manager = StorageManager()
