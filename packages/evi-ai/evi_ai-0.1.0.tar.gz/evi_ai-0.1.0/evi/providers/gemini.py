"""
Gemini provider implementation for the evi package.
"""
import os
import json
import streamlit as st
from typing import Dict, Any, List

from .base import BaseProvider

class GeminiProvider(BaseProvider):
    """
    Provider class for Google's Gemini models.
    """
    
    def __init__(self, model_id: str = "gemini-2.0-flash"):
        """
        Initialize the Gemini provider with the specified model ID.
        
        Args:
            model_id: The ID of the model to use (default: "gemini-1.5-pro")
        """
        self.model_id = model_id
        self.client = None
        self.genai = None
        self.params = {
            "max_output_tokens": 1000,
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40
        }
    
    def initialize(self) -> None:
        """
        Initialize the Gemini client with the API key.
        """
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("Google Generative AI package is not installed. Install it with 'pip install google-generativeai'")
            
        # Get API key from environment or streamlit session state
        api_key = os.getenv("GEMINI_API_KEY")
            
        if not api_key and hasattr(st, 'session_state') and 'gemini_api_key' in st.session_state:
            api_key = st.session_state.gemini_api_key
                
        if not api_key and st is not None:
            st.warning("Gemini API Key not found in environment. Please enter it below.")
            api_key = st.text_input("Enter Gemini API Key:", type="password", key="gemini_key_input")
            if api_key:
                st.session_state.gemini_api_key = api_key
            else:
                st.stop()
        
        if not api_key:
            raise ValueError("Gemini API key is required. Set the GEMINI_API_KEY environment variable.")
            
        genai.configure(api_key=api_key)
        self.genai = genai
        self.client = genai.GenerativeModel(model_name=self.model_id)
    
    def _format_messages(self, prompt: str, system_prompt: str) -> List[Dict[str, str]]:
        """
        Format the user and system prompts into the Gemini message format.
        
        Args:
            prompt: The user's prompt
            system_prompt: The system prompt for the framework
            
        Returns:
            Messages formatted for Gemini API
        """
        # For Gemini, we'll just combine system and user prompt
        return [
            {"role": "user", "parts": [{"text": f"{system_prompt}\n\n{prompt}"}]}
        ]
    
    def generate_json_config(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        """
        Generate a JSON configuration using the Gemini API.
        
        Args:
            prompt: The user's natural language description
            system_prompt: The system prompt specific to the framework
            
        Returns:
            A dictionary containing the generated configuration
        """
        if self.client is None:
            self.initialize()
            
        # Format the prompt for Gemini
        messages = self._format_messages(prompt, system_prompt)
        
        # Construct generation config
        generation_config = {
            "temperature": self.params["temperature"],
            "top_p": self.params["top_p"],
            "top_k": self.params["top_k"],
            "max_output_tokens": self.params["max_output_tokens"],
        }
        
        try:
            # Call the Gemini API
            response = self.client.generate_content(
                messages[0]["parts"][0]["text"],
                generation_config=generation_config
            )
            
            content = response.text
            
            # Extract JSON from response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                return json.loads(json_str)
            else:
                raise ValueError("Could not extract valid JSON from model response")
                
        except Exception as e:
            raise Exception(f"Error in Gemini text generation: {str(e)}")
    
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
        
        # Re-initialize the client with the new model if it was already initialized
        if self.client is not None and self.genai is not None:
            self.client = self.genai.GenerativeModel(model_name=self.model_id)
