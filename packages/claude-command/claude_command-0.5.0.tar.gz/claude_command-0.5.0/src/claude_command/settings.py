"""Configuration settings for Claude Command MCP Server"""

import os
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings for Claude Command MCP Server"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # API Keys
    gemini_api_key: Optional[str] = Field(
        default=None, description="Google Gemini API key"
    )
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(
        default=None, description="Anthropic Claude API key"
    )

    # AI Client configuration
    default_ai_client: str = Field(
        default="gemini", description="Default AI client type"
    )

    # Model configuration
    gemini_model_name: str = Field(
        default="gemini-2.0-flash-exp", description="Gemini model name"
    )
    openai_model_name: str = Field(default="gpt-4", description="OpenAI model name")
    max_output_tokens: int = Field(default=8192, description="Maximum output tokens")

    # Temperature settings for different operations
    default_temperature: float = Field(
        default=0.5, ge=0.0, le=2.0, description="Default temperature"
    )
    brainstorm_temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Brainstorming temperature"
    )
    code_review_temperature: float = Field(
        default=0.2, ge=0.0, le=2.0, description="Code review temperature"
    )
    conversation_temperature: float = Field(
        default=0.5, ge=0.0, le=2.0, description="Conversation temperature"
    )
    analysis_temperature: float = Field(
        default=0.3, ge=0.0, le=2.0, description="Analysis temperature"
    )
    creative_temperature: float = Field(
        default=0.8, ge=0.0, le=2.0, description="Creative temperature"
    )

    # File and directory configuration
    conversations_dir: str = Field(
        default="~/claude-command", description="Directory for conversation storage"
    )
    max_history_length: int = Field(
        default=50, ge=1, description="Maximum conversation history length"
    )

    # User configuration
    user_name: str = Field(default="Human", description="User display name")

    def has_valid_api_key(self) -> bool:
        """Check if at least one valid API key is configured"""
        return bool(
            self.gemini_api_key or self.openai_api_key or self.anthropic_api_key
        )

    def get_temperature_for_task(self, task_type: str) -> float:
        """Get recommended temperature for specific task types"""
        temperatures = {
            "brainstorm": self.brainstorm_temperature,
            "code_review": self.code_review_temperature,
            "conversation": self.conversation_temperature,
            "analysis": self.analysis_temperature,
            "creative": self.creative_temperature,
        }
        return temperatures.get(task_type, self.default_temperature)


# Global settings instance
settings = Settings()


# Legacy compatibility functions for config patterns
def get_conversations_dir() -> str:
    """Get conversations directory path in user's home directory"""
    return os.path.expanduser(settings.conversations_dir)


def get_gemini_api_key() -> Optional[str]:
    """Get Gemini API key from settings"""
    return settings.gemini_api_key


def get_openai_api_key() -> Optional[str]:
    """Get OpenAI API key from settings"""
    return settings.openai_api_key


def get_anthropic_api_key() -> Optional[str]:
    """Get Anthropic API key from settings"""
    return settings.anthropic_api_key


def get_gemini_model_name() -> str:
    """Get Gemini model name from settings"""
    return settings.gemini_model_name


def get_openai_model_name() -> str:
    """Get OpenAI model name from settings"""
    return settings.openai_model_name


def get_default_temperature() -> float:
    """Get default temperature from settings"""
    return settings.default_temperature


def get_max_output_tokens() -> int:
    """Get max output tokens from settings"""
    return settings.max_output_tokens


def get_user_name() -> str:
    """Get user name from settings"""
    return settings.user_name


def get_temperature_for_task(task_type: str) -> float:
    """Get recommended temperature for specific task types"""
    return settings.get_temperature_for_task(task_type)
