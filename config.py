"""
Configuration module for ShortsGen application.

This module centralizes all configuration settings used throughout the application,
organized by functional areas with proper typing for better AI assistance.
"""

import os
import logging
from typing import Dict, List, Optional, TypedDict, Final
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================
# API Keys and Authentication
# ============================

DEEPAI_API_KEY: Final[Optional[str]] = os.getenv("DEEPAI_API_KEY")
OPENAI_API_KEY: Final[Optional[str]] = os.getenv("OPENAI_API_KEY")

# URL of the processing service (api-gateway communicates with it)
PROCESSING_SERVICE_URL: Final[str] = os.getenv("PROCESSING_SERVICE_URL", "http://localhost:8001")

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

# Initialize directories configuration
DIRS = Directories()

# File paths
VOICE_FILE_PATH: Final[str] = os.path.join(DIRS.voice, "voice.mp3")
VIDEO_FILE_PATH: Final[str] = os.path.join(DIRS.video, "video.mp4")

# ============================
# AI Models Configuration
# ============================

class ImageModel(Enum):
    """Available image generation models."""
    DALLE_2 = "dall-e-2"
    DALLE_3 = "dall-e-3"

class TextModel(Enum):
    """Available text generation models."""
    GPT4O_MINI_TTS = "gpt-4o-mini-tts"
    GEMMA3_12B = "gemma3:12b"

class ImageSizes(Enum):
    """Available image size configurations."""
    small = "256x256"
    medium = "512x512"
    large = "1024x1024"

GENERATED_IMAGE_SIZE: Final[str] = ImageSizes.large.value
DALLE_MODEL: Final[str] = ImageModel.DALLE_2.value

# Text model settings
OPENAI_MODEL: Final[str] = TextModel.GPT4O_MINI_TTS.value
LOCAL_TEXT_TO_TEXT_MODEL: Final[str] = TextModel.GEMMA3_12B.value
LOCAL: Final[bool] = False  # Working with local models: "run ollama serve"

# ============================
# Audio Configuration
# ============================

class AudioConfig(TypedDict):
    """Audio generation configuration."""
    voice: str
    format: str

# Audio configuration
AUDIO_CONFIG: Final[AudioConfig] = {
    "voice": "coral",
    "format": "mp3"
}

# Audio narration style instructions
AUDIO_INSTRUCTIONS: Final[str] = """
Affect: A gentle, curious narrator with a Russian accent, guiding a magical, child-friendly adventure.
Tone: Magical, warm, and inviting, creating a sense of wonder and excitement.
Pacing: Steady and measured, with slight pauses to emphasize magical moments.
Emotion: Wonder, curiosity, and a sense of adventure, with a lighthearted and positive vibe throughout.
Pronunciation: Clear and precise, with an emphasis on storytelling.
"""

# ============================
# Prompt Templates
# ============================

@dataclass
class PromptTemplates:
    """Templates for various AI prompts used in the application."""
    
    system: str = (
        "You are a highly skilled audio assistant capable of transforming text into vivid, emotionally charged audio. "
        "Maintain a voice pitch between 180–230 Hz and a dynamic range that spans from a soft whisper to powerful delivery, "
        "allowing for expressive emotional bursts. "
        "Adopt a resonant tone with a slight huskiness and sarcastic nuances; minimal jitter and shimmer ensure sound stability. "
        "Speak with clear diction, incorporating expressive intonation shifts and pauses that convey confidence and playful mockery. "
        "Instantly adjust your tone from mocking irony to deep expressiveness, reflecting a rich inner world and bold character. "
        "Speak with a clear Russian accent."
    )
    
    user: str = "Please narrate the following text with maximum clarity and emotion, but really quickly: «{text}»"
    
    assistant: str = "Audio output generated. The transcript of the audio is provided below."
    
    frames: str = (
        "Divide the following text into {count_scenes} iconic and striking scenes. "
        "Each frame should have a minimalist style with vivid comic-style visuals. "
        "For each scene, create a brief description (up to 50 words) that conveys the atmosphere, visual details, and mood.\n\n"
        "Text: {novella_text}\n"
        "Add a General description of the environment as the fifth scene for creating a drawing, up to 100 words long."
    )
    
    search: str = (
        "Generate {count_scenes} image search queries for a novella illustration. Each query must include:\n"
        "1. Protagonist's name\n2. Specific action\n3. Environment details\n4. Atmospheric conditions\n"
        "Format: [Name] [action verb] in/on [location] with [lighting/weather]. Example: 'Anna running through misty forest under moonlight'\n\n"
        "Novella text:\n{novella_text}"
    )
    
    novella: str = (
        "Create a mini-novel (up to 200 words) in the style of Sin City, where dark noir "
        "and striking visual contrasts combine with top-notch meme quotes. "
        "Let the story unfold on shadowy streets, where every dialogue is a burst of biting sarcasm "
        "or a palette of irony, reflecting the reality we live in. "
        "The characters, composed of cold-blooded resolve and daring courage, speak in the language of zoomers and alphas, "
        "where memes are a means of communication and everything around is a game of manipulation. "
        "Add unexpected twists and sharp phrases so that every line makes you think: "
        "\"Oh, this isn't trash and isn't suffocating! Like and subscribe, damn it!\"."
    )

# Initialize prompt templates
PROMPTS = PromptTemplates()

# System constants - reference the dataclass fields for clarity
SYSTEM_PROMPT: Final[str] = PROMPTS.system
USER_PROMPT: Final[str] = PROMPTS.user
ASSISTANT_MESSAGE: Final[str] = PROMPTS.assistant
FRAMES_PROMPT_TEMPLATE: Final[str] = PROMPTS.frames
SEARCH_USER_PROMPT: Final[str] = PROMPTS.search
NOVELLA_PROMPT: Final[str] = PROMPTS.novella

# ============================
# Scene Generation Configuration
# ============================

# Number of scenes to generate
NUMBER_OF_THE_SCENES: Final[int] = 6

# UI elements configuration
HORIZONTAL_SIZE: Final[int] = 256
CHUNK_SIZE: Final[int] = 25
FONTSIZE: Final[int] = 20

# ============================
# Function Definitions for LLM
# ============================

# Function definition for search query generation
SEARCH_QUERY_FUNCTION: Final[List[Dict]] = [{
    "type": "function",
    "function": {
        "name": "generate_search_queries",
        "description": "Generate image search queries",
        "parameters": {
            "type": "object",
            "properties": {
                "queries": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "List of search queries for finding images"
                }
            },
            "required": ["queries"]
        }
    }
}]

# ============================
# Testing Configuration
# ============================

# Testing flags
TEST_AUDIO: Final[bool] = True  # Skip audio generation if voice.mp3 exists
TEST_SCENES: Final[bool] = True  # Skip images generation if exist

# ============================
# Logger Configuration
# ============================

# Configure application logger
logger = logging.getLogger(__name__)
