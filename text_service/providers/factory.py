"""Provider factory and registry."""

from typing import Dict, Type
from .base import LLMProvider
from .openai_provider import OpenAIProvider
from .gemma_provider import GemmaProvider
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from models.domain import ModelType
from exceptions import ModelException

class ProviderFactory:
    """Factory for creating LLM providers."""
    
    _providers: Dict[ModelType, Type[LLMProvider]] = {
        ModelType.OPENAI: OpenAIProvider,
        ModelType.GEMMA: GemmaProvider
    }
    
    @classmethod
    def create_provider(cls, model_type: ModelType, **kwargs) -> LLMProvider:
        """Create a provider instance for the given model type."""
        if model_type not in cls._providers:
            raise ModelException(f"Unsupported model type: {model_type}")
        
        provider_class = cls._providers[model_type]
        return provider_class(**kwargs)
    
    @classmethod
    def register_provider(cls, model_type: ModelType, provider_class: Type[LLMProvider]):
        """Register a new provider."""
        cls._providers[model_type] = provider_class
