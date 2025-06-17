"""
Configuration module for Text Service.

This module contains all configuration settings specific to the text generation service.
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

# OpenAI Model Settings
DEFAULT_OPENAI_MODEL: Final[str] = "gpt-4o-mini"
DEFAULT_MAX_TOKENS: Final[int] = 300
DEFAULT_TEMPERATURE: Final[float] = 0.8

# Local model settings
LOCAL_TEXT_TO_TEXT_MODEL: Final[str] = os.getenv("LOCAL_TEXT_TO_TEXT_MODEL", "gemma2:2b")
LOCAL_MODEL_URL: Final[str] = os.getenv("LOCAL_MODEL_URL", "http://localhost:11434/api/generate")

# ============================
# Service Configuration
# ============================

SERVICE_HOST: Final[str] = os.getenv("TEXT_SERVICE_HOST", "0.0.0.0")
SERVICE_PORT: Final[int] = int(os.getenv("TEXT_SERVICE_PORT", "8002"))

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
            logging.FileHandler('text_service.log', encoding='utf-8')
        ]
    )
