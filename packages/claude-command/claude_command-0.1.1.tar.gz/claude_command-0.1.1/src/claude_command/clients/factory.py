#!/usr/bin/env python3
"""
AI client factory
Creates and manages AI client instances based on configuration
"""

from typing import Dict, Optional

from .gemini import GeminiClient
from .interface import AIClient


class ClientFactory:
    """Factory for creating AI client instances"""

    _clients: Dict[str, AIClient] = {}
    _client_classes = {
        "gemini": GeminiClient,
        # Add other clients here as they're implemented
        # "openai": OpenAIClient,
        # "claude": ClaudeClient,
    }

    @classmethod
    def create_client(cls, client_type: str = "gemini") -> Optional[AIClient]:
        """Create or get cached AI client instance"""
        # Return cached client if available
        if client_type in cls._clients:
            return cls._clients[client_type]

        # Create new client
        client_class = cls._client_classes.get(client_type.lower())
        if not client_class:
            return None

        try:
            client = client_class()
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
        for client_type in ["gemini", "openai", "claude"]:
            client = cls.create_client(client_type)
            if client and client.is_available():
                return client
        return None

    @classmethod
    def clear_cache(cls) -> None:
        """Clear cached client instances"""
        cls._clients.clear()


# Convenience function for backward compatibility
def create_client(client_type: str = "gemini") -> Optional[AIClient]:
    """Create an AI client instance"""
    return ClientFactory.create_client(client_type)


# Global default client instance
default_client = ClientFactory.get_primary_client()
