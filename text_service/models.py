"""
Data models for Text Service API requests and responses.
"""

from pydantic import BaseModel
from typing import Optional


class TextGenerationRequest(BaseModel):
    """Request model for text generation endpoint."""
    prompt: str
    max_tokens: Optional[int] = 300
    temperature: Optional[float] = 0.8


class TextGenerationResponse(BaseModel):
    """Response model for text generation endpoint."""
    success: bool
    content: str = ""
    message: str = ""
    model_used: str = ""
    tokens_generated: int = 0
