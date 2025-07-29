#!/usr/bin/env python3
"""
Configuration module for Claude Command
Contains environment variables, constants, and configuration settings for multiple AI clients
"""

import os
from typing import Optional

# Server version
__version__ = "1.0.0"

# AI Client configuration
DEFAULT_AI_CLIENT = "gemini"
SUPPORTED_CLIENTS = ["gemini", "openai", "claude"]

# Model configuration defaults
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash-preview-05-20"
DEFAULT_OPENAI_MODEL = "gpt-4"
DEFAULT_TEMPERATURE = 0.5
DEFAULT_MAX_OUTPUT_TOKENS = 8192

# Temperature settings for different operations
BRAINSTORM_TEMPERATURE = 0.7
CODE_REVIEW_TEMPERATURE = 0.2
CONVERSATION_TEMPERATURE = 0.5
ANALYSIS_TEMPERATURE = 0.3
CREATIVE_TEMPERATURE = 0.8

# File and directory configuration
CONVERSATIONS_DIR_NAME = "claude-command"
LIVE_STREAM_FILENAME = "live_stream.txt"
SESSION_FILE_PREFIX = "session"
CONVERSATION_FILE_PREFIX = "conversation"


def get_ai_client_type() -> str:
    """Get preferred AI client type from environment or use default"""
    return os.getenv("AI_CLIENT_TYPE", DEFAULT_AI_CLIENT).lower()


def get_gemini_api_key() -> Optional[str]:
    """Get Gemini API key from environment variables"""
    return os.getenv("GEMINI_API_KEY")


def get_openai_api_key() -> Optional[str]:
    """Get OpenAI API key from environment variables"""
    return os.getenv("OPENAI_API_KEY")


def get_gemini_model_name() -> str:
    """Get Gemini model name from environment or use default"""
    return os.getenv("GEMINI_MODEL_NAME", DEFAULT_GEMINI_MODEL)


def get_openai_model_name() -> str:
    """Get OpenAI model name from environment or use default"""
    return os.getenv("OPENAI_MODEL_NAME", DEFAULT_OPENAI_MODEL)


def get_conversations_dir() -> str:
    """Get conversations directory path in user's home directory"""
    home_dir = os.path.expanduser("~")
    return os.path.join(home_dir, CONVERSATIONS_DIR_NAME)


def get_default_temperature() -> float:
    """Get default temperature from environment or use default"""
    try:
        # Check for generic AI_TEMPERATURE first, then specific client temperature
        temp_var = os.getenv("AI_TEMPERATURE") or os.getenv("GEMINI_TEMPERATURE")
        return float(temp_var) if temp_var else DEFAULT_TEMPERATURE
    except ValueError:
        return DEFAULT_TEMPERATURE


def get_max_output_tokens() -> int:
    """Get max output tokens from environment or use default"""
    try:
        # Check for generic first, then specific client tokens
        tokens_var = os.getenv("AI_MAX_TOKENS") or os.getenv("GEMINI_MAX_TOKENS")
        return int(tokens_var) if tokens_var else DEFAULT_MAX_OUTPUT_TOKENS
    except ValueError:
        return DEFAULT_MAX_OUTPUT_TOKENS


def get_user_name() -> str:
    """Get user name from environment or use default"""
    return os.getenv("USER_NAME", "Human")


def get_temperature_for_task(task_type: str) -> float:
    """Get recommended temperature for specific task types"""
    temperatures = {
        "brainstorm": BRAINSTORM_TEMPERATURE,
        "code_review": CODE_REVIEW_TEMPERATURE,
        "conversation": CONVERSATION_TEMPERATURE,
        "analysis": ANALYSIS_TEMPERATURE,
        "creative": CREATIVE_TEMPERATURE,
    }
    return temperatures.get(task_type, DEFAULT_TEMPERATURE)
