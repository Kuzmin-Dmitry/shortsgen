"""
Task handler for text service using new Redis-based architecture.
"""

import json
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
import redis.asyncio as redis
from config import REDIS_URL, TEXT_QUEUE, logger
from models import Task, TaskStatus


class TaskHandler:
    """Task handler for text service with Redis queue."""
    
    def __init__(self, redis_url: str = REDIS_URL):
        """Initialize task handler.
        
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
    
    async def listen_tasks(self) -> None:
        """Listen for tasks in text-service queue."""
        if not self.redis:
            await self.connect()
        
        if not self.redis:
            raise RuntimeError("Failed to connect to Redis")
        
        logger.info(f"Started listening for tasks on {TEXT_QUEUE}...")
        
        while True:
            try:
                # Block and wait for task (right pop from queue)
                result = await self.redis.brpop(TEXT_QUEUE, timeout=1)
                
                if result:
                    _, task_id = result
                    await self._process_task(task_id)
                else:
                    # Timeout - continue listening
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"Error listening for tasks: {e}")
                await asyncio.sleep(1)
    
    async def _process_task(self, task_id: str) -> None:
        """Process a single task.
        
        Args:
            task_id: Task ID to process
        """
        try:
            # Get task data from Redis
            task_data = await self._get_task_data(task_id)
            if not task_data:
                logger.warning(f"Task {task_id} not found")
                return
            
            # Parse task
            task = Task(**task_data)
            
            # Skip if task is not queued
            if task.status != TaskStatus.QUEUED:
                logger.info(f"Task {task_id} status is {task.status}, skipping")
                return
            
            # Update status to processing
            await self._update_task_status(task_id, TaskStatus.PROCESSING)
            
            logger.info(f"Processing task {task_id}: {task.name}")
            
            # Route to appropriate handler
            if task.name == "CreateText":
                await self._handle_create_text(task)
            elif task.name == "CreateSlidePrompt":
                await self._handle_create_slide_prompt(task)
            else:
                logger.warning(f"Unknown task type: {task.name}")
                await self._update_task_status(task_id, TaskStatus.FAILED)
                return
            
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}")
            await self._update_task_status(task_id, TaskStatus.FAILED)
    
    async def _handle_create_text(self, task: Task) -> None:
        """Handle CreateText task.
        
        Args:
            task: Task to process
        """
        try:
            from text_generator import GetTextOpenAI
            generator = GetTextOpenAI()
            
            # Get model from params
            model = task.params.get("model", "gpt-4o-mini")
            
            # Generate text
            result = await generator.generate_text(
                prompt=task.prompt or "Напиши короткую историю",
                model=model,
                tone="neutral",
                language="ru",
                max_tokens=512
            )
            
            # Store result
            result_ref = await self._store_text_result(task.scenario_id, task.id, result)
            
            # Update task as successful
            await self._update_task_status(
                task.id, 
                TaskStatus.SUCCESS, 
                result_ref=result_ref
            )
            
            # Trigger consumers
            await self._trigger_consumers(task)
            
        except Exception as e:
            logger.error(f"CreateText failed for task {task.id}: {e}")
            await self._update_task_status(task.id, TaskStatus.FAILED)
    
    async def _handle_create_slide_prompt(self, task: Task) -> None:
        """Handle CreateSlidePrompt task.
        
        Args:
            task: Task to process
        """
        try:
            from text_generator import GetTextOpenAI
            generator = GetTextOpenAI()
            
            # Get model from params
            model = task.params.get("model", "gpt-4o-mini")
            
            # Generate slide prompt
            result = await generator.generate_text(
                prompt=task.prompt or "Создай заголовок для слайда",
                model=model,
                tone="neutral", 
                language="ru",
                max_tokens=128
            )
            
            # Store result
            result_ref = await self._store_text_result(task.scenario_id, task.id, result)
            
            # Update task as successful
            await self._update_task_status(
                task.id,
                TaskStatus.SUCCESS,
                result_ref=result_ref
            )
            
            # Trigger consumers
            await self._trigger_consumers(task)
            
        except Exception as e:
            logger.error(f"CreateSlidePrompt failed for task {task.id}: {e}")
            await self._update_task_status(task.id, TaskStatus.FAILED)
    
    async def _get_task_data(self, task_id: str) -> Optional[Dict]:
        """Get task data from Redis.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task data or None if not found
        """
        if not self.redis:
            return None
        
        try:
            task_key = f"task:{task_id}"
            task_data = await self.redis.hgetall(task_key)
            
            if not task_data:
                return None
            
            # Parse JSON fields
            if "consumers" in task_data and task_data["consumers"]:
                task_data["consumers"] = json.loads(task_data["consumers"])
            else:
                task_data["consumers"] = []
                
            if "params" in task_data and task_data["params"]:
                task_data["params"] = json.loads(task_data["params"])
            else:
                task_data["params"] = {}
            
            # Convert queue to int
            if "queue" in task_data:
                task_data["queue"] = int(task_data["queue"])
            
            return task_data
            
        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {e}")
            return None
    
    async def _update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        result_ref: Optional[str] = None
    ) -> None:
        """Update task status in Redis.
        
        Args:
            task_id: Task ID
            status: New status
            result_ref: Optional result reference
        """
        if not self.redis:
            return
        
        try:
            task_key = f"task:{task_id}"
            
            updates = {
                "status": status.value,
                "updated_at": datetime.now().isoformat()
            }
            
            if result_ref:
                updates["result_ref"] = result_ref
            
            await self.redis.hset(task_key, mapping=updates)
            logger.info(f"Updated task {task_id} status to {status.value}")
            
        except Exception as e:
            logger.error(f"Failed to update task {task_id}: {e}")
    
    async def _trigger_consumers(self, task: Task) -> None:
        """Trigger consumer tasks by decrementing their queue count.
        
        Args:
            task: Completed task
        """
        if not self.redis or not task.consumers:
            return
        
        try:
            for consumer_id in task.consumers:
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
                        logger.info(f"Consumer {consumer_id} ready, added to {queue_name}")
        
        except Exception as e:
            logger.error(f"Failed to trigger consumers for task {task.id}: {e}")
    
    async def _store_text_result(
        self,
        scenario_id: str,
        task_id: str,
        text: str
    ) -> str:
        """Store generated text result.
        
        Args:
            scenario_id: Scenario ID
            task_id: Task ID
            text: Generated text
            
        Returns:
            Result reference path
        """
        from config import TEXT_OUTPUT_DIR
        import os
        
        try:
            os.makedirs(TEXT_OUTPUT_DIR, exist_ok=True)
            file_path = f"{TEXT_OUTPUT_DIR}/text_{task_id}.txt"
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)
            
            logger.info(f"Text saved to: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to store text result: {e}")
            return ""
