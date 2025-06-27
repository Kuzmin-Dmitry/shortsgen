"""
Task handler for video service using Redis-based architecture.
"""

import json
import asyncio
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
import redis.asyncio as redis
from config import REDIS_URL, VIDEO_QUEUE, logger
from models import Task, TaskStatus
from video_generator import VideoService


class TaskHandler:
    """Task handler for video service with Redis queue."""
    
    def __init__(self, redis_url: str = REDIS_URL):
        """Initialize task handler.
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.redis: Optional[Any] = None
        self.video_service = VideoService()
    
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
        """Listen for tasks in video-service queue."""
        if not self.redis:
            await self.connect()
        
        if not self.redis:
            raise RuntimeError("Failed to connect to Redis")
        
        logger.info(f"Started listening for tasks on {VIDEO_QUEUE}...")
        
        while True:
            try:
                # Block and wait for task (right pop from queue)
                result = await self.redis.brpop(VIDEO_QUEUE, timeout=1)
                
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
            if task.name in ["CreateVideo", "GenerateVideo", "CreateVideoFromSlides"]:
                await self._handle_create_video(task)
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
    
    async def _handle_create_video(self, task: Task) -> None:
        """Handle CreateVideo/GenerateVideo task.
        
        Args:
            task: Task to process
        """
        try:
            # Get audio path from voice_track_id dependency
            audio_path = None
            if task.voice_track_id:
                audio_path = await self._get_audio_from_dependency(task.voice_track_id)
            
            # Get audio path from params if not from dependency
            if not audio_path:
                audio_path = task.params.get("audio_path", "")
            
            if not audio_path or not os.path.exists(audio_path):
                raise ValueError(f"Audio file not found: {audio_path}")
            
            # Get image paths from slide_ids dependencies
            image_paths = []
            if task.slide_ids:
                logger.info(f"Processing {len(task.slide_ids)} slide IDs: {task.slide_ids}")
                for slide_id in task.slide_ids:
                    img_path = await self._get_image_from_dependency(slide_id)
                    if img_path and os.path.exists(img_path):
                        image_paths.append(img_path)
                        logger.info(f"Added image path: {img_path}")
                    else:
                        logger.warning(f"Image not found for slide {slide_id}: {img_path}")
            
            # Get image paths from params if not from dependencies
            if not image_paths:
                image_paths = task.params.get("image_paths", [])
                logger.info(f"Using image paths from params: {image_paths}")
            
            logger.info(f"Final image paths: {image_paths}")
            
            if not image_paths:
                raise ValueError("No image paths provided")
            
            # Extract video generation parameters
            fps = task.params.get("fps", 24)
            resolution = task.params.get("resolution", (1920, 1080))
            slide_duration = task.params.get("slide_duration", 3.0)
            transition_duration = task.params.get("transition_duration", 0.5)
            enable_ken_burns = task.params.get("enable_ken_burns", True)
            zoom_factor = task.params.get("zoom_factor", 1.1)
            
            # Generate video
            result = await self.video_service.generate_video_async(
                audio_path=audio_path,
                image_paths=image_paths,
                fps=fps,
                resolution=resolution,
                slide_duration=slide_duration,
                transition_duration=transition_duration,
                enable_ken_burns=enable_ken_burns,
                zoom_factor=zoom_factor,
            )
            
            if result["success"]:
                # Store result
                result_ref = result.get("video_path", "")
                
                # Update task as successful
                await self._update_task_status(
                    task.id, 
                    TaskStatus.SUCCESS, 
                    result_ref=result_ref
                )
                
                # Trigger consumers
                await self._trigger_consumers(task)
                
                logger.info(f"Video generation completed for task {task.id}")
            else:
                raise ValueError(result.get("message", "Video generation failed"))
                
        except Exception as e:
            logger.error(f"CreateVideo task failed: {e}")
            await self._update_task_status(task.id, TaskStatus.FAILED)

    async def _get_audio_from_dependency(self, voice_task_id: str) -> str:
        """Get audio file path from voice dependency task.
        
        Args:
            voice_task_id: ID of voice generation task
            
        Returns:
            Audio file path or empty string if not found
        """
        try:
            if not self.redis:
                return ""
            
            # Get voice task data
            voice_task_key = f"task:{voice_task_id}"
            voice_task_data = await self.redis.hgetall(voice_task_key)
            
            if not voice_task_data:
                logger.warning(f"Voice task {voice_task_id} not found")
                return ""
            
            # Check if task completed successfully
            if voice_task_data.get("status") != "success":
                logger.warning(f"Voice task {voice_task_id} not completed successfully")
                return ""
            
            # Get result reference (audio file path)
            result_ref = voice_task_data.get("result_ref", "")
            if result_ref and os.path.exists(result_ref):
                return result_ref
            
            logger.warning(f"No audio file found for voice task {voice_task_id}")
            return ""
            
        except Exception as e:
            logger.error(f"Failed to get audio from dependency {voice_task_id}: {e}")
            return ""

    async def _get_image_from_dependency(self, slide_task_id: str) -> str:
        """Get image file path from slide dependency task.
        
        Args:
            slide_task_id: ID of slide/image generation task
            
        Returns:
            Image file path or empty string if not found
        """
        try:
            if not self.redis:
                return ""
            
            # Get slide task data
            slide_task_key = f"task:{slide_task_id}"
            slide_task_data = await self.redis.hgetall(slide_task_key)
            
            if not slide_task_data:
                logger.warning(f"Slide task {slide_task_id} not found")
                return ""
            
            # Check if task completed successfully
            if slide_task_data.get("status") != "success":
                logger.warning(f"Slide task {slide_task_id} not completed successfully")
                return ""
            
            # Get result reference (image file path)
            result_ref = slide_task_data.get("result_ref", "")
            logger.info(f"Found result_ref for slide task {slide_task_id}: {result_ref}")
            
            if result_ref and os.path.exists(result_ref):
                logger.info(f"Image file exists at: {result_ref}")
                return result_ref
            
            if result_ref:
                logger.warning(f"Image file does not exist at: {result_ref}")
            else:
                logger.warning(f"No result_ref found for slide task {slide_task_id}")
            
            logger.warning(f"No image file found for slide task {slide_task_id}")
            return ""
            
        except Exception as e:
            logger.error(f"Failed to get image from dependency {slide_task_id}: {e}")
            return ""
