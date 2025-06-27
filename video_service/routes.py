"""
Video Service Routes - API endpoints for video generation operations.
"""

import logging
from fastapi import APIRouter, HTTPException
from models import VideoGenerationRequest, VideoGenerationResponse, HealthResponse
from video_generator import VideoService

logger = logging.getLogger(__name__)

router = APIRouter()
video_service = VideoService()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for service monitoring.
    
    Returns:
        HealthResponse: Service health status information
    """
    return HealthResponse(
        status="healthy",
        service="video-service",
        version="1.0.0"
    )

@router.post("/generateVideo", response_model=VideoGenerationResponse)
async def generate_video(request: VideoGenerationRequest):
    """
    Generate video from audio and images.
    
    Args:
        request: Video generation request containing audio, images and parameters
        
    Returns:
        VideoGenerationResponse: Generated video response with metadata
        
    Raises:
        HTTPException: If video generation fails
    """
    try:
        logger.info(
            f"Generating video with {len(request.image_paths)} images, "
            f"audio: {request.audio_path}"
        )
        
        result = await video_service.generate_video_async(
            audio_path=request.audio_path,
            image_paths=request.image_paths,
            fps=request.fps,
            resolution=request.resolution or (1920, 1080),
            slide_duration=request.slide_duration,
            transition_duration=request.transition_duration,
            enable_ken_burns=request.enable_ken_burns,
            zoom_factor=request.zoom_factor,
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["message"])
        
        return VideoGenerationResponse(
            success=result["success"],
            message=result["message"],
            video_url=result.get("video_url"),
            duration=result.get("duration"),
            file_size=result.get("file_size"),
            resolution=result.get("resolution"),
        )
        
    except Exception as e:
        logger.error(f"Video generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
