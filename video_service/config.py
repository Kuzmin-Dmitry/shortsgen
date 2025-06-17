"""
Configuration module for Video Service.

This module centralizes all configuration settings used in the video service.
"""

import os
from typing import Final
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================
# Directory Configuration
# ============================

@dataclass
class Directories:
    """Application directory structure configuration."""
    
    base: str = os.getenv("DEFAULT_OUTPUT_DIR", "./output")
    scenes: str = ""
    video: str = ""
    voice: str = ""
    text: str = ""
    
    def __post_init__(self) -> None:
        """Initialize derived directory paths."""
        self.scenes = os.path.join(self.base, "scenes")
        self.video = os.path.join(self.base, "video")
        self.voice = os.path.join(self.base, "voice")
        self.text = os.path.join(self.base, "text")
        
        # Create directories if they don't exist
        for directory in [self.base, self.scenes, self.video, self.voice, self.text]:
            os.makedirs(directory, exist_ok=True)

DIRS = Directories()

# ============================
# Video Configuration
# ============================

# Video output settings
VIDEO_FILE_NAME: Final[str] = "video.mp4"
VIDEO_FILE_PATH: Final[str] = os.path.join(DIRS.video, VIDEO_FILE_NAME)

# Video generation settings
FONTSIZE: Final[int] = 72
CHUNK_SIZE: Final[int] = 512
HORIZONTAL_SIZE: Final[int] = 1024

# ============================
# Service URLs
# ============================

PROCESSING_SERVICE_URL: Final[str] = os.getenv("PROCESSING_SERVICE_URL", "http://processing-service:8001")
VIDEO_SERVICE_URL: Final[str] = os.getenv("VIDEO_SERVICE_URL", "http://video-service:8004")

# ============================
# Default Settings
# ============================

DEFAULT_FPS: Final[int] = 24
DEFAULT_WIDTH: Final[int] = 1024
DEFAULT_HEIGHT: Final[int] = 1024
DEFAULT_FADE_DURATION: Final[float] = 0.5

# Font configuration
DEFAULT_FONT_PATH: Final[str] = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FALLBACK_FONT_PATH: Final[str] = '/System/Library/Fonts/Arial.ttf'  # macOS fallback
WINDOWS_FONT_PATH: Final[str] = 'C:/Windows/Fonts/arial.ttf'  # Windows fallback

def get_system_font() -> str:
    """Get appropriate system font based on OS"""
    if os.path.exists(DEFAULT_FONT_PATH):
        return DEFAULT_FONT_PATH
    elif os.path.exists(FALLBACK_FONT_PATH):
        return FALLBACK_FONT_PATH
    elif os.path.exists(WINDOWS_FONT_PATH):
        return WINDOWS_FONT_PATH
    else:
        return DEFAULT_FONT_PATH  # Let moviepy handle font fallback
