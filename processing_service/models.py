from datetime import datetime
from enum import StrEnum
from typing import Optional, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TaskStatus(StrEnum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"


class TaskOut(BaseModel):
    """
    DTO, который мы отдаем наружу и кладем в очередь.
    """
    id: UUID = Field(default_factory=uuid4)
    scenario_id: UUID
    name: str
    status: TaskStatus = TaskStatus.pending
    message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ScenarioTemplate(BaseModel):
    """
    Шаблон сценария: имя + список задач, которые нужно сгенерировать.
    """
    name: str
    tasks: List[str]
