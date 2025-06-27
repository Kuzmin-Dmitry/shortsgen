"""
Video Service Configuration
"""

import os
import logging
from typing import Final
from dotenv import load_dotenv

load_dotenv()

# Redis Configuration  
REDIS_HOST: Final[str] = os.getenv("REDIS_HOST", "redis")
REDIS_PORT: Final[int] = int(os.getenv("REDIS_PORT", "6379"))
REDIS_URL: Final[str] = os.getenv("REDIS_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}")
VIDEO_QUEUE: Final[str] = "queue:video-service"

# Video Configuration
DEFAULT_FPS: Final[int] = 24
DEFAULT_RESOLUTION: Final[tuple] = (1920, 1080)
DEFAULT_FORMAT: Final[str] = "mp4"
DEFAULT_CODEC: Final[str] = "libx264"
DEFAULT_AUDIO_CODEC: Final[str] = "aac"

# File Storage
OUTPUT_DIR: Final[str] = os.getenv("OUTPUT_DIR", "/app/output")
VIDEO_OUTPUT_DIR: Final[str] = f"{OUTPUT_DIR}/video"
AUDIO_INPUT_DIR: Final[str] = f"{OUTPUT_DIR}/voice"
IMAGES_INPUT_DIR: Final[str] = f"{OUTPUT_DIR}/images"

# Video Effects Configuration
DEFAULT_SLIDE_DURATION: Final[float] = 3.0  # seconds per slide
DEFAULT_TRANSITION_DURATION: Final[float] = 0.5  # transition between slides
DEFAULT_ZOOM_FACTOR: Final[float] = 1.1  # ken burns effect zoom

# Service Configuration
SERVICE_HOST: Final[str] = os.getenv("VIDEO_SERVICE_HOST", "0.0.0.0")
SERVICE_PORT: Final[int] = int(os.getenv("VIDEO_SERVICE_PORT", "8004"))

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
