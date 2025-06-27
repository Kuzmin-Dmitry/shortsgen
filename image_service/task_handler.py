"""
Task handler for image service using Redis-based architecture.
"""

import json
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
import redis.asyncio as redis
from config import REDIS_URL, IMAGE_QUEUE, logger
from models import Task, TaskStatus
from image_generator import ImageService


class TaskHandler:
    """Task handler for image service with Redis queue."""
    
    def __init__(self, redis_url: str = REDIS_URL):
        """Initialize task handler.
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.redis: Optional[Any] = None
        self.image_service = ImageService()
    
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
        """Listen for tasks in image-service queue."""
        if not self.redis:
            await self.connect()
        
        if not self.redis:
            raise RuntimeError("Failed to connect to Redis")
        
        logger.info(f"Started listening for tasks on {IMAGE_QUEUE}...")
        
        while True:
            try:
                # Block and wait for task (right pop from queue)
                result = await self.redis.brpop(IMAGE_QUEUE, timeout=1)
                
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
            if task.name == "CreateImage" or task.name == "CreateSlide":
                await self._handle_create_image(task)
            else:
                logger.warning(f"Unknown task type: {task.name}")
                await self._update_task_status(task_id, TaskStatus.FAILED)
                
        except Exception as e:
            logger.error(f"Task processing failed: {e}")
            await self._update_task_status(task_id, TaskStatus.FAILED)
    
    async def _get_task_data(self, task_id: str) -> Optional[Dict[str, Any]]:
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
            
            # Parse slide_ids field
            if "slide_ids" in task_data and task_data["slide_ids"]:
                task_data["slide_ids"] = json.loads(task_data["slide_ids"])
            else:
                task_data["slide_ids"] = []
            
            # Convert queue to int
            if "queue" in task_data:
                task_data["queue"] = int(task_data["queue"])
            
            return task_data
            
        except Exception as e:
            logger.error(f"Failed to get task data for {task_id}: {e}")
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
    
    async def _handle_create_image(self, task: Task) -> None:
        """Handle CreateImage/CreateSlide task.
        
        Args:
            task: Task to process
        """
        try:
            # Extract parameters
            prompt = task.params.get("prompt", "")
            style = task.params.get("style", "natural")
            size = task.params.get("resolution", "1024x1024")  # scenaries.yml uses 'resolution'
            quality = task.params.get("quality", "standard")
            
            # If no prompt in params but has slide_prompt_id, try to get prompt from dependency
            if not prompt and task.slide_prompt_id:
                prompt = await self._get_prompt_from_dependency(task.slide_prompt_id)
            
            # If still no prompt but has a direct prompt field, use it
            if not prompt and task.prompt:
                prompt = task.prompt
            
            if not prompt:
                raise ValueError("Prompt parameter is required")
            
            # Generate image
            result = await self.image_service.generate_image_async(
                prompt=prompt,
                size=size,
                style=style,
                quality=quality
            )
            
            if result["success"]:
                # Store result
                result_ref = result.get("image_path", result.get("filename", ""))
                
                # Update task as successful
                await self._update_task_status(
                    task.id, 
                    TaskStatus.SUCCESS, 
                    result_ref=result_ref
                )
                
                # Trigger consumers
                await self._trigger_consumers(task)
                
                logger.info(f"Image generation completed for task {task.id}")
            else:
                raise ValueError(result.get("message", "Image generation failed"))
                
        except Exception as e:
            logger.error(f"CreateImage task failed: {e}")
            await self._update_task_status(task.id, TaskStatus.FAILED)

    async def _get_prompt_from_dependency(self, prompt_task_id: str) -> str:
        """Get prompt result from dependency task.
        
        Args:
            prompt_task_id: ID of prompt generation task
            
        Returns:
            Generated prompt or empty string if not found
        """
        try:
            if not self.redis:
                return ""
            
            # Get prompt task data
            prompt_task_key = f"task:{prompt_task_id}"
            prompt_task_data = await self.redis.hgetall(prompt_task_key)
            
            if not prompt_task_data:
                logger.warning(f"Prompt task {prompt_task_id} not found")
                return ""
            
            # Check if task completed successfully
            if prompt_task_data.get("status") != "success":
                logger.warning(f"Prompt task {prompt_task_id} not completed successfully")
                return ""
            
            # Get result reference (should contain the prompt)
            result_ref = prompt_task_data.get("result_ref", "")
            if result_ref:
                # If result_ref is a file path, read the file
                # If it's direct text, return it
                # For now, assume it's direct text
                return result_ref
            
            logger.warning(f"No result found for prompt task {prompt_task_id}")
            return ""
            
        except Exception as e:
            logger.error(f"Failed to get prompt from dependency {prompt_task_id}: {e}")
            return ""
