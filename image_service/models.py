"""Data models for image service."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    QUEUED = "queued" 
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"


class Task(BaseModel):
    """Task model for image generation."""
    id: str
    scenario_id: str
    service: str
    name: str
    queue: int = 0
    status: TaskStatus = TaskStatus.PENDING
    created_at: str = ""
    updated_at: str = ""
    consumers: List[str] = Field(default_factory=list)
    params: Dict[str, Any] = Field(default_factory=dict)
    result_ref: str = ""
    
    # Image-specific fields
    prompt: Optional[str] = None
    slide_prompt_id: Optional[str] = None

    def model_post_init(self, __context) -> None:
        """Auto-populate timestamps and status."""
        current_time = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = current_time
        if not self.updated_at:
            self.updated_at = current_time
        
        if self.queue == 0 and self.status == TaskStatus.PENDING:
            self.status = TaskStatus.QUEUED

class ImageGenerationRequest(BaseModel):
    """Request model for image generation."""
    prompt: str = Field(..., description="Text prompt for image generation")
    size: str = Field(default="1024x1024", description="Image size")
    background: str = Field(default="auto")     # 
    quality: str = Field(default="low", description="Image quality")


class ImageGenerationResponse(BaseModel):
    """Response model for image generation."""
    success: bool
    message: str
    image_url: Optional[str] = None
    file_size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
