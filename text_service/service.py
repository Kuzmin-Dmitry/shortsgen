"""Core text generation service."""

import logging
from typing import List, Optional, Dict, Any, Union
from models.domain import ModelType, ModelResponse
from providers import ProviderFactory
from exceptions import ModelException

logger = logging.getLogger(__name__)

class TextGenerationService:
    """Main service for text generation operations."""
    
    def __init__(self):
        """Initialize the text generation service."""
        self.provider_factory = ProviderFactory()
        logger.info("TextGenerationService initialized")
    
    def generate_text(
        self,
        prompt: str,
        functions: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 300,
        model: Union[str, ModelType] = ModelType.OPENAI,
        temperature: float = 0.8,
        system_prompt: Optional[str] = None
    ) -> Union[str, Dict[str, Any]]:
        """Generate text using the specified model."""
        # Convert string to enum if needed
        if isinstance(model, str):
            try:
                model = ModelType(model.lower())
            except ValueError:
                model = ModelType.GEMMA if model.lower() == "gemma" else ModelType.OPENAI
        
        logger.info(f"Generating text with model={model.value}")
        
        try:
            provider = self.provider_factory.create_provider(model)
            
            if not provider.is_available():
                raise ModelException(f"Provider {model.value} is not available")
            
            response = provider.generate_text(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                functions=functions,
                system_prompt=system_prompt
            )
            
            # Return appropriate content based on tool calls
            if response.has_tool_calls() and response.tool_calls:
                return response.tool_calls[0]['arguments']
            else:
                return response.content
                
        except ModelException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in text generation: {e}")
            raise ModelException(f"Unexpected error: {e}")
    
    def extract_queries_from_tool_call(self, tool_call_result: Dict[str, Any]) -> List[str]:
        """Extract search queries from tool call result."""
        if "queries" in tool_call_result:
            return tool_call_result["queries"]
        
        if "scenes" in tool_call_result and isinstance(tool_call_result["scenes"], list):
            return [scene.get("query", "") for scene in tool_call_result["scenes"]]
        
        return []
