"""
Configuration module for Audio Service.

This module contains all configuration settings for the audio microservice,
including OpenAI TTS API configuration and audio parameters.
"""

import os
import logging
from typing import Dict, Optional, Final
from enum import Enum
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================
# API Keys and Authentication
# ============================

OPENAI_API_KEY: Final[Optional[str]] = os.getenv("OPENAI_API_KEY")

# ============================
# Audio Service Configuration
# ============================

class TTSModel(Enum):
    """Available text-to-speech models."""
    TTS_1 = "tts-1"
    TTS_1_HD = "tts-1-hd"

class TTSVoice(Enum):
    """Available TTS voices."""
    ALLOY = "alloy"
    ECHO = "echo"
    FABLE = "fable"
    ONYX = "onyx"
    NOVA = "nova"
    SHIMMER = "shimmer"

class AudioFormat(Enum):
    """Available audio formats."""
    MP3 = "mp3"
    OPUS = "opus"
    AAC = "aac"
    FLAC = "flac"
    WAV = "wav"
    PCM = "pcm"

# TTS model settings
TTS_MODEL: Final[str] = TTSModel.TTS_1.value

# Audio configuration
AUDIO_CONFIG: Final[Dict[str, str]] = {
    "voice": TTSVoice.ALLOY.value,
    "format": AudioFormat.MP3.value
}

# ============================
# Directory Configuration
# ============================

DEFAULT_OUTPUT_DIR: Final[str] = os.getenv("DEFAULT_OUTPUT_DIR", "./output")

# ============================
# Testing Configuration
# ============================

# Testing flags
TEST_AUDIO: Final[bool] = os.getenv("TEST_AUDIO", "true").lower() == "true"

# ============================
# Service Configuration
# ============================

# Service port
SERVICE_PORT: Final[int] = int(os.getenv("AUDIO_SERVICE_PORT", "8003"))

# Service host
SERVICE_HOST: Final[str] = os.getenv("AUDIO_SERVICE_HOST", "0.0.0.0")

# ============================
# Logger Configuration
# ============================

# Configure application logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
