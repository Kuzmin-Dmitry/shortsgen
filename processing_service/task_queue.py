"""
Task queue management for Redis.
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
import redis.asyncio as redis
from config import REDIS_URL, logger
from models import Task, TaskStatus


class TaskQueue:
    """Redis-based task queue manager."""
    
    def __init__(self, redis_url: str = REDIS_URL):
        """Initialize task queue.
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.redis: Optional[Any] = None
    
    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
            logger.info("Disconnected from Redis")
    
    async def publish_tasks(self, tasks: List[Task]) -> int:
        """Publish tasks to Redis queues.
        
        Args:
            tasks: List of tasks to publish
            
        Returns:
            Number of tasks published
        """
        if not self.redis:
            await self.connect()
        
        if not self.redis:
            raise RuntimeError("Failed to connect to Redis")
        
        published = 0
        
        for task in tasks:
            try:
                # Store task data
                task_key = f"task:{task.id}"
                task_data = task.model_dump()
                
                # Convert list fields to JSON strings for Redis
                if "consumers" in task_data and task_data["consumers"]:
                    task_data["consumers"] = json.dumps(task_data["consumers"])
                elif "consumers" in task_data:
                    task_data["consumers"] = "[]"
                    
                if "slide_ids" in task_data and task_data["slide_ids"]:
                    task_data["slide_ids"] = json.dumps(task_data["slide_ids"])
                elif "slide_ids" in task_data:
                    task_data["slide_ids"] = "[]"
                    
                if "params" in task_data and task_data["params"]:
                    task_data["params"] = json.dumps(task_data["params"])
                elif "params" in task_data:
                    task_data["params"] = "{}"
                
                # Remove None values
                task_data = {k: v for k, v in task_data.items() if v is not None}
                
                await self.redis.hset(task_key, mapping=task_data)
                
                # Add to service queue if ready (queue == 0)
                if task.queue == 0:
                    queue_name = f"queue:{task.service}"
                    await self.redis.lpush(queue_name, task.id)
                    logger.info(f"Task {task.id} added to {queue_name}")
                
                published += 1
                
            except Exception as e:
                logger.error(f"Failed to publish task {task.id}: {e}")
        
        logger.info(f"Published {published}/{len(tasks)} tasks to Redis")
        return published
    
    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        result_ref: Optional[str] = None
    ) -> None:
        """Update task status and trigger dependent tasks.
        
        Args:
            task_id: Task ID to update
            status: New status
            result_ref: Optional result reference
        """
        if not self.redis:
            await self.connect()
        
        if not self.redis:
            raise RuntimeError("Failed to connect to Redis")
        
        try:
            task_key = f"task:{task_id}"
            
            # Update task status
            updates = {
                "status": status.value,
                "updated_at": datetime.now().isoformat()
            }
            
            if result_ref:
                updates["result_ref"] = result_ref
            
            await self.redis.hset(task_key, mapping=updates)
            
            # If task completed successfully, trigger consumers
            if status == TaskStatus.SUCCESS:
                await self._trigger_consumers(task_id)
                
            logger.info(f"Updated task {task_id} status to {status.value}")
            
        except Exception as e:
            logger.error(f"Failed to update task {task_id}: {e}")
    
    async def _trigger_consumers(self, completed_task_id: str) -> None:
        """Trigger consumer tasks when dependency completes.
        
        Args:
            completed_task_id: ID of completed task
        """
        if not self.redis:
            return
            
        try:
            # Get task data
            task_key = f"task:{completed_task_id}"
            task_data = await self.redis.hgetall(task_key)
            
            if not task_data:
                logger.warning(f"Task {completed_task_id} not found")
                return
            
            # Parse consumers
            consumers_str = task_data.get("consumers", "[]")
            consumers = json.loads(consumers_str) if consumers_str else []
            
            # Update each consumer's queue count
            for consumer_id in consumers:
                consumer_key = f"task:{consumer_id}"
                
                # Decrement queue count
                new_queue = await self.redis.hincrby(consumer_key, "queue", -1)
                
                # If queue reaches 0, add to service queue
                if new_queue == 0:
                    consumer_data = await self.redis.hgetall(consumer_key)
                    service = consumer_data.get("service")
                    
                    if service:
                        queue_name = f"queue:{service}"
                        await self.redis.lpush(queue_name, consumer_id)
                        logger.info(
                            f"Task {consumer_id} ready, added to {queue_name}"
                        )
                
        except Exception as e:
            logger.error(f"Failed to trigger consumers for {completed_task_id}: {e}")
    
    async def get_task(self, task_id: str) -> Optional[Dict]:
        """Get task data by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task data or None if not found
        """
        if not self.redis:
            await self.connect()
        
        if not self.redis:
            return None
        
        try:
            task_key = f"task:{task_id}"
            task_data = await self.redis.hgetall(task_key)
            
            # Parse JSON fields back
            if "consumers" in task_data and task_data["consumers"]:
                task_data["consumers"] = json.loads(task_data["consumers"])
            if "slide_ids" in task_data and task_data["slide_ids"]:
                task_data["slide_ids"] = json.loads(task_data["slide_ids"])
            if "params" in task_data and task_data["params"]:
                task_data["params"] = json.loads(task_data["params"])
                
            return task_data
        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {e}")
            return None
    
    async def get_scenario_tasks(self, scenario_id: str) -> List[Dict]:
        """Get all tasks for a scenario.
        
        Args:
            scenario_id: Scenario ID
            
        Returns:
            List of task data
        """
        if not self.redis:
            await self.connect()
        
        if not self.redis:
            return []
        
        try:
            # Find all tasks for scenario
            pattern = "task:*"
            tasks = []
            
            async for key in self.redis.scan_iter(match=pattern):
                task_data = await self.redis.hgetall(key)
                if task_data.get("scenario_id") == scenario_id:
                    # Parse JSON fields
                    if "consumers" in task_data and task_data["consumers"]:
                        task_data["consumers"] = json.loads(task_data["consumers"])
                    if "slide_ids" in task_data and task_data["slide_ids"]:
                        task_data["slide_ids"] = json.loads(task_data["slide_ids"])
                    if "params" in task_data and task_data["params"]:
                        task_data["params"] = json.loads(task_data["params"])
                    tasks.append(task_data)
            
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to get scenario tasks {scenario_id}: {e}")
            return []


# Global task queue instance
task_queue = TaskQueue()
