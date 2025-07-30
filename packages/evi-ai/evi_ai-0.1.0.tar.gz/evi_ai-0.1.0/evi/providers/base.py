"""
Base provider class that defines the interface for all LLM providers.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    This class defines the interface that all provider implementations
    must adhere to.
    """
    
    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the provider, including API key validation.
        
        This method should be called before any generation methods
        to ensure the provider is properly configured.
        """
        pass
    
    @abstractmethod
    def generate_json_config(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        """
        Generate a JSON configuration based on the user and system prompts.
        
        Args:
            prompt: The user's natural language description
            system_prompt: The system prompt specific to the framework
            
        Returns:
            A dictionary containing the generated configuration
            
        Raises:
            Exception: If the generation fails for any reason
        """
        pass
    
    @abstractmethod
    def get_model_id(self) -> str:
        """
        Get the default model ID for this provider.
        
        Returns:
            The default model ID as a string
        """
        pass
    
    @abstractmethod
    def set_model_id(self, model_id: str) -> None:
        """
        Set the model ID for this provider.
        
        Args:
            model_id: The model ID to use
        """
        pass
