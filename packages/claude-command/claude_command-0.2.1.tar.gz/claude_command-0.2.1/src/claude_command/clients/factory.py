"""AI client factory for creating and managing client instances"""

from typing import Dict, Optional, Type

from ..settings import settings
from .anthropic import AnthropicClient
from .gemini import GeminiClient
from .interface import AIClient
from .openai import OpenAIClient


class ClientFactory:
    """Factory for creating AI client instances based on configuration"""

    _clients: Dict[str, AIClient] = {}
    _client_classes: Dict[str, Type[AIClient]] = {
        "gemini": GeminiClient,
        "openai": OpenAIClient,
        "anthropic": AnthropicClient,
    }

    @classmethod
    def create_client(cls, client_type: str = "gemini") -> Optional[AIClient]:
        """Create or get cached AI client instance"""
        # Return cached client if available
        if client_type in cls._clients:
            return cls._clients[client_type]

        # Create new client based on type
        client_class = cls._client_classes.get(client_type.lower())
        if not client_class:
            return None

        try:
            # Get appropriate API key for client type
            client: Optional[AIClient] = None
            if client_type.lower() == "gemini" and settings.gemini_api_key:
                client = GeminiClient(settings.gemini_api_key)
            elif client_type.lower() == "openai" and settings.openai_api_key:
                client = OpenAIClient(settings.openai_api_key)
            elif client_type.lower() == "anthropic" and settings.anthropic_api_key:
                client = AnthropicClient(settings.anthropic_api_key)
            else:
                return None

            cls._clients[client_type] = client
            return client
        except Exception:
            return None

    @classmethod
    def get_available_clients(cls) -> Dict[str, bool]:
        """Get status of all available client types"""
        status = {}
        for client_type in cls._client_classes.keys():
            client = cls.create_client(client_type)
            status[client_type] = client.is_available() if client else False
        return status

    @classmethod
    def get_primary_client(cls) -> Optional[AIClient]:
        """Get the primary/default AI client"""
        # Try clients in order of preference
        for client_type in ["gemini", "openai", "anthropic"]:
            client = cls.create_client(client_type)
            if client and client.is_available():
                return client
        return None

    @classmethod
    def clear_cache(cls) -> None:
        """Clear cached client instances"""
        cls._clients.clear()


# Convenience functions
def create_client(client_type: str = "gemini") -> Optional[AIClient]:
    """Create an AI client instance"""
    return ClientFactory.create_client(client_type)


def get_primary_client() -> Optional[AIClient]:
    """Get the primary available AI client"""
    return ClientFactory.get_primary_client()


def create_available_clients() -> list[AIClient]:
    """Create all available AI clients based on configuration"""
    clients = []

    # Try to create Gemini client
    if settings.gemini_api_key:
        gemini_client = ClientFactory.create_client("gemini")
        if gemini_client and gemini_client.is_available():
            clients.append(gemini_client)

    # Try to create OpenAI client
    if settings.openai_api_key:
        openai_client = ClientFactory.create_client("openai")
        if openai_client and openai_client.is_available():
            clients.append(openai_client)

    # Try to create Anthropic client
    if settings.anthropic_api_key:
        anthropic_client = ClientFactory.create_client("anthropic")
        if anthropic_client and anthropic_client.is_available():
            clients.append(anthropic_client)

    return clients


def get_client_by_name(name: str) -> Optional[AIClient]:
    """Get a specific client by name/model"""
    clients = create_available_clients()
    for client in clients:
        if client.get_model_name().lower() == name.lower():
            return client
    return None
