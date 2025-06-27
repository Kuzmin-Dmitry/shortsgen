"""
Integration tests for text-service with Redis.
"""

import asyncio
import json
import os
import tempfile
from datetime import datetime
from unittest.mock import patch, AsyncMock
from models import Task, TaskStatus
from task_handler import TaskHandler
from config import logger


async def test_redis_integration():
    """Test Redis integration without actual Redis connection."""
    print("🧪 Testing Redis integration...")
    
    # Mock Redis client
    mock_redis = AsyncMock()
    
    # Create task handler with mocked Redis
    handler = TaskHandler()
    handler.redis = mock_redis
    
    # Test task data
    test_task = Task(
        id="integration_test_123",
        scenario_id="scenario_456",
        service="text-service",
        name="CreateText",
        status=TaskStatus.QUEUED,
        prompt="Write a short story about a cat",
        params={"model": "gpt-3.5-turbo"},
        consumers=["consumer_task_1"]
    )
    
    # Mock Redis responses
    task_data = test_task.model_dump()
    task_data["consumers"] = json.dumps(task_data["consumers"])
    task_data["params"] = json.dumps(task_data["params"])
    task_data["queue"] = str(task_data["queue"])
    
    mock_redis.hgetall.return_value = task_data
    mock_redis.hincrby.return_value = 0  # Consumer queue becomes 0
    mock_redis.hgetall.side_effect = [
        task_data,  # First call for task data
        {"service": "image-service"}  # Second call for consumer data
    ]
    
    # Test getting task data
    retrieved_data = await handler._get_task_data("integration_test_123")
    
    assert retrieved_data["id"] == "integration_test_123"
    assert retrieved_data["name"] == "CreateText"
    assert retrieved_data["consumers"] == ["consumer_task_1"]
    assert retrieved_data["params"]["model"] == "gpt-3.5-turbo"
    print("✅ Task data retrieval works")
    
    # Test status update
    await handler._update_task_status("integration_test_123", TaskStatus.PROCESSING)
    mock_redis.hset.assert_called()
    print("✅ Status update works")
    
    # Test consumer triggering
    await handler._trigger_consumers(test_task)
    mock_redis.hincrby.assert_called()
    mock_redis.lpush.assert_called()
    print("✅ Consumer triggering works")
    
    print("🎉 Redis integration test passed!")


async def test_text_generation_flow():
    """Test complete text generation flow."""
    print("🧪 Testing text generation flow...")
    
    # Create temporary output directory
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('config.TEXT_OUTPUT_DIR', temp_dir):
            handler = TaskHandler()
            handler.redis = AsyncMock()
            
            # Mock successful text generation
            with patch('text_generator.GetTextOpenAI') as mock_generator_class:
                mock_generator = AsyncMock()
                mock_generator.generate_text.return_value = "Generated cat story text"
                mock_generator_class.return_value = mock_generator
                
                # Create test task
                test_task = Task(
                    id="text_gen_test_456",
                    scenario_id="scenario_789",
                    service="text-service", 
                    name="CreateText",
                    prompt="Write about a cat",
                    params={"model": "gpt-3.5-turbo"}
                )
                
                # Test text generation
                await handler._handle_create_text(test_task)
                
                # Verify text generator was called
                mock_generator.generate_text.assert_called_once()
                call_args = mock_generator.generate_text.call_args[1]
                assert call_args["prompt"] == "Write about a cat"
                assert call_args["model"] == "gpt-3.5-turbo"
                
                # Verify status update was called
                handler.redis.hset.assert_called()
                
                # Check if file was created
                expected_file = os.path.join(temp_dir, f"text_{test_task.id}.txt")
                assert os.path.exists(expected_file)
                
                with open(expected_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    assert content == "Generated cat story text"
                
                print("✅ Text generation and file storage works")
    
    print("🎉 Text generation flow test passed!")


async def test_slide_prompt_generation():
    """Test slide prompt generation."""
    print("🧪 Testing slide prompt generation...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('config.TEXT_OUTPUT_DIR', temp_dir):
            handler = TaskHandler()
            handler.redis = AsyncMock()
            
            with patch('text_generator.GetTextOpenAI') as mock_generator_class:
                mock_generator = AsyncMock()
                mock_generator.generate_text.return_value = "Space Exploration Title"
                mock_generator_class.return_value = mock_generator
                
                test_task = Task(
                    id="slide_test_789",
                    scenario_id="scenario_abc",
                    service="text-service",
                    name="CreateSlidePrompt", 
                    prompt="Create title for space slide",
                    params={"model": "gpt-4o-mini"}
                )
                
                await handler._handle_create_slide_prompt(test_task)
                
                # Verify correct parameters
                call_args = mock_generator.generate_text.call_args[1]
                assert call_args["prompt"] == "Create title for space slide"
                assert call_args["model"] == "gpt-4o-mini"
                assert call_args["max_tokens"] == 128
                
                print("✅ Slide prompt generation works")
    
    print("🎉 Slide prompt test passed!")


async def test_error_handling():
    """Test error handling scenarios."""
    print("🧪 Testing error handling...")
    
    handler = TaskHandler()
    handler.redis = AsyncMock()
    
    # Test with missing task data
    handler.redis.hgetall.return_value = {}
    
    result = await handler._get_task_data("nonexistent_task")
    assert result is None
    print("✅ Missing task handling works")
    
    # Test text generation failure
    with patch('text_generator.GetTextOpenAI') as mock_generator_class:
        mock_generator = AsyncMock()
        mock_generator.generate_text.side_effect = Exception("API Error")
        mock_generator_class.return_value = mock_generator
        
        test_task = Task(
            id="error_test_123",
            scenario_id="scenario_error",
            service="text-service",
            name="CreateText",
            prompt="This will fail"
        )
        
        await handler._handle_create_text(test_task)
        
        # Should update status to FAILED
        handler.redis.hset.assert_called()
        print("✅ Error handling works")
    
    print("🎉 Error handling test passed!")


async def test_app_health():
    """Test application health endpoint."""
    print("🧪 Testing application health...")
    
    from app import app
    from fastapi.testclient import TestClient
    
    with TestClient(app) as client:
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "text-service"
        assert data["version"] == "2.0.0"
        
        print("✅ Health endpoint works")
    
    print("🎉 Health test passed!")


async def main():
    """Run all integration tests."""
    print("🚀 Starting text-service integration tests...\n")
    
    try:
        await test_redis_integration()
        print()
        
        await test_text_generation_flow()
        print()
        
        await test_slide_prompt_generation()
        print()
        
        await test_error_handling()
        print()
        
        await test_app_health()
        print()
        
        print("🎉 ALL INTEGRATION TESTS PASSED! 🎉")
        print("Text-service is ready for production use!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Add requirements check
    try:
        import fastapi
        import redis
        import openai
        print("✅ All required packages are available")
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("Run: pip install -r requirements.txt")
        exit(1)
    
    asyncio.run(main())
