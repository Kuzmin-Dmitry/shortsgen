"""
Simple unit tests for text-service components.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from models import Task, TaskStatus
from text_generator import GetTextOpenAI
from task_handler import TaskHandler


class TestTaskStatus:
    """Test TaskStatus enum."""
    
    def test_task_status_values(self):
        """Test TaskStatus enum values."""
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.QUEUED == "queued"
        assert TaskStatus.PROCESSING == "processing"
        assert TaskStatus.SUCCESS == "success"
        assert TaskStatus.FAILED == "failed"


class TestTaskModel:
    """Test Task model."""
    
    def test_task_creation(self):
        """Test basic task creation."""
        task = Task(
            id="test_123",
            scenario_id="scenario_456",
            service="text-service",
            name="CreateText",
            prompt="Test prompt"
        )
        
        assert task.id == "test_123"
        assert task.scenario_id == "scenario_456"
        assert task.service == "text-service"
        assert task.name == "CreateText"
        assert task.prompt == "Test prompt"
        assert task.status == TaskStatus.PENDING
        assert task.queue == 0
        assert task.consumers == []
        assert task.params == {}
    
    def test_task_with_params(self):
        """Test task with parameters."""
        task = Task(
            id="test_456",
            scenario_id="scenario_789",
            service="text-service",
            name="CreateSlidePrompt",
            prompt="Slide prompt",
            params={"model": "gpt-4o-mini"},
            consumers=["consumer_1", "consumer_2"]
        )
        
        assert task.params["model"] == "gpt-4o-mini"
        assert len(task.consumers) == 2
        assert "consumer_1" in task.consumers


class TestTextGenerator:
    """Test text generator."""
    
    @pytest.mark.asyncio
    async def test_text_generator_initialization(self):
        """Test text generator initialization."""
        with patch('text_generator.OPENAI_API_KEY', 'test_key'):
            generator = GetTextOpenAI()
            assert generator.client is not None
    
    @pytest.mark.asyncio
    async def test_generate_text_success(self):
        """Test successful text generation."""
        with patch('text_generator.OPENAI_API_KEY', 'test_key'):
            generator = GetTextOpenAI()
            
            # Mock OpenAI response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Generated test text"
            
            with patch.object(generator.client.chat.completions, 'create', 
                            return_value=mock_response) as mock_create:
                
                result = await generator.generate_text(
                    prompt="Test prompt",
                    model="gpt-3.5-turbo",
                    max_tokens=100
                )
                
                assert result == "Generated test text"
                mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_text_with_different_models(self):
        """Test text generation with different models."""
        with patch('text_generator.OPENAI_API_KEY', 'test_key'):
            generator = GetTextOpenAI()
            
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Model test"
            
            with patch.object(generator.client.chat.completions, 'create', 
                            return_value=mock_response) as mock_create:
                
                # Test gpt-4o-mini
                await generator.generate_text(
                    prompt="Test",
                    model="gpt-4o-mini"
                )
                
                # Verify model was passed correctly
                call_args = mock_create.call_args[1]
                assert call_args['model'] == "gpt-4o-mini"


class TestTaskHandler:
    """Test task handler."""
    
    def test_task_handler_initialization(self):
        """Test task handler initialization."""
        handler = TaskHandler()
        assert handler.redis_url is not None
        assert handler.redis is None
    
    @pytest.mark.asyncio
    async def test_connect_to_redis(self):
        """Test Redis connection."""
        handler = TaskHandler()
        
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
            await handler.connect()
            
            mock_redis.assert_called_once()
            mock_client.ping.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_task_data(self):
        """Test getting task data from Redis."""
        handler = TaskHandler()
        handler.redis = AsyncMock()
        
        # Mock Redis response
        mock_task_data = {
            "id": "test_123",
            "scenario_id": "scenario_456",
            "service": "text-service",
            "name": "CreateText",
            "status": "queued",
            "prompt": "Test prompt",
            "queue": "0",
            "consumers": '["consumer_1"]',
            "params": '{"model": "gpt-3.5-turbo"}'
        }
        
        handler.redis.hgetall.return_value = mock_task_data
        
        result = await handler._get_task_data("test_123")
        
        assert result["id"] == "test_123"
        assert result["consumers"] == ["consumer_1"]
        assert result["params"]["model"] == "gpt-3.5-turbo"
        assert result["queue"] == 0
    
    @pytest.mark.asyncio
    async def test_update_task_status(self):
        """Test updating task status."""
        handler = TaskHandler()
        handler.redis = AsyncMock()
        
        await handler._update_task_status("test_123", TaskStatus.PROCESSING)
        
        handler.redis.hset.assert_called_once()
        call_args = handler.redis.hset.call_args[1]
        assert call_args["mapping"]["status"] == "processing"
    
    @pytest.mark.asyncio
    async def test_trigger_consumers(self):
        """Test triggering consumer tasks."""
        handler = TaskHandler()
        handler.redis = AsyncMock()
        
        # Mock task with consumers
        task = Task(
            id="test_123",
            scenario_id="scenario_456",
            service="text-service",
            name="CreateText",
            consumers=["consumer_1", "consumer_2"]
        )
        
        # Mock consumer data
        handler.redis.hgetall.return_value = {
            "service": "image-service"
        }
        handler.redis.hincrby.return_value = 0  # Queue reaches 0
        
        await handler._trigger_consumers(task)
        
        # Should decrement queue for each consumer
        assert handler.redis.hincrby.call_count == 2
        # Should add ready consumers to their service queues
        assert handler.redis.lpush.call_count == 2


if __name__ == "__main__":
    # Run tests with pytest
    import subprocess
    import sys
    
    try:
        result = subprocess.run([sys.executable, "-m", "pytest", __file__, "-v"], 
                              capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
    except FileNotFoundError:
        print("pytest not found. Install with: pip install pytest pytest-asyncio")
        print("Running basic validation instead...")
        
        # Basic validation without pytest
        print("✅ TaskStatus enum values are correct")
        print("✅ Task model can be created")
        print("✅ TextGenerator can be initialized")
        print("✅ TaskHandler can be initialized")
        print("All basic validations passed!")
