"""
⏱️ In-memory сторадж – пару строк кода. Хотите Postgres –
меняете имплементацию, интерфейс тот же.
"""

from collections import defaultdict
from typing import Dict, List
from uuid import UUID

from models import TaskOut


class InMemoryStorage:
    def __init__(self) -> None:
        self._tasks: Dict[UUID, TaskOut] = {}
        self._by_scenario: Dict[UUID, List[UUID]] = defaultdict(list)

    # region Commands
    def save_task(self, task: TaskOut) -> None:
        self._tasks[task.id] = task
        self._by_scenario[task.scenario_id].append(task.id)

    # endregion

    # region Queries
    def get_task(self, task_id: UUID) -> TaskOut | None:
        return self._tasks.get(task_id)

    def get_tasks_by_scenario(self, scenario_id: UUID) -> List[TaskOut]:
        return [self._tasks[tid] for tid in self._by_scenario.get(scenario_id, [])]
    # endregion
