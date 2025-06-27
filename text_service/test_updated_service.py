"""
Test script for updated text-service with new Redis architecture.
"""

import asyncio
import json
from typing import Dict, Any
import redis.asyncio as redis
from models import Task, TaskStatus
from config import REDIS_URL, TEXT_QUEUE, logger


async def test_task_flow():
    """Test the complete task flow: publish -> process -> verify."""
    
    # Connect to Redis
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    
    try:
        await redis_client.ping()
        logger.info("Connected to Redis for testing")
        
        # Create test task
        test_task = Task(
            id="test_task_123",
            scenario_id="test_scenario_456",
            service="text-service",
            name="CreateText",
            queue=0,
            status=TaskStatus.QUEUED,
            prompt="Напиши короткий рассказ про кота",
            params={"model": "gpt-4o-mini"}
        )
        
        # Store task in Redis
        task_key = f"task:{test_task.id}"
        task_data = test_task.model_dump()
        
        # Convert lists/dicts to JSON strings for Redis
        task_data["consumers"] = json.dumps(task_data["consumers"])
        task_data["params"] = json.dumps(task_data["params"])
        
        result = await redis_client.hset(task_key, mapping=task_data)
        
        # Add task to queue  
        queue_result = await redis_client.lpush(TEXT_QUEUE, test_task.id)
        
        logger.info(f"Test task {test_task.id} added to queue")
        
        # Wait a bit for processing
        await asyncio.sleep(5)
        
        # Check task status
        updated_task_data = await redis_client.hgetall(task_key)
        
        if updated_task_data:
            status = updated_task_data.get("status", "unknown")
            result_ref = updated_task_data.get("result_ref", "")
            
            logger.info(f"Task status: {status}")
            logger.info(f"Result reference: {result_ref}")
            
            if status == TaskStatus.SUCCESS.value:
                logger.info("✅ Test PASSED: Task completed successfully")
            else:
                logger.error(f"❌ Test FAILED: Expected SUCCESS, got {status}")
        else:
            logger.error("❌ Test FAILED: Task data not found")
            
    except Exception as e:
        logger.error(f"Test error: {e}")
    finally:
        await redis_client.close()


async def test_slide_prompt_task():
    """Test CreateSlidePrompt task."""
    
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    
    try:
        # Create slide prompt test task
        test_task = Task(
            id="slide_test_789",
            scenario_id="test_scenario_456",
            service="text-service",
            name="CreateSlidePrompt",
            queue=0,
            status=TaskStatus.QUEUED,
            prompt="Создай заголовок для слайда о космосе",
            params={"model": "gpt-3.5-turbo"}
        )
        
        # Store and queue task
        task_key = f"task:{test_task.id}"
        task_data = test_task.model_dump()
        task_data["consumers"] = json.dumps(task_data["consumers"])
        task_data["params"] = json.dumps(task_data["params"])
        
        await redis_client.hset(task_key, mapping=task_data)
        await redis_client.lpush(TEXT_QUEUE, test_task.id)
        
        logger.info(f"Slide prompt test task {test_task.id} added to queue")
        
        # Wait for processing
        await asyncio.sleep(5)
        
        # Check results
        updated_data = await redis_client.hgetall(task_key)
        status = updated_data.get("status", "unknown")
        
        logger.info(f"Slide prompt task status: {status}")
        
        if status == TaskStatus.SUCCESS.value:
            logger.info("✅ Slide prompt test PASSED")
        else:
            logger.error(f"❌ Slide prompt test FAILED: {status}")
            
    except Exception as e:
        logger.error(f"Slide prompt test error: {e}")
    finally:
        await redis_client.close()


async def check_queue_status():
    """Check current queue status."""
    
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    
    try:
        queue_length = await redis_client.llen(TEXT_QUEUE)
        logger.info(f"Current {TEXT_QUEUE} length: {queue_length}")
        
        # List some tasks in queue
        if queue_length > 0:
            tasks = await redis_client.lrange(TEXT_QUEUE, 0, 5)
            logger.info(f"Tasks in queue: {tasks}")
            
    except Exception as e:
        logger.error(f"Queue check error: {e}")
    finally:
        await redis_client.close()


if __name__ == "__main__":
    print("Testing updated text-service...")
    
    async def run_tests():
        await check_queue_status()
        await test_task_flow()
        await test_slide_prompt_task()
        await check_queue_status()
    
    asyncio.run(run_tests())
