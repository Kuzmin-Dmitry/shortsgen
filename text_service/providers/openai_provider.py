"""OpenAI provider implementation."""

import json
import logging
from typing import List, Optional, Dict, Any
from openai import OpenAI
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from .base import LLMProvider
from models.domain import ModelResponse, FunctionCall
from exceptions import OpenAIException
from config import OPENAI_API_KEY, DEFAULT_OPENAI_MODEL

logger = logging.getLogger(__name__)

class OpenAIProvider(LLMProvider):
    """OpenAI language model provider."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenAI provider."""
        self.api_key = api_key or OPENAI_API_KEY
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        
    def is_available(self) -> bool:
        """Check if OpenAI is available."""
        return self.client is not None
        
    def generate_text(
        self,
        prompt: str,
        max_tokens: int = 300,
        temperature: float = 0.8,
        functions: Optional[List[Dict[str, Any]]] = None,
        system_prompt: Optional[str] = None
    ) -> ModelResponse:
        """Generate text using OpenAI."""
        if not self.client:
            raise OpenAIException("OpenAI client not initialized.")
            
        try:
            messages = self._build_messages(prompt, system_prompt)
            params = self._build_params(messages, max_tokens, temperature, functions)
            
            response = self.client.chat.completions.create(**params)
            return self._parse_response(response)
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise OpenAIException(f"OpenAI API error: {e}")
    
    def _build_messages(self, prompt: str, system_prompt: Optional[str]) -> List[Dict[str, str]]:
        """Build messages for OpenAI API."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        else:
            messages.append({"role": "system", "content": "You are a comic book writer's assistant."})
        messages.append({"role": "user", "content": prompt})
        return messages
    
    def _build_params(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: int, 
        temperature: float,
        functions: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Build parameters for OpenAI API call."""
        params = {
            "model": DEFAULT_OPENAI_MODEL,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        if functions:
            params["tools"] = functions
            params["tool_choice"] = "auto"
            
        return params
    
    def _parse_response(self, response) -> ModelResponse:
        """Parse OpenAI API response."""
        message = response.choices[0].message
        
        tool_calls: Optional[List[FunctionCall]] = None
        if hasattr(message, 'tool_calls') and message.tool_calls:
            tool_calls = []
            for tool_call in message.tool_calls:
                if tool_call.type == "function":
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                        tool_calls.append({
                            "name": tool_call.function.name,
                            "arguments": arguments
                        })
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse function arguments: {e}")
        
        return ModelResponse(
            content=message.content or "",
            tool_calls=tool_calls,
            raw_response=response
        )
