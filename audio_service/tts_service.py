import os
import logging
from typing import Optional, Generator
from pathlib import Path
from openai import OpenAI

from config import (
    OPENAI_API_KEY,
    DEFAULT_TTS_MODEL,
    DEFAULT_VOICE,
    DEFAULT_TTS_SPEED,
    AUDIO_OUTPUT_DIR,
)
from models import (
    AudioGenerationRequest,
    AudioGenerationResponse,
    TTSVoice,
    AudioFormat,
)

logger = logging.getLogger(__name__)

class OpenAITTSService:
    """Service for OpenAI text-to-speech generation."""
    
    def __init__(self):
        """Initialize OpenAI client."""
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required")
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self._ensure_output_dir()
    
    def _ensure_output_dir(self) -> None:
        Path(AUDIO_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    # ---------- public API ----------

    def generate_audio(self, request: AudioGenerationRequest) -> AudioGenerationResponse:
        """Synchronously generate an audio file."""
        if request.mock:
            return self._mock_response(model=DEFAULT_TTS_MODEL)

        try:
            # Resolve parameters / fallbacks
            voice = (request.voice or TTSVoice.ALLOY).value
            audio_format = (request.format or AudioFormat.MP3).value
            speed = request.speed or DEFAULT_TTS_SPEED

            logger.debug(
                "Generating audio | model=%s voice=%s format=%s speed=%.2f pitch=%d style=%s",
                DEFAULT_TTS_MODEL,
                voice,
                audio_format,
                speed
            )

            # 🔥 Core API call
            response = self.client.audio.speech.create(
                model=DEFAULT_TTS_MODEL,
                voice=voice,
                input=request.text,
                response_format=audio_format,
                speed=speed
            )

            file_path = self._save_audio(response.content, audio_format, request.text)
            file_size_kb = os.path.getsize(file_path) / 1024

            return AudioGenerationResponse(
                success=True,
                message="Audio generated successfully",
                file_size_kb=file_size_kb,
                duration_seconds=self._estimate_duration(request.text, speed),
                model_used=DEFAULT_TTS_MODEL,
            )
        except Exception as exc:
            logger.exception("Audio generation failed: %s", exc)
            return AudioGenerationResponse(success=False, message="Audio generation failed", error=str(exc))

    # ---------- helpers ----------

    def _save_audio(self, data: bytes, ext: str, source_text: str) -> str:
        filename = f"audio_{hash(source_text)}.{ext}"
        file_path = os.path.join(AUDIO_OUTPUT_DIR, filename)
        with open(file_path, "wb") as f:
            f.write(data)
        logger.info("Saved audio file: %s", file_path)
        return file_path

    def _estimate_duration(self, text: str, speed: float) -> float:
        words = len(text.split())
        # базовая оценка исходя из 150 wpm, скорректированная по speed
        return (words / 150) * 60 / speed

    def _mock_response(self, model: str) -> AudioGenerationResponse:
        return AudioGenerationResponse(
            success=True,
            message="Mock audio generated successfully",
            file_size_kb=123.45,
            duration_seconds=15.0,
            model_used=model,
        )

# Singleton accessor remains unchanged
_service: Optional[OpenAITTSService] = None

def get_tts_service() -> OpenAITTSService:
    global _service
    if _service is None:
        _service = OpenAITTSService()
    return _service