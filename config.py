# config.py

import os
from dotenv import load_dotenv

load_dotenv()

DEEPAI_API_KEY = os.getenv("DEEPAI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# DEFAULT_IMAGE_SIZE = "1024x1024"
DEFAULT_IMAGE_SIZE = "256x256"
DEFAULT_OUTPUT_DIR = os.getenv("DEFAULT_OUTPUT_DIR", "./output")

DEFAULT_IMAGES_OUTPUT_DIR = os.path.join(DEFAULT_OUTPUT_DIR, "images")
DEFAULT_VIDEO_OUTPUT_DIR = os.path.join(DEFAULT_OUTPUT_DIR, "video")
DEFAULT_VOICE_OUTPUT_DIR = os.path.join(DEFAULT_OUTPUT_DIR, "voice")
DEFAULT_TEXT_OUTPUT_DIR = os.path.join(DEFAULT_OUTPUT_DIR, "text")

VOICE_FILE_PATH = os.path.join(DEFAULT_VOICE_OUTPUT_DIR, "voice.mp3")
VIDEO_FILE_PATH = os.path.join(DEFAULT_VIDEO_OUTPUT_DIR, "video.mp4")

# DALLE_MODEL = "dall-e-3"
DALLE_MODEL = "dall-e-2"

# Имя модели, используемой для генерации аудио
OPENAI_MODEL = "gpt-4o-audio-preview"

# Настройки для аудио: голос и формат
AUDIO_CONFIG = {
    "voice": "nova",
    "format": "mp3"
}

# Системное сообщение для установки стиля аудио (настраиваемый шаблон)
SYSTEM_PROMPT = (
    "You are a highly skilled audio assistant capable of transforming text into vivid, emotionally charged audio. "
    "Maintain a voice pitch between 180–230 Hz and a dynamic range that spans from a soft whisper to powerful delivery, "
    "allowing for expressive emotional bursts. "
    "Adopt a resonant tone with a slight huskiness and sarcastic nuances; minimal jitter and shimmer ensure sound stability. "
    "Speak with clear diction, incorporating expressive intonation shifts and pauses that convey confidence and playful mockery. "
    "Instantly adjust your tone from mocking irony to deep expressiveness, reflecting a rich inner world and bold character. "
    "Speak with a clear Russian accent."
)

USER_PROMPT = "Please narrate the following text with maximum clarity and emotion, but really quickly: «{text}»"

# Сообщение подтверждения (вынесено для возможной интернационализации)
ASSISTANT_MESSAGE = "Audio output generated. The transcript of the audio is provided below."

# Testing features
TEST_AUDIO = True  # Skip audio generation if voice.mp3 exists
TEST_IMAGES = True  # Skip images generation if exist