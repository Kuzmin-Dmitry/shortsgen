from fastapi import FastAPI, HTTPException, status, File, UploadFile, Form
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, ValidationError
from typing import List, Optional, Dict, Any
import os
import logging
import tempfile
import shutil
from pathlib import Path

from video_editor import VideoEditor, VideoSettings as VEVideoSettings, TransitionType, TextPosition
from config import VIDEO_FILE_PATH, DIRS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('video_service.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Video Service API", 
    description="Microservice for video generation and editing",
    version="1.0.0"
)

# Request/Response models
class VideoGenerationRequest(BaseModel):
    """Request model for video generation from images and audio"""
    images_folder: str
    audio_file: str
    settings: Optional[Dict[str, Any]] = None
    mock: Optional[bool] = False

class VideoSettings(BaseModel):
    """Video generation settings"""
    fps: int = 24
    width: int = 1024
    height: int = 1024
    text_fontsize: int = 72
    chunk_size: int = 512
    fade_duration: float = 0.5
    text_color: str = "white"
    bg_color: str = "black"
    font: str = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    text_position: str = "bottom"
    transition_type: str = "fade"

class VideoGenerationResponse(BaseModel):
    """Response model for video generation"""
    success: bool
    message: str
    video_path: Optional[str] = None
    duration: Optional[float] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="video-service", 
        version="1.0.0"
    )

@app.post("/generate", response_model=VideoGenerationResponse)
async def generate_video(request: VideoGenerationRequest):
    """
    Generate video from images and audio
    
    Args:
        request: Video generation request with images folder, audio file and settings
        
    Returns:
        VideoGenerationResponse with success status and video path
    """
    try:
        logger.info(f"Received video generation request for images: {request.images_folder}, audio: {request.audio_file}")
        
        # Check if mock mode is enabled
        if request.mock:
            logger.info("Mock mode enabled - returning simulated video generation response")
            
            # Calculate mock video duration based on typical values
            mock_duration = 15.0  # Default mock duration
            
            # Try to get actual audio duration if file exists for more realistic mock
            try:
                if os.path.exists(request.audio_file):
                    from moviepy.editor import AudioFileClip # type: ignore
                    with AudioFileClip(request.audio_file) as audio_clip:
                        mock_duration = audio_clip.duration
                else:
                    logger.info(f"Audio file not found for mock: {request.audio_file}, using default duration")
            except Exception as e:
                logger.warning(f"Could not get audio duration for mock: {e}")
            
            # Count images for more realistic mock response
            image_count = 0
            try:
                if os.path.exists(request.images_folder):
                    image_files = [f for f in os.listdir(request.images_folder) 
                                 if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
                    image_count = len(image_files)
            except Exception as e:
                logger.warning(f"Could not count images for mock: {e}")
                image_count = 6  # Default assumption
            
            return VideoGenerationResponse(
                success=True,
                message=f"Mock video generated from {image_count} images with {mock_duration:.1f}s duration",
                video_path="mock_video_output.mp4",
                duration=mock_duration
            )
        
        # Validate inputs
        if not os.path.exists(request.images_folder):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Images folder not found: {request.images_folder}"
            )
        
        if not os.path.exists(request.audio_file):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Audio file not found: {request.audio_file}"
            )
          # Create video settings from request
        video_settings = None
        if request.settings:
            try:
                settings_dict = request.settings.copy()
                # Convert string enums to appropriate types
                if 'text_position' in settings_dict:
                    settings_dict['text_position'] = TextPosition(settings_dict['text_position'])
                if 'transition_type' in settings_dict:
                    settings_dict['transition_type'] = TransitionType(settings_dict['transition_type'])
                    
                video_settings = VEVideoSettings(**settings_dict)
            except (ValidationError, ValueError) as e:
                logger.warning(f"Invalid settings provided, using defaults: {e}")
                video_settings = VEVideoSettings()
        else:
            video_settings = VEVideoSettings()
        
        # Initialize video editor
        video_editor = VideoEditor(video_settings)
        
        # Generate video
        success = video_editor.create_video_from_images_and_audio(
            image_folder=request.images_folder,
            audio_file=request.audio_file,
            output_file=VIDEO_FILE_PATH        )
        
        if success:
            # Get video duration for response
            try:
                from moviepy.editor import VideoFileClip # type: ignore
                with VideoFileClip(VIDEO_FILE_PATH) as clip:
                    duration = clip.duration
            except Exception as e:
                logger.warning(f"Could not get video duration: {e}")
                duration = None
                
            logger.info(f"Video generation completed successfully: {VIDEO_FILE_PATH}")
            return VideoGenerationResponse(
                success=True,
                message="Video generated successfully",
                video_path=VIDEO_FILE_PATH,
                duration=duration
            )
        else:
            logger.error("Video generation failed")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Video generation failed"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error generating video: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/download/{filename}")
async def download_video(filename: str):
    """
    Download generated video file
    
    Args:
        filename: Name of the video file to download
        
    Returns:
        FileResponse with the video file
    """
    try:
        video_path = os.path.join(DIRS.video, filename)
        
        if not os.path.exists(video_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Video file not found: {filename}"
            )
        
        return FileResponse(
            path=video_path,
            media_type="video/mp4",
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error downloading video: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/upload-images")
async def upload_images(files: List[UploadFile] = File(...)):
    """
    Upload multiple image files for video generation
    
    Args:
        files: List of image files to upload
        
    Returns:
        JSONResponse with upload status and folder path
    """
    try:
        # Create temporary directory for uploaded images
        temp_dir = tempfile.mkdtemp(prefix="video_images_")
        logger.info(f"Created temporary directory for images: {temp_dir}")
        
        uploaded_files = []
        for file in files:
            if file.content_type not in ["image/jpeg", "image/jpg", "image/png", "image/bmp", "image/gif"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid file type: {file.content_type}. Only image files are allowed."
                )
              # Save uploaded file
            if file.filename is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File must have a filename"
                )
            file_path = os.path.join(temp_dir, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            uploaded_files.append(file.filename)
            
        logger.info(f"Uploaded {len(uploaded_files)} images to {temp_dir}")
        
        return JSONResponse(content={
            "success": True,
            "message": f"Uploaded {len(uploaded_files)} images",
            "folder_path": temp_dir,
            "files": uploaded_files
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error uploading images: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8004, reload=False)
