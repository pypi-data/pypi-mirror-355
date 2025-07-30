"""
Base framework class that defines the interface for all framework handlers.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseFramework(ABC):
    """
    Abstract base class for framework handlers.
    
    This class defines the interface that all framework implementations
    must adhere to.
    """
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this framework.
        
        Returns:
            The system prompt as a string
        """
        pass
    
    @abstractmethod
    def generate_code(self, config: Dict[str, Any]) -> str:
        """
        Generate code from a JSON configuration.
        
        Args:
            config: The JSON configuration for the agent system
            
        Returns:
            The generated code as a string
            
        Raises:
            Exception: If the code generation fails for any reason
        """
        pass
    
    @abstractmethod
    def get_default_config(self) -> Dict[str, Any]:
        """
        Get a default configuration for this framework.
        
        Returns:
            A dictionary containing the default configuration
        """
        pass
        
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate the configuration for this framework.
        
        Args:
            config: The configuration to validate
            
        Returns:
            True if the configuration is valid, False otherwise
        """
        # Default implementation just checks if the required keys exist
        try:
            for key in self.get_required_keys():
                if key not in config:
                    return False
            return True
        except:
            return False
    
    @abstractmethod
    def get_required_keys(self) -> list:
        """
        Get the required keys for this framework's configuration.
        
        Returns:
            A list of required keys
        """
        pass
