from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum


class AudioLanguage(str, Enum):
    """Supported languages for audio generation."""
    EN = "en"
    RU = "ru"


class AudioFormat(str, Enum):
    """Supported audio formats."""
    MP3 = "mp3"
    OPUS = "opus"
    AAC = "aac"
    FLAC = "flac"
    WAV = "wav"
    PCM = "pcm"


class TTSVoice(str, Enum):
    """Available TTS voices."""
    ALLOY = "alloy"
    ECHO = "echo"
    FABLE = "fable"
    ONYX = "onyx"
    NOVA = "nova"
    SHIMMER = "shimmer"


class AudioGenerationRequest(BaseModel):
    """Request model for audio generation."""
    text: str = Field(..., description="Text to convert to speech", min_length=1)
    language: AudioLanguage = Field(default=AudioLanguage.RU, description="Language of the text")
    voice: Optional[TTSVoice] = Field(default=None, description="Voice to use for TTS")
    format: Optional[AudioFormat] = Field(default=None, description="Audio format")
    mock: Optional[bool] = Field(default=False, description="Enable mock mode for testing without actual generation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Привет! Это тестовое сообщение для генерации аудио.",
                "language": "ru",
                "voice": "alloy",
                "format": "mp3",
                "mock": False
            }
        }


class AudioGenerationResponse(BaseModel):
    """Response model for audio generation."""
    success: bool = Field(..., description="Whether the generation was successful")
    message: str = Field(..., description="Status message")
    file_size_kb: Optional[float] = Field(default=None, description="Generated file size in KB")
    duration_seconds: Optional[float] = Field(default=None, description="Audio duration in seconds")
    error: Optional[str] = Field(default=None, description="Error message if generation failed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Audio generated successfully",
                "file_size_kb": 123.45,
                "duration_seconds": 15.2
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "service": "audio-service",
                "version": "1.0.0"
            }
        }
