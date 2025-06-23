"""
Configuration module for Audio Service.

This module contains all configuration settings specific to the audio generation service.
"""

import os
import logging
from typing import Optional, Final
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================
# API Keys and Authentication
# ============================

OPENAI_API_KEY: Final[Optional[str]] = os.getenv("OPENAI_API_KEY")

# ============================
# Model Configuration
# ============================

# OpenAI TTS Model Settings
DEFAULT_TTS_MODEL: Final[str] = "gpt-4o-mini-tts"
DEFAULT_VOICE: Final[str] = "alloy"
DEFAULT_TTS_SPEED: Final[float] = 1.0          # 0.25 – 4.0
DEFAULT_TTS_PITCH: Final[int] = 0             # ±12 полутонов
DEFAULT_TTS_STYLE: Final[str] = "neutral"      # см. Enum AudioStyle
DEFAULT_AUDIO_FORMAT: Final[str] = "mp3"

# ============================
# Service Configuration
# ============================

SERVICE_HOST: Final[str] = os.getenv("AUDIO_SERVICE_HOST", "0.0.0.0")
SERVICE_PORT: Final[int] = int(os.getenv("AUDIO_SERVICE_PORT", "8003"))

# Audio output configuration
AUDIO_OUTPUT_DIR: Final[str] = os.getenv("AUDIO_OUTPUT_DIR", "./output/voice")
MAX_AUDIO_DURATION: Final[int] = int(os.getenv("MAX_AUDIO_DURATION", "300"))  # seconds

# ============================
# Logging Configuration
# ============================

LOG_LEVEL: Final[str] = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT: Final[str] = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'

def configure_logging() -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper()),
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("audio_service.log", encoding="utf-8")
        ]
    )