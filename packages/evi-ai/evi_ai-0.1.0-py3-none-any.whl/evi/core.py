"""
Core module for the evi package containing the main controller class.
"""
import json
from typing import Dict, Any, Optional

from .providers import create_provider, BaseProvider
from .frameworks import create_framework, BaseFramework

class EviGenerator:
    """
    Main controller class for the evi package.
    
    This class orchestrates the generation process by selecting the appropriate
    provider and framework based on user input.
    """
    
    def __init__(self, provider: str = "openai", framework: str = "crewai"):
        """
        Initialize the generator with the specified provider and framework.
        
        Args:
            provider: The LLM provider to use ("openai" or "gemini")
            framework: The agent framework to use ("crewai", "langgraph", or "react")
        """
        self.provider_name = provider.lower()
        self.framework_name = framework.lower()
        
        # Create provider and framework instances
        self.provider = create_provider(self.provider_name)
        self.framework = create_framework(self.framework_name)
    
    def set_provider(self, provider: str):
        """
        Change the LLM provider.
        
        Args:
            provider: The LLM provider to use ("openai" or "gemini")
        """
        if provider.lower() not in ["openai", "gemini"]:
            raise ValueError(f"Unsupported provider: {provider}. Use 'openai' or 'gemini'.")
            
        self.provider_name = provider.lower()
        self.provider = create_provider(self.provider_name)
    
    def set_framework(self, framework: str):
        """
        Change the agent framework.
        
        Args:
            framework: The agent framework to use ("crewai", "langgraph", or "react")
        """
        if framework.lower() not in ["crewai", "langgraph", "react"]:
            raise ValueError(f"Unsupported framework: {framework}. Use 'crewai', 'langgraph', or 'react'.")
            
        self.framework_name = framework.lower()
        self.framework = create_framework(self.framework_name)
    
    def generate(self, prompt: str, output_format: str = "code") -> str:
        """
        Generate agent code or configuration based on a prompt.
        
        Args:
            prompt: The natural language description of the desired agent system
            output_format: The desired output format ("code" or "json")
            
        Returns:
            The generated code or JSON configuration
        """
        # Get the system prompt for the selected framework
        system_prompt = self.framework.get_system_prompt()
        
        try:
            # Generate JSON configuration using the provider
            config = self.provider.generate_json_config(prompt, system_prompt)
            
            # Return the JSON or generate code based on the output format
            if output_format.lower() == "json":
                return json.dumps(config, indent=2)
            else:
                return self.framework.generate_code(config)
                
        except Exception as e:
            error_msg = f"Error in generation process: {str(e)}"
            print(error_msg)
            
            # Use default config if generation fails
            if output_format.lower() == "json":
                return json.dumps(self.framework.get_default_config(), indent=2)
            else:
                return self.framework.generate_code(self.framework.get_default_config())
