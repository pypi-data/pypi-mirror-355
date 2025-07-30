"""
Provider module for interacting with different LLM providers.
"""
from typing import Dict, Any

from .base import BaseProvider
from .openai import OpenAIProvider
from .gemini import GeminiProvider

def create_provider(provider_name: str) -> BaseProvider:
    """
    Factory function to create the appropriate provider instance.
    
    Args:
        provider_name: The name of the provider to use ("openai" or "gemini")
        
    Returns:
        An instance of the appropriate provider class
    
    Raises:
        ValueError: If the provider name is not supported
    """
    if provider_name.lower() == "openai":
        return OpenAIProvider()
    elif provider_name.lower() == "gemini":
        return GeminiProvider()
    else:
        raise ValueError(f"Unsupported provider: {provider_name}. Use 'openai' or 'gemini'.")

__all__ = [
    "BaseProvider",
    "OpenAIProvider",
    "GeminiProvider",
    "create_provider"
]
