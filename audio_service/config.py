"""
Audio Service Configuration
"""

import os
import logging
from typing import Final
from dotenv import load_dotenv

load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY: Final[str] = os.getenv("OPENAI_API_KEY", "")

# Redis Configuration  
REDIS_HOST: Final[str] = os.getenv("REDIS_HOST", "redis")
REDIS_PORT: Final[int] = int(os.getenv("REDIS_PORT", "6379"))
REDIS_URL: Final[str] = os.getenv("REDIS_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}")
AUDIO_QUEUE: Final[str] = "queue:voice-service"

# TTS Configuration
DEFAULT_VOICE: Final[str] = "alloy"
DEFAULT_SPEED: Final[float] = 1.0
DEFAULT_FORMAT: Final[str] = "mp3"

# File Storage
OUTPUT_DIR: Final[str] = os.getenv("OUTPUT_DIR", "/app/output")
AUDIO_OUTPUT_DIR: Final[str] = f"{OUTPUT_DIR}/voice"

# Service Configuration
SERVICE_HOST: Final[str] = os.getenv("AUDIO_SERVICE_HOST", "0.0.0.0")
SERVICE_PORT: Final[int] = int(os.getenv("AUDIO_SERVICE_PORT", "8003"))

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)