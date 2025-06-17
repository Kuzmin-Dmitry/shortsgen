"""Request models for Text Service API."""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any

class TextGenerationRequest(BaseModel):
    """Request model for text generation."""
    prompt: str = Field(..., description="The text prompt to generate from")
    functions: Optional[List[Dict[str, Any]]] = Field(None, description="List of function definitions for the model")
    max_tokens: int = Field(300, description="Maximum number of tokens in the response", ge=1, le=4000)
    model: str = Field("openai", description="Model type to use (openai or gemma)")
    temperature: float = Field(0.8, description="Controls randomness in generation", ge=0.0, le=1.0)
    system_prompt: Optional[str] = Field(None, description="Optional system prompt to set context")
    mock: Optional[bool] = Field(False, description="Enable mock mode for testing without actual generation")
