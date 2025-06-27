"""
Text-to-Speech service implementation.
"""

import os
import hashlib
from typing import Dict, Any, Optional
from openai import OpenAI
from config import OPENAI_API_KEY, AUDIO_OUTPUT_DIR, DEFAULT_VOICE, DEFAULT_SPEED, logger


class TTSService:
    """Text-to-Speech service using OpenAI API."""
    
    def __init__(self):
        """Initialize TTS service."""
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required")
        
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self._ensure_output_dir()
    
    def _ensure_output_dir(self) -> None:
        """Ensure output directory exists."""
        os.makedirs(AUDIO_OUTPUT_DIR, exist_ok=True)
    
    def _generate_filename(self, text: str, voice: str, speed: float) -> str:
        """Generate unique filename based on parameters.
        
        Args:
            text: Input text
            voice: Voice name
            speed: Speech speed
            
        Returns:
            Unique filename
        """
        content_hash = hashlib.md5(
            f"{text}_{voice}_{speed}".encode()
        ).hexdigest()[:12]
        return f"audio_{content_hash}.mp3"
    
    async def generate_audio_async(
        self,
        text: str,
        voice: str = DEFAULT_VOICE,
        speed: float = DEFAULT_SPEED,
    ) -> Dict[str, Any]:
        """Generate audio asynchronously.
        
        Args:
            text: Text to convert
            voice: Voice to use
            speed: Speech speed
            
        Returns:
            Result dictionary
        """
        try:
            filename = self._generate_filename(text, voice, speed)
            filepath = os.path.join(AUDIO_OUTPUT_DIR, filename)
            
            # Check if file already exists
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                return {
                    "success": True,
                    "message": "Audio generated successfully (cached)",
                    "audio_url": f"/output/voice/{filename}",
                    "audio_path": filepath,
                    "file_size": file_size,
                    "filename": filename,
                }
            
            # Generate audio using OpenAI
            response = self.client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice=voice,
                input=text,
                speed=speed,
            )
            
            # Save audio file
            with open(filepath, "wb") as f:
                f.write(response.content)
            
            file_size = os.path.getsize(filepath)
            
            logger.info(f"Generated audio: {filename} ({file_size} bytes)")
            
            return {
                "success": True,
                "message": "Audio generated successfully",
                "audio_url": f"/output/voice/{filename}",
                "audio_path": filepath,
                "file_size": file_size,
                "filename": filename,
            }
            
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            return {
                "success": False,
                "message": f"Audio generation failed: {str(e)}",
            }
    
    def generate_audio(self, request) -> Any:
        """Synchronous wrapper for backward compatibility."""
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            self.generate_audio_async(
                text=request.text,
                voice=getattr(request, 'voice', DEFAULT_VOICE),
                speed=getattr(request, 'speed', DEFAULT_SPEED),
            )
        )
        
        # Convert to response object for compatibility
        from models import AudioGenerationResponse
        
        return AudioGenerationResponse(
            success=result["success"],
            message=result["message"],
            audio_url=result.get("audio_url"),
            file_size=result.get("file_size"),
        )


def get_tts_service() -> TTSService:
    """Get TTS service instance."""
    return TTSService()
