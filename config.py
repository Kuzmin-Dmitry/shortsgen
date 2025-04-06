# config.py

import logging
import logging.config
import os
from dotenv import load_dotenv
from utils.logger import LoggerConfigurator

load_dotenv()

DEEPAI_API_KEY = os.getenv("DEEPAI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

DEFAULT_IMAGE_SIZE = "1024x1024"
# DEFAULT_IMAGE_SIZE = "256x256"
DEFAULT_OUTPUT_DIR = os.getenv("DEFAULT_OUTPUT_DIR", "./output")

DEFAULT_SCENES_OUTPUT_DIR = os.path.join(DEFAULT_OUTPUT_DIR, "scenes")
DEFAULT_VIDEO_OUTPUT_DIR = os.path.join(DEFAULT_OUTPUT_DIR, "video")
DEFAULT_VOICE_OUTPUT_DIR = os.path.join(DEFAULT_OUTPUT_DIR, "voice")
DEFAULT_TEXT_OUTPUT_DIR = os.path.join(DEFAULT_OUTPUT_DIR, "text")

VOICE_FILE_PATH = os.path.join(DEFAULT_VOICE_OUTPUT_DIR, "voice.mp3")
VIDEO_FILE_PATH = os.path.join(DEFAULT_VIDEO_OUTPUT_DIR, "video.mp4")

# DALLE_MODEL = "dall-e-3"
DALLE_MODEL = "dall-e-2"

# Name of the model used for audio generation
OPENAI_MODEL = "gpt-4o-mini-tts"
LOCAL_TEXT_TO_TEXT_MODEL = "gemma3:12b"
LOCAL = False  # Working with local models: "run ollama serve"

# Audio settings: voice and format
AUDIO_CONFIG = {
    "voice": "coral",
    "format": "mp3"
}

# Audio instructions for the new streaming API
AUDIO_INSTRUCTIONS = """
Affect: A gentle, curious narrator with a Russian accent, guiding a magical, child-friendly adventure.
Tone: Magical, warm, and inviting, creating a sense of wonder and excitement.
Pacing: Steady and measured, with slight pauses to emphasize magical moments.
Emotion: Wonder, curiosity, and a sense of adventure, with a lighthearted and positive vibe throughout.
Pronunciation: Clear and precise, with an emphasis on storytelling.
"""

# System message for setting audio style (customizable template)
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

# Confirmation message (externalized for possible internationalization)
ASSISTANT_MESSAGE = "Audio output generated. The transcript of the audio is provided below."

# Number of scenes to generate
NUMBER_OF_THE_SCENES = 6

# Template for frames prompt
FRAMES_PROMPT_TEMPLATE = (
    "Divide the following text into {count_scenes} iconic and striking scenes. "
    "Each frame should have a minimalist style with vivid comic-style visuals. "
    "For each scene, create a brief description (up to 50 words) that conveys the atmosphere, visual details, and mood.\n\n"
    "Text: {novella_text}\n"
    "Add a General description of the environment as the fifth scene for creating a drawing, up to 100 words long."
)

# Template for creating web requests for searching images in internet
SEARCH_REQUEST_TEMPLATE = (
    "Create a series of search queries for illustrating a novella divided into {count_scenes} parts.\n\n"
    "# TASK:\n"
    "Analyze the novella text, divide it into {count_scenes} logical parts, and create ONE search query for EACH part to find a suitable image.\n\n"
    "# STRICT OUTPUT FORMAT REQUIREMENTS:\n"
    "* The result MUST be presented ONLY in YAML format with a single key 'image_search_queries'\n"
    "* DO NOT add any explanations, comments, or additional text before or after the YAML\n"
    "* DO NOT use code markers (```) — output only clean YAML\n\n"
    "# SEARCH QUERY REQUIREMENTS:\n"
    "1. Length of EACH query: exactly 5-12 words\n"
    "2. EACH query MUST include the protagonist's name EXACTLY as mentioned in the text\n"
    "3. Queries should describe a SPECIFIC scene from the corresponding part of the text\n"
    "4. Include in EACH query:\n"
    "   - Main character (by name)\n"
    "   - Specific action\n"
    "   - Clear description of the setting\n"
    "   - Lighting and atmosphere\n"
    "5. Use vivid visual adjectives and popular keywords for image search engines\n"
    "6. Ensure visual consistency across all queries: uniform style, color palette, composition\n"
    "7. AVOID abstract concepts and vague wording\n"
    "8. Use phrases that are likely to find professional photographs or artistic images\n\n"
    "# EXAMPLE OF CORRECT OUTPUT:\n"
    "image_search_queries:\n"
    "  - \"Anna Karenina at winter station in dim lantern light\"\n"
    "  - \"Anna Karenina reading letter sunny morning luxurious living room\"\n\n"
    
    "Novella text:\n{novella_text}"
)

#
# Testing features
#
TEST_AUDIO = True  # Skip audio generation if voice.mp3 exists
TEST_SCENES = True  # Skip images generation if exist
#
# FOR UI:
#

NOVELLA_PROMPT = (
    "Create a mini-novel (up to 200 words) in the style of Sin City, where dark noir "
    "and striking visual contrasts combine with top-notch meme quotes. "
    "Let the story unfold on shadowy streets, where every dialogue is a burst of biting sarcasm "
    "or a palette of irony, reflecting the reality we live in. "
    "The characters, composed of cold-blooded resolve and daring courage, speak in the language of zoomers and alphas, "
    "where memes are a means of communication and everything around is a game of manipulation. "
    "Add unexpected twists and sharp phrases so that every line makes you think: "
    "\"Oh, this isn't trash and isn't suffocating! Like and subscribe, damn it!\"."
)

# For Text on a picture
HORIZONTAL_SIZE = 256

# Amount of words in a chunk
CHUNK_SIZE = 25

# Font size for text on a picture   
FONTSIZE = 20

# Configure logging
logger_configurator = LoggerConfigurator()
logger = logger_configurator.get_logger()
