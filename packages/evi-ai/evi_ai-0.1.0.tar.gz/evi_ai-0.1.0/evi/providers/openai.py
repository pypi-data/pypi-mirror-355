"""
OpenAI provider implementation for the evi package.
"""
import os
import json
import streamlit as st
from typing import Dict, Any, List

from .base import BaseProvider

class OpenAIProvider(BaseProvider):
    """
    Provider class for OpenAI models.
    """
    
    def __init__(self, model_id: str = "gpt-4-turbo"):
        """
        Initialize the OpenAI provider with the specified model ID.
        
        Args:
            model_id: The ID of the model to use (default: "gpt-4-turbo")
        """
        self.model_id = model_id
        self.client = None
        self.params = {
            "max_tokens": 1000,
            "temperature": 0.7,
            "top_p": 0.95,
            "frequency_penalty": 0,
            "presence_penalty": 0
        }
    
    def initialize(self) -> None:
        """
        Initialize the OpenAI client with the API key.
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("OpenAI package is not installed. Install it with 'pip install openai'")
            
        # Get API key from environment or streamlit session state
        api_key = os.getenv("OPENAI_API_KEY")
            
        if not api_key and hasattr(st, 'session_state') and 'openai_api_key' in st.session_state:
            api_key = st.session_state.openai_api_key
                
        if not api_key and st is not None:
            st.warning("OpenAI API Key not found in environment. Please enter it below.")
            api_key = st.text_input("Enter OpenAI API Key:", type="password", key="openai_key_input")
            if api_key:
                st.session_state.openai_api_key = api_key
            else:
                st.stop()
        
        if not api_key:
            raise ValueError("OpenAI API key is required. Set the OPENAI_API_KEY environment variable.")
            
        self.client = OpenAI(api_key=api_key)
    
    def _format_messages(self, prompt: str, system_prompt: str) -> List[Dict[str, str]]:
        """
        Format the user and system prompts into a list of messages for the OpenAI API.
        
        Args:
            prompt: The user's prompt
            system_prompt: The system prompt for the framework
            
        Returns:
            List of message dictionaries for the OpenAI API
        """
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    
    def generate_json_config(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        """
        Generate a JSON configuration using the OpenAI API.
        
        Args:
            prompt: The user's natural language description
            system_prompt: The system prompt specific to the framework
            
        Returns:
            A dictionary containing the generated configuration
        """
        if self.client is None:
            self.initialize()
            
        messages = self._format_messages(prompt, system_prompt)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                max_tokens=self.params["max_tokens"],
                temperature=self.params["temperature"],
                top_p=self.params["top_p"],
                frequency_penalty=self.params["frequency_penalty"],
                presence_penalty=self.params["presence_penalty"]
            )
            
            content = response.choices[0].message.content
            
            # Extract JSON from response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                return json.loads(json_str)
            else:
                raise ValueError("Could not extract valid JSON from model response")
                
        except Exception as e:
            raise Exception(f"Error in OpenAI text generation: {str(e)}")
    
    def get_model_id(self) -> str:
        """
        Get the current model ID.
        
        Returns:
            The model ID as a string
        """
        return self.model_id
    
    def set_model_id(self, model_id: str) -> None:
        """
        Set the model ID.
        
        Args:
            model_id: The model ID to use
        """
        self.model_id = model_id
