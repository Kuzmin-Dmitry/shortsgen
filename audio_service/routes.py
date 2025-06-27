"""
Audio Service Routes - API endpoints for text-to-speech operations.
"""

import logging
from fastapi import APIRouter, HTTPException
from models import AudioGenerationRequest, AudioGenerationResponse, HealthResponse
from tts_service import TTSService

logger = logging.getLogger(__name__)

router = APIRouter()
tts_service = TTSService()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for service monitoring.
    
    Returns:
        HealthResponse: Service health status information
    """
    return HealthResponse(
        status="healthy",
        service="audio-service",
        version="2.0.0"
    )

@router.post("/generateAudio", response_model=AudioGenerationResponse)
async def generate_audio(request: AudioGenerationRequest):
    """
    Generate audio from text using text-to-speech.
    
    Args:
        request: Audio generation request containing text and parameters
        
    Returns:
        AudioGenerationResponse: Generated audio response with metadata
        
    Raises:
        HTTPException: If audio generation fails
    """
    try:
        logger.info(f"Generating audio for text length: {len(request.text)} chars")
        
        result = await tts_service.generate_audio_async(
            text=request.text,
            voice=request.voice,
            speed=request.speed,
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["message"])
        
        return AudioGenerationResponse(
            success=result["success"],
            message=result["message"],
            audio_url=result.get("audio_url"),
            file_size=result.get("file_size"),
        )
        
    except Exception as e:
        logger.error(f"Audio generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
