"""
Text Service - Unified service for text generation using HTTP API.
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import logging
from text_client import TextClient

logger = logging.getLogger(__name__)

@dataclass
class ModelResponse:
    """Structured response from model generation."""
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    raw_response: Optional[Any] = None
    
    def has_tool_calls(self) -> bool:
        """Check if response contains tool calls."""
        return self.tool_calls is not None and len(self.tool_calls) > 0

class TextService:
    """Service for text generation using the text service HTTP API."""
    
    def __init__(self, base_url: Optional[str] = None):
        self.text_client = TextClient(base_url)
        logger.info("TextService initialized with HTTP client")

    def generate_text(
        self, 
        prompt: str, 
        functions: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 300,
        model: str = "openai",
        temperature: float = 0.7
    ) -> Union[str, Dict[str, Any], ModelResponse]:
        """Generate text using the text service API."""
        try:
            logger.debug(f"Generating text for prompt: {prompt[:50]}...")
            
            result = self.text_client.generate_text(
                prompt=prompt,
                functions=functions,
                max_tokens=max_tokens,
                model=model,
                temperature=temperature
            )
            
            return self._process_response(result)
                
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            raise

    def _process_response(self, result: Any) -> Union[str, Dict[str, Any], ModelResponse]:
        """Process and normalize API response."""
        if isinstance(result, dict):
            if "function_call" in result or "tool_calls" in result:
                return result
            elif "content" in result:
                return ModelResponse(
                    content=result["content"],
                    tool_calls=result.get("tool_calls"),
                    raw_response=result
                )
            else:
                return result
        else:
            return str(result)

    def health_check(self) -> bool:
        """Check if the text service is available."""
        return self.text_client.health_check()

__all__ = ['TextService', 'ModelResponse']