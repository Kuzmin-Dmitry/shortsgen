"""
Workflow state management and tracking.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

class StageStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class StageResult:
    """Result of a workflow stage execution."""
    stage_name: str
    status: StageStatus
    data: Any = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None

@dataclass
class WorkflowState:
    """Tracks the state of workflow execution."""
    workflow_id: str = field(default_factory=lambda: f"wf_{int(datetime.now().timestamp())}")
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    results: Dict[str, StageResult] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_result(self, stage_name: str, result: StageResult):
        """Add a stage result to the workflow state."""
        self.results[stage_name] = result
    
    def get_completed_stages(self) -> List[str]:
        """Get list of completed stage names."""
        return [
            name for name, result in self.results.items()
            if result.status == StageStatus.COMPLETED
        ]
    
    def get_failed_stages(self) -> List[str]:
        """Get list of failed stage names."""
        return [
            name for name, result in self.results.items()
            if result.status == StageStatus.FAILED
        ]
    
    def is_completed(self) -> bool:
        """Check if workflow is completed."""
        return self.completed_at is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow state to dictionary for serialization."""
        return {
            "workflow_id": self.workflow_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "results": {
                name: {
                    "stage_name": result.stage_name,
                    "status": result.status.value,
                    "error_message": result.error_message,
                    "started_at": result.started_at.isoformat() if result.started_at else None,
                    "completed_at": result.completed_at.isoformat() if result.completed_at else None,
                    "duration_seconds": result.duration_seconds
                }
                for name, result in self.results.items()
            },
            "metadata": self.metadata
        }

@dataclass
class WorkflowResult:
    """Final result of workflow execution."""
    success: bool
    output_path: Optional[str] = None
    error_message: Optional[str] = None
    state: Optional[WorkflowState] = None
    elapsed_time: Optional[float] = None
