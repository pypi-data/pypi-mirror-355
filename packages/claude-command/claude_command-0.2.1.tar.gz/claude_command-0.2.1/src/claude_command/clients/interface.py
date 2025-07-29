"""Abstract interface for AI clients"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class AIClient(ABC):
    """Abstract base class for all AI model clients"""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the AI client is available for use"""
        pass

    @abstractmethod
    def get_error(self) -> str:
        """Get initialization or connection error message"""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the name/identifier of the AI model"""
        pass

    @abstractmethod
    def call_simple(self, prompt: str, temperature: Optional[float] = None) -> str:
        """Simple AI call without conversation context"""
        pass

    @abstractmethod
    def call_with_conversation(
        self,
        prompt: str,
        conversation_history: List[Dict[str, Any]],
        temperature: Optional[float] = None,
    ) -> str:
        """Call AI with full conversation context"""
        pass

    @abstractmethod
    def call_with_streaming(
        self,
        prompt: str,
        conversation_history: List[Dict[str, Any]],
        streaming_file: str,
        temperature: Optional[float] = None,
    ) -> str:
        """Call AI with streaming output to file"""
        pass

    @abstractmethod
    def review_code(self, code: str, focus: str = "general") -> str:
        """Perform code review with the AI"""
        pass

    @abstractmethod
    def brainstorm(self, topic: str, context: str = "") -> str:
        """Brainstorm with the AI"""
        pass

    def get_display_name(self) -> str:
        """Get human-readable display name for the AI"""
        return self.get_model_name()

    def get_recommended_temperature(self, task_type: str) -> float:
        """Get recommended temperature for different task types"""
        temperatures = {
            "code_review": 0.2,
            "brainstorm": 0.7,
            "conversation": 0.5,
            "analysis": 0.3,
            "creative": 0.8,
        }
        return temperatures.get(task_type, 0.5)
