"""
Text Service Configuration
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
TEXT_QUEUE: Final[str] = "queue:text-service"

# File Storage
OUTPUT_DIR: Final[str] = os.getenv("OUTPUT_DIR", "/app/output")
TEXT_OUTPUT_DIR: Final[str] = f"{OUTPUT_DIR}/text"

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
