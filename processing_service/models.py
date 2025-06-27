"""
Data models for processing service.
"""

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
    """Task model from scenaries.yml template."""
    id: str
    scenario_id: str = ""  # Will be populated by ScenarioGenerator
    service: str
    name: str
    queue: int = 0
    status: TaskStatus = TaskStatus.PENDING
    created_at: str = ""  # Will be populated by ScenarioGenerator
    updated_at: str = ""  # Will be populated by ScenarioGenerator
    consumers: List[str] = Field(default_factory=list)
    params: Dict[str, Any] = Field(default_factory=dict)
    result_ref: str = ""
    
    # Task-specific fields
    count: Optional[int] = 1  # Number of task instances to create
    prompt: Optional[str] = None
    text_task_id: Optional[str] = None
    slide_prompt_id: Optional[str] = None
    slide_ids: Optional[List[str]] = None
    voice_track_id: Optional[str] = None

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


class Scenario(BaseModel):
    """Scenario template model."""
    scenario_id: str
    version: str
    name: str = ""  # Will be populated from scenario_id if missing
    variables: Dict[str, Any] = Field(default_factory=dict)
    tasks: List[Task] = Field(default_factory=list)

    def model_post_init(self, __context) -> None:
        """Auto-populate missing fields."""
        # Set default name if missing
        if not self.name:
            self.name = self.scenario_id
        
        # Populate scenario_id in all tasks and ensure timestamps
        current_time = datetime.now().isoformat()
        for task in self.tasks:
            if not task.scenario_id:
                task.scenario_id = self.scenario_id
            if not task.created_at:
                task.created_at = current_time
            if not task.updated_at:
                task.updated_at = current_time


class CreateScenarioRequest(BaseModel):
    """Request model for scenario creation."""
    scenario: str = "CreateVideo"
    description: str
    slides_count: int = Field(default=3, ge=1, le=10)


class CreateScenarioResponse(BaseModel):
    """Response model for scenario creation."""
    scenario_id: str
    tasks_created: int
    status: str = "pending"


class TaskStatusUpdate(BaseModel):
    """Model for task status updates."""
    status: TaskStatus
    result_ref: Optional[str] = None
