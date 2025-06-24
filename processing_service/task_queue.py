import json
from typing import Any, List
from uuid import UUID

import redis.asyncio as redis
from pydantic import BaseModel

from models import TaskOut
from config import REDIS_URL, REDIS_CHANNEL


class RedisQueue:
    """
    Redis адаптер для очереди и хранения задач.
    """
    def __init__(self, dsn: str = REDIS_URL, channel: str = REDIS_CHANNEL) -> None:
        self._dsn = dsn
        self._channel = channel
        self._redis: redis.Redis | None = None

    async def connect(self) -> None:
        if not self._redis:
            self._redis = await redis.from_url(self._dsn, decode_responses=True)
    
    async def push(self, data: BaseModel | dict[str, Any]) -> None:
        await self.connect()
        assert self._redis is not None
        payload = data.json() if isinstance(data, BaseModel) else json.dumps(data)
        await self._redis.rpush(self._channel, payload)

    async def save_task(self, task: TaskOut) -> None:
        """Сохраняет задачу в Redis"""
        await self.connect()
        assert self._redis is not None
        task_key = f"task:{task.id}"
        scenario_key = f"scenario:{task.scenario_id}"
        
        # Исключаем None значения для Redis
        task_data = {k: v for k, v in task.model_dump(mode="json").items() if v is not None}
        await self._redis.hset(task_key, mapping=task_data)
        await self._redis.sadd(scenario_key, str(task.id))

    async def get_task(self, task_id: UUID) -> TaskOut | None:
        """Получает задачу из Redis"""
        await self.connect()
        assert self._redis is not None
        task_key = f"task:{task_id}"
        task_data = await self._redis.hgetall(task_key)
        
        if not task_data:
            return None
            
        return TaskOut.model_validate(task_data)

    async def get_tasks_by_scenario(self, scenario_id: UUID) -> List[TaskOut]:
        """Получает все задачи сценария из Redis"""
        await self.connect()
        assert self._redis is not None
        scenario_key = f"scenario:{scenario_id}"
        task_ids = await self._redis.smembers(scenario_key)
        
        tasks = []
        for task_id_str in task_ids:
            task = await self.get_task(UUID(task_id_str))
            if task:
                tasks.append(task)
        
        return tasks
