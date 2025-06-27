"""
Image Service Configuration
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
IMAGE_QUEUE: Final[str] = "queue:image-service"

# Image Generation Configuration
DEFAULT_SIZE: Final[str] = "1024x1024"
DEFAULT_STYLE: Final[str] = "natural"
DEFAULT_QUALITY: Final[str] = "low"

# File Storage
OUTPUT_DIR: Final[str] = os.getenv("OUTPUT_DIR", "/app/output")
IMAGES_OUTPUT_DIR: Final[str] = f"{OUTPUT_DIR}/images"

# Service Configuration
SERVICE_HOST: Final[str] = os.getenv("IMAGE_SERVICE_HOST", "0.0.0.0")
SERVICE_PORT: Final[int] = int(os.getenv("IMAGE_SERVICE_PORT", "8005"))

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)