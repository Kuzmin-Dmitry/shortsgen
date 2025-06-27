"""Image Service Configuration."""

import os
import logging
from dotenv import load_dotenv

load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Redis Configuration  
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_URL = os.getenv("REDIS_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}")
IMAGE_QUEUE = "queue:image-service"

# Image Generation Configuration
DEFAULT_SIZE = "1024x1024"
DEFAULT_QUALITY = "low"
DEFAULT_BACKGROUND = "auto"

# File Storage
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/app/output")
IMAGES_OUTPUT_DIR = f"{OUTPUT_DIR}/images"

# Service Configuration
SERVICE_HOST = os.getenv("IMAGE_SERVICE_HOST", "0.0.0.0")
SERVICE_PORT = int(os.getenv("IMAGE_SERVICE_PORT", "8005"))

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)