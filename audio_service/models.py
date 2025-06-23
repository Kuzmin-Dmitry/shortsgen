from pydantic import BaseModel, Field, conint, confloat
from typing import Optional, Literal
from enum import Enum


class AudioLanguage(str, Enum):
    EN = "en"
    RU = "ru"


class AudioFormat(str, Enum):
    MP3 = "mp3"
    OPUS = "opus"
    AAC = "aac"
    FLAC = "flac"
    WAV = "wav"
    PCM = "pcm"


class TTSVoice(str, Enum):
    ALLOY = "alloy"
    ASH = "ash"
    BALLAD = "ballad"
    CORAL = "coral"
    ECHO = "echo"
    FABLE = "fable"
    ONYX = "onyx"
    NOVA = "nova"
    SAGE = "sage"
    SHIMMER = "shimmer"
    VERSE = "verse"
 

class AudioStyle(str, Enum):
    """For gpt-4o-mini-tts."""
    NEUTRAL = "neutral"
    NARRATION = "narration"
    NEWS = "news"
    EMOTIONAL = "emotional"
    DISCOURSE = "discourse"


class AudioGenerationRequest(BaseModel):
    text: str = Field(..., description="Text to convert to speech", min_length=1)
    language: AudioLanguage = Field(default=AudioLanguage.RU)
    voice: Optional[TTSVoice] = Field(default=None)
    format: Optional[AudioFormat] = Field(default=None)
    speed: float = Field(1.0, ge=0.25, le=4.0, description="0.25–4.0×")
    mock: Optional[bool] = Field(default=False)

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Привет, это обновлённый сервис!",
                "language": "ru",
                "voice": "alloy",
                "format": "mp3",
                "speed": 1.2,
                "pitch": 2,
                "style": "narration",
                "stream": False,
                "mock": False
            }
        }


class AudioGenerationResponse(BaseModel):
    """Response model for audio generation."""
    success: bool = Field(..., description="Whether the generation was successful")
    message: str = Field(..., description="Status message")
    file_size_kb: Optional[float] = Field(default=None, description="Generated file size in KB")
    duration_seconds: Optional[float] = Field(default=None, description="Audio duration in seconds")
    model_used: Optional[str] = None
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
