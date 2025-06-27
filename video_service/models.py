"""
Data models for video service.
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
    count: Optional[int] = 1
    prompt: Optional[str] = None
    text_task_id: Optional[str] = None
    slide_prompt_id: Optional[str] = None
    slide_ids: Optional[List[str]] = None
    voice_track_id: Optional[str] = None
    
    # Video-specific fields
    audio_path: Optional[str] = None
    image_paths: Optional[List[str]] = None
    fps: Optional[int] = None
    resolution: Optional[tuple] = None

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


class VideoGenerationRequest(BaseModel):
    """Request model for video generation."""
    audio_path: str = Field(..., description="Path to audio file")
    image_paths: List[str] = Field(..., description="List of image file paths")
    fps: int = Field(default=24, description="Frames per second")
    resolution: Optional[tuple] = Field(default=(1920, 1080), description="Video resolution")
    slide_duration: float = Field(default=3.0, description="Duration per slide in seconds")
    transition_duration: float = Field(default=0.5, description="Transition duration")
    enable_ken_burns: bool = Field(default=True, description="Enable Ken Burns effect")
    zoom_factor: float = Field(default=1.1, description="Zoom factor for Ken Burns")


class VideoGenerationResponse(BaseModel):
    """Response model for video generation."""
    success: bool
    message: str
    video_url: Optional[str] = None
    duration: Optional[float] = None
    file_size: Optional[int] = None
    resolution: Optional[tuple] = None


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    service: str
    version: str
