"""
Text API Client - HTTP client for communicating with the Text Service.

This module provides a simple HTTP client for making API calls to the
text service microservice via REST API.
"""

import requests
import logging
from typing import Dict, List, Optional, Any, Union
import os

logger = logging.getLogger(__name__)


class TextClient:
    """
    HTTP client for communicating with the Text Service API.
    
    This client makes HTTP requests to the text service microservice
    and handles API communication errors.
    """
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the text client.
        
        Args:
            base_url: Base URL of the text service API
        """
        self.base_url = (base_url or os.getenv("TEXT_SERVICE_URL", "http://text-service:8002")).rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        logger.info(f"TextClient initialized with base URL: {self.base_url}")

    def generate_text(
        self,
        prompt: str,
        functions: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 300,
        model: str = "openai",
        temperature: float = 0.7,
        timeout: int = 60
    ) -> Union[str, Dict[str, Any]]:
        """
        Generate text using the text service API.
        
        Args:
            prompt: The text prompt for generation
            functions: Optional function definitions for tool calling
            max_tokens: Maximum number of tokens to generate
            model: Model to use for generation
            temperature: Sampling temperature
            timeout: Request timeout in seconds
            
        Returns:
            Generated text or function call result
            
        Raises:
            requests.RequestException: If API request fails
        """
        try:
            payload = {
                "prompt": prompt,
                "max_tokens": max_tokens,
                "model": model,
                "temperature": temperature
            }
            
            if functions:
                payload["functions"] = functions
            
            logger.debug(f"Making text generation request: {prompt[:50]}...")
            
            response = self.session.post(
                f"{self.base_url}/generate",
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Handle different response formats
            if isinstance(result, dict):
                if "text" in result:
                    return result["text"]
                elif "content" in result:
                    return result["content"]
                elif "function_call" in result:
                    return result["function_call"]
                else:
                    return result
            else:
                return str(result)
                
        except requests.RequestException as e:
            logger.error(f"Text generation API request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during text generation: {e}")
            raise

    def health_check(self) -> bool:
        """
        Check if the text service is healthy.
        
        Returns:
            bool: True if service is healthy, False otherwise
        """
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Text service health check failed: {e}")
            return False
