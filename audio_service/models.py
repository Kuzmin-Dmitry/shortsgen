"""
Data models for audio service.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task execution status - matches processing-service."""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"


class Task(BaseModel):
    """Task model matching processing-service structure."""
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
    
    # Task-specific fields (matching processing-service)
    count: Optional[int] = 1  # Number of task instances to create
    prompt: Optional[str] = None
    text_task_id: Optional[str] = None
    slide_prompt_id: Optional[str] = None
    slide_ids: Optional[List[str]] = None
    voice_track_id: Optional[str] = None
    
    # Audio-specific fields
    text: Optional[str] = None
    voice: Optional[str] = None
    speed: Optional[float] = None

    def model_post_init(self, __context) -> None:
        """Auto-populate timestamp fields and set status based on queue."""
        current_time = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = current_time
        if not self.updated_at:
            self.updated_at = current_time
        
        # Set status to QUEUED for tasks ready to execute (queue == 0)
        if self.queue == 0 and self.status == TaskStatus.PENDING:
            self.status = TaskStatus.QUEUED


class AudioGenerationRequest(BaseModel):
    """Request model for audio generation."""
    text: str = Field(..., description="Text to convert to speech")
    voice: str = Field(default="alloy", description="Voice to use")
    speed: float = Field(default=1.0, ge=0.25, le=4.0, description="Speech speed")
    format: str = Field(default="mp3", description="Audio format")


class AudioGenerationResponse(BaseModel):
    """Response model for audio generation."""
    success: bool
    message: str
    audio_url: Optional[str] = None
    duration: Optional[float] = None
    file_size: Optional[int] = None


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    service: str
    version: str
