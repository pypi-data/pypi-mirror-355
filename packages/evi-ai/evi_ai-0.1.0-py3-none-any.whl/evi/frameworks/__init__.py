"""
Framework module for generating code for different agent frameworks.
"""
from typing import Dict, Any

from .base import BaseFramework
from .crewai import CrewAIFramework
from .langgraph import LangGraphFramework
from .react import ReActFramework

def create_framework(framework_name: str) -> BaseFramework:
    """
    Factory function to create the appropriate framework instance.
    
    Args:
        framework_name: The name of the framework to use ("crewai", "langgraph", or "react")
        
    Returns:
        An instance of the appropriate framework class
    
    Raises:
        ValueError: If the framework name is not supported
    """
    if framework_name.lower() == "crewai":
        return CrewAIFramework()
    elif framework_name.lower() == "langgraph":
        return LangGraphFramework()
    elif framework_name.lower() == "react":
        return ReActFramework()
    else:
        raise ValueError(f"Unsupported framework: {framework_name}. Use 'crewai', 'langgraph', or 'react'.")

__all__ = [
    "BaseFramework",
    "CrewAIFramework",
    "LangGraphFramework",
    "ReActFramework",
    "create_framework"
]
