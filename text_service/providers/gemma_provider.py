"""Gemma provider implementation."""

import logging
from typing import List, Optional, Dict, Any
import requests
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from .base import LLMProvider
from models.domain import ModelResponse
from exceptions import GemmaException
from config import LOCAL_TEXT_TO_TEXT_MODEL, LOCAL_MODEL_URL

logger = logging.getLogger(__name__)

class GemmaProvider(LLMProvider):
    """Local Gemma model provider."""
    
    def __init__(self, model_url: Optional[str] = None, model_name: Optional[str] = None):
        """Initialize Gemma provider."""
        self.model_url = model_url or LOCAL_MODEL_URL
        self.model_name = model_name or LOCAL_TEXT_TO_TEXT_MODEL
        
    def is_available(self) -> bool:
        """Check if Gemma model is available."""
        try:
            response = requests.get(self.model_url.replace('/api/generate', '/api/tags'), timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def generate_text(
        self,
        prompt: str,
        max_tokens: int = 300,
        temperature: float = 0.8,
        functions: Optional[List[Dict[str, Any]]] = None,
        system_prompt: Optional[str] = None
    ) -> ModelResponse:
        """Generate text using Gemma model."""
        try:
            payload = self._build_payload(prompt, max_tokens, temperature, system_prompt)
            response = requests.post(self.model_url, json=payload)
            
            if response.status_code == 200:
                return self._parse_response(response.json())
            else:
                raise GemmaException(f"Gemma API returned status {response.status_code}")
                
        except requests.RequestException as e:
            logger.error(f"Gemma model request error: {e}")
            raise GemmaException(f"Gemma model error: {e}")
        except Exception as e:
            logger.error(f"Unexpected Gemma error: {e}")
            raise GemmaException(f"Unexpected Gemma error: {e}")
    
    def _build_payload(
        self, 
        prompt: str, 
        max_tokens: int, 
        temperature: float,
        system_prompt: Optional[str]
    ) -> Dict[str, Any]:
        """Build payload for Gemma API."""
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
            
        return {
            "model": self.model_name,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": 0.9,
                "num_ctx": 4096
            }
        }
    
    def _parse_response(self, response_json: Dict[str, Any]) -> ModelResponse:
        """Parse Gemma API response."""
        text_response = response_json.get("response", "")
        return ModelResponse(content=text_response, raw_response=response_json)
