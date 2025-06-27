"""
Task handler for audio service using Redis-based architecture.
"""

import json
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
import redis.asyncio as redis
from config import REDIS_URL, AUDIO_QUEUE, logger
from models import Task, TaskStatus
from tts_service import TTSService


class TaskHandler:
    """Task handler for audio service with Redis queue."""
    
    def __init__(self, redis_url: str = REDIS_URL):
        """Initialize task handler.
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.redis: Optional[Any] = None
        self.tts_service = TTSService()
    
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
        """Listen for tasks in audio-service queue."""
        if not self.redis:
            await self.connect()
        
        if not self.redis:
            raise RuntimeError("Failed to connect to Redis")
        
        logger.info(f"Started listening for tasks on {AUDIO_QUEUE}...")
        
        while True:
            try:
                # Block and wait for task (right pop from queue)
                result = await self.redis.brpop(AUDIO_QUEUE, timeout=1)
                
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
            if task.name == "CreateAudio" or task.name == "CreateVoice":
                await self._handle_create_audio(task)
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
    
    async def _handle_create_audio(self, task: Task) -> None:
        """Handle CreateAudio/CreateVoice task.
        
        Args:
            task: Task to process
        """
        try:
            # Extract parameters
            text = task.params.get("text", "")
            voice = task.params.get("voice", "alloy")
            speed = task.params.get("speed", 1.0)
            
            # If no text in params but has text_task_id, try to get text from dependency
            if not text and task.text_task_id:
                text = await self._get_text_from_dependency(task.text_task_id)
            
            if not text:
                raise ValueError("Text parameter is required")
            
            # Generate audio
            result = await self.tts_service.generate_audio_async(
                text=text,
                voice=voice,
                speed=speed
            )
            
            if result["success"]:
                # Store result
                result_ref = result.get("audio_path", "")
                
                # Update task as successful
                await self._update_task_status(
                    task.id, 
                    TaskStatus.SUCCESS, 
                    result_ref=result_ref
                )
                
                # Trigger consumers
                await self._trigger_consumers(task)
                
                logger.info(f"Audio generation completed for task {task.id}")
            else:
                raise ValueError(result.get("message", "Audio generation failed"))
                
        except Exception as e:
            logger.error(f"CreateAudio task failed: {e}")
            await self._update_task_status(task.id, TaskStatus.FAILED)

    async def _get_text_from_dependency(self, text_task_id: str) -> str:
        """Get text result from dependency task.
        
        Args:
            text_task_id: ID of text generation task
            
        Returns:
            Generated text or empty string if not found
        """
        try:
            if not self.redis:
                return ""
            
            # Get text task data
            text_task_key = f"task:{text_task_id}"
            text_task_data = await self.redis.hgetall(text_task_key)
            
            if not text_task_data:
                logger.warning(f"Text task {text_task_id} not found")
                return ""
            
            # Check if task completed successfully
            if text_task_data.get("status") != "success":
                logger.warning(f"Text task {text_task_id} not completed successfully")
                return ""
            
            # Get result reference (should contain the text)
            result_ref = text_task_data.get("result_ref", "")
            if result_ref:
                # If result_ref is a file path, read the file
                # If it's direct text, return it
                # For now, assume it's direct text
                return result_ref
            
            logger.warning(f"No result found for text task {text_task_id}")
            return ""
            
        except Exception as e:
            logger.error(f"Failed to get text from dependency {text_task_id}: {e}")
            return ""
