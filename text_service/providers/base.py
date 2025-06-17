"""Abstract base class for language model providers."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from models.domain import ModelResponse

class LLMProvider(ABC):
    """Abstract base class for language model providers."""
    
    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        max_tokens: int = 300,
        temperature: float = 0.8,
        functions: Optional[List[Dict[str, Any]]] = None,
        system_prompt: Optional[str] = None
    ) -> ModelResponse:
        """Generate text using the model provider."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the model provider is available."""
        pass
