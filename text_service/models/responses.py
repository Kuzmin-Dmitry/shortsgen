"""Response models for Text Service API."""

from pydantic import BaseModel
from typing import Dict, Optional, Any, Union

class TextGenerationResponse(BaseModel):
    """Response model for text generation."""
    content: Union[str, Dict[str, Any]]
    success: bool
    model_used: str
    tokens_generated: Optional[int] = None

class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    status_code: int

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    service: str
    version: str
