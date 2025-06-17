"""
Enhanced configuration management with validation.
"""

from typing import Dict, Any, Optional
import os
import logging
from pydantic import BaseModel, Field
from enum import Enum

logger = logging.getLogger(__name__)

class Environment(Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"

class ServiceConfig(BaseModel):
    """Base configuration for all services."""
    url: str = Field(..., description="Service URL")
    timeout: int = Field(default=30, ge=1, le=300, description="Request timeout in seconds")
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")
    
class AIServiceConfig(ServiceConfig):
    """Configuration for AI services."""
    api_key: Optional[str] = Field(default=None, description="API key for the service")
    model: str = Field(..., description="Model to use")
    
class MediaConfig(BaseModel):
    """Configuration for media generation."""
    image_size: str = Field(default="1024x1024", description="Generated image size")
    video_fps: int = Field(default=24, ge=1, le=60, description="Video FPS")
    audio_format: str = Field(default="mp3", description="Audio format")

class ApplicationConfig(BaseModel):
    """Main application configuration."""
    environment: Environment = Field(default=Environment.DEVELOPMENT)
    
    # Service configurations
    text_service: ServiceConfig
    audio_service: ServiceConfig  
    video_service: ServiceConfig
    image_service: AIServiceConfig
    
    # Media configuration
    media: MediaConfig
    
    # Processing configuration
    scene_count: int = Field(default=6, ge=1, le=20, description="Number of scenes to generate")
    test_mode: bool = Field(default=False, description="Enable test mode")
    
    @classmethod
    def from_env(cls) -> 'ApplicationConfig':
        """Create configuration from environment variables."""
        return cls(
            environment=Environment(os.getenv("ENVIRONMENT", "development")),
            text_service=ServiceConfig(
                url=os.getenv("TEXT_SERVICE_URL", "http://text-service:8002"),
                timeout=int(os.getenv("TEXT_SERVICE_TIMEOUT", "30")),
                max_retries=int(os.getenv("TEXT_SERVICE_RETRIES", "3"))
            ),
            audio_service=ServiceConfig(
                url=os.getenv("AUDIO_SERVICE_URL", "http://audio-service:8003"),
                timeout=int(os.getenv("AUDIO_SERVICE_TIMEOUT", "120")),
                max_retries=int(os.getenv("AUDIO_SERVICE_RETRIES", "3"))
            ),
            video_service=ServiceConfig(
                url=os.getenv("VIDEO_SERVICE_URL", "http://video-service:8004"),
                timeout=int(os.getenv("VIDEO_SERVICE_TIMEOUT", "300")),
                max_retries=int(os.getenv("VIDEO_SERVICE_RETRIES", "3"))
            ),
            image_service=AIServiceConfig(
                url=os.getenv("IMAGE_SERVICE_URL", "https://api.openai.com"),
                api_key=os.getenv("OPENAI_API_KEY"),
                model=os.getenv("DALLE_MODEL", "dall-e-2"),
                timeout=int(os.getenv("IMAGE_SERVICE_TIMEOUT", "60")),
                max_retries=int(os.getenv("IMAGE_SERVICE_RETRIES", "3"))
            ),
            media=MediaConfig(
                image_size=os.getenv("IMAGE_SIZE", "1024x1024"),
                video_fps=int(os.getenv("VIDEO_FPS", "24")),
                audio_format=os.getenv("AUDIO_FORMAT", "mp3")
            ),
            scene_count=int(os.getenv("SCENE_COUNT", "6")),
            test_mode=os.getenv("TEST_MODE", "false").lower() == "true"
        )

class ConfigManager:
    """Manages application configuration with validation."""
    
    def __init__(self):
        self._config: Optional[ApplicationConfig] = None
    
    @property
    def config(self) -> ApplicationConfig:
        """Get the current configuration."""
        if self._config is None:
            self._config = ApplicationConfig.from_env()
        return self._config
    
    def reload_config(self) -> ApplicationConfig:
        """Reload configuration from environment."""
        self._config = ApplicationConfig.from_env()
        return self._config
    
    def validate_config(self) -> bool:
        """Validate current configuration."""
        try:
            self.config  # This will trigger validation
            return True
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False

# Global configuration manager instance
config_manager = ConfigManager()
