from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import StreamingResponse
import io
import logging
from typing import Dict, Any
from service import AudioService, AudioServiceError, ConfigurationError, GenerationError
from models.requests import (
    AudioGenerationRequest, 
    AudioGenerationResponse, 
    HealthResponse
)
from config import SERVICE_PORT, SERVICE_HOST

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Audio Service",
    description="Microservice for text-to-speech audio generation using OpenAI API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize audio service
try:
    audio_service = AudioService()
    logger.info("Audio service initialized successfully")
except ConfigurationError as e:
    logger.error(f"Failed to initialize audio service: {e}")
    audio_service = None


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint that returns service status."""
    return HealthResponse(
        status="healthy" if audio_service else "unhealthy",
        service="audio-service", 
        version="1.0.0"
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    if not audio_service:
        raise HTTPException(
            status_code=503, 
            detail="Audio service is not properly configured"
        )
    
    return HealthResponse(
        status="healthy",
        service="audio-service",
        version="1.0.0"
    )


@app.post("/generate", response_model=AudioGenerationResponse)
async def generate_audio_file(request: AudioGenerationRequest):
    """
    Generate audio from text and return metadata.
    The audio file will be saved in the default output directory.
    """
    if not audio_service:
        raise HTTPException(
            status_code=503,
            detail="Audio service is not properly configured"
        )
    
    # Check if mock mode is enabled
    if request.mock:
        logger.info("Mock mode enabled - returning simulated audio generation response")
        # Return mock response with realistic values
        mock_text_length = len(request.text)
        mock_duration = max(1.0, mock_text_length * 0.1)  # Rough estimate: 0.1 sec per character
        mock_file_size = max(10.0, mock_duration * 8.0)   # Rough estimate: 8KB per second
        
        return AudioGenerationResponse(
            success=True,
            message=f"Mock audio generated for {mock_text_length} characters using {request.voice or 'default'} voice",
            file_size_kb=round(mock_file_size, 2),
            duration_seconds=round(mock_duration, 2)
        )

    try:# Create a temporary output path
        from pathlib import Path
        from config import DEFAULT_OUTPUT_DIR
        
        output_dir = Path(DEFAULT_OUTPUT_DIR) / "voice"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate a filename based on text hash for uniqueness
        import hashlib
        text_hash = hashlib.md5(request.text.encode()).hexdigest()[:8]
        output_path = output_dir / f"audio_{text_hash}.mp3"
        
        # Update audio service configuration if voice/format specified
        audio_config = {}
        if request.voice:
            audio_config["voice"] = request.voice.value
        if request.format:
            audio_config["format"] = request.format.value
            
        # Use custom config if provided
        if audio_config:
            service = AudioService(audio_config=audio_config)
        else:
            service = audio_service
        
        # Generate audio
        result = service.generate_audio(
            text=request.text,
            output_path=output_path,
            language=request.language.value
        )
        
        if result.success:
            return AudioGenerationResponse(
                success=True,
                message=result.message or "Audio generated successfully",
                file_size_kb=result.file_size_kb,
                duration_seconds=result.duration_seconds
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=result.message or "Audio generation failed"
            )
            
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except GenerationError as e:
        logger.error(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/generate-stream")
async def generate_audio_stream(request: AudioGenerationRequest):
    """
    Generate audio from text and return it as a streaming response.
    This endpoint returns the audio file directly without saving it.
    """
    if not audio_service:
        raise HTTPException(
            status_code=503,
            detail="Audio service is not properly configured"
        )
    
    # Check if mock mode is enabled
    if request.mock:
        logger.info("Mock mode enabled - returning simulated audio stream")
        # Create a small mock audio content (silence)
        mock_audio_data = b'\x00' * 1024  # Simple mock audio data
        
        # Determine content type based on format
        format_value = request.format.value if request.format else "mp3"
        content_type = f"audio/{format_value}"
        
        return StreamingResponse(
            io.BytesIO(mock_audio_data),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename=mock_audio.{format_value}",
                "X-Mock-Mode": "true"
            }
        )
    
    try:
        # Update audio service configuration if voice/format specified
        audio_config = {}
        if request.voice:
            audio_config["voice"] = request.voice.value
        if request.format:
            audio_config["format"] = request.format.value
            
        # Use custom config if provided
        if audio_config:
            service = AudioService(audio_config=audio_config)
        else:
            service = audio_service
        
        # Generate audio in memory
        audio_data = service.generate_audio_in_memory(
            text=request.text,
            language=request.language.value
        )
        
        # Determine content type based on format
        format_value = request.format.value if request.format else "mp3"
        content_type_map = {
            "mp3": "audio/mpeg",
            "opus": "audio/opus",
            "aac": "audio/aac", 
            "flac": "audio/flac",
            "wav": "audio/wav",
            "pcm": "audio/pcm"
        }
        content_type = content_type_map.get(format_value, "audio/mpeg")
        
        # Create streaming response
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename=audio.{format_value}",
                "Content-Length": str(len(audio_data))
            }
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except GenerationError as e:
        logger.error(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=SERVICE_HOST,
        port=SERVICE_PORT,
        reload=True,
        log_level="info"
    )
