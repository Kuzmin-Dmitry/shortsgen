"""
Media Processor - Specialized service for handling audio and video generation.
"""

import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from audio_client import AudioClient
from video_client import VideoClient
from image_service import ImageService
from workflow_state import StageResult, StageStatus
from resilience import with_retry, RetryConfig
from config import VOICE_FILE_PATH, VIDEO_FILE_PATH, DIRS

logger = logging.getLogger(__name__)

class MediaProcessor:
    """Service responsible for generating and processing media content."""
    
    def __init__(self):
        self.audio_client = AudioClient()
        self.video_client = VideoClient()
        self.image_service = ImageService()
        self.retry_config = RetryConfig(max_attempts=3, base_delay=2.0)
        logger.info("MediaProcessor initialized")
    
    @with_retry(RetryConfig())
    def generate_scene_images(self, scene_descriptions: List[str]) -> StageResult:
        """Generate AI images for scene descriptions."""
        stage_name = "ai_image_generation"
        started_at = datetime.now()
        
        try:
            logger.info(f"Generating AI images for {len(scene_descriptions)} scenes")
            
            image_paths = []
            for i, description in enumerate(scene_descriptions, 1):
                logger.debug(f"Generating image {i} for: {description[:50]}...")
                
                image_path = self.image_service.generate_image(
                    prompt=description,
                    size="1024x1024",
                    filename=f"image_{i}.jpg"
                )
                
                if image_path and Path(image_path).exists():
                    image_paths.append(image_path)
                    logger.debug(f"Generated image {i}: {image_path}")
                else:
                    logger.warning(f"Failed to generate image {i}")
            
            if not image_paths:
                raise ValueError("No images were generated successfully")
            
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            
            logger.info(f"Generated {len(image_paths)} AI images in {duration:.2f}s")
            
            return StageResult(
                stage_name=stage_name,
                status=StageStatus.COMPLETED,
                data=image_paths,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration
            )
            
        except Exception as e:
            logger.error(f"Failed to generate AI images: {e}")
            return StageResult(
                stage_name=stage_name,
                status=StageStatus.FAILED,
                error_message=str(e),
                started_at=started_at,
                completed_at=datetime.now()
            )
    
    @with_retry(RetryConfig())
    def find_web_images(self, search_queries: List[str]) -> StageResult:
        """Find and download images from web search."""
        stage_name = "web_image_search"
        started_at = datetime.now()
        
        try:
            logger.info(f"Searching web images for {len(search_queries)} queries")
            
            image_paths = []
            for i, query in enumerate(search_queries, 1):
                logger.debug(f"Searching images for query {i}: {query}")
                
                # Use image service to search and download
                search_results = self.image_service.search_images(
                    query=query,
                    count=1,
                    filename=f"image_{i}.jpg"
                )
                
                if search_results:
                    image_paths.extend(search_results)
                    logger.debug(f"Found {len(search_results)} images for query {i}")
                else:
                    logger.warning(f"No images found for query {i}: {query}")
            
            if not image_paths:
                raise ValueError("No images were found from web search")
            
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            
            logger.info(f"Found {len(image_paths)} web images in {duration:.2f}s")
            
            return StageResult(
                stage_name=stage_name,
                status=StageStatus.COMPLETED,
                data=image_paths,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration
            )
            
        except Exception as e:
            logger.error(f"Failed to find web images: {e}")
            return StageResult(
                stage_name=stage_name,
                status=StageStatus.FAILED,
                error_message=str(e),
                started_at=started_at,
                completed_at=datetime.now()
            )
    
    @with_retry(RetryConfig())
    def generate_audio(self, narrative_text: str) -> StageResult:
        """Generate audio narration from text."""
        stage_name = "audio_generation"
        started_at = datetime.now()
        
        try:
            logger.info("Generating audio narration")
            
            # Ensure voice directory exists
            voice_dir = Path(DIRS.voice)
            voice_dir.mkdir(parents=True, exist_ok=True)
            
            audio_path = self.audio_client.generate_audio(
                text=narrative_text,
                filename=VOICE_FILE_PATH
            )
            
            if not audio_path or not Path(audio_path).exists():
                raise ValueError("Audio generation failed - no file created")
            
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            
            logger.info(f"Generated audio in {duration:.2f}s: {audio_path}")
            
            return StageResult(
                stage_name=stage_name,
                status=StageStatus.COMPLETED,
                data=audio_path,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration
            )
            
        except Exception as e:
            logger.error(f"Failed to generate audio: {e}")
            return StageResult(
                stage_name=stage_name,
                status=StageStatus.FAILED,
                error_message=str(e),
                started_at=started_at,
                completed_at=datetime.now()
            )
    
    @with_retry(RetryConfig())
    def compose_video(self, image_paths: List[str], audio_path: str) -> StageResult:
        """Compose final video from images and audio."""
        stage_name = "video_composition"
        started_at = datetime.now()
        
        try:
            logger.info(f"Composing video from {len(image_paths)} images and audio")
            
            # Ensure video directory exists
            video_dir = Path(DIRS.video)
            video_dir.mkdir(parents=True, exist_ok=True)
            
            # Validate inputs
            if not image_paths:
                raise ValueError("No images provided for video composition")
            
            if not audio_path or not Path(audio_path).exists():
                raise ValueError(f"Audio file not found: {audio_path}")
            
            # Verify all image files exist
            valid_images = []
            for img_path in image_paths:
                if Path(img_path).exists():
                    valid_images.append(img_path)
                else:
                    logger.warning(f"Image file not found: {img_path}")
            
            if not valid_images:
                raise ValueError("No valid image files found")
            
            video_path = self.video_client.create_video(
                image_paths=valid_images,
                audio_path=audio_path,
                output_path=VIDEO_FILE_PATH
            )
            
            if not video_path or not Path(video_path).exists():
                raise ValueError("Video composition failed - no file created")
            
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            
            logger.info(f"Composed video in {duration:.2f}s: {video_path}")
            
            return StageResult(
                stage_name=stage_name,
                status=StageStatus.COMPLETED,
                data=video_path,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration
            )
            
        except Exception as e:
            logger.error(f"Failed to compose video: {e}")
            return StageResult(
                stage_name=stage_name,
                status=StageStatus.FAILED,
                error_message=str(e),
                started_at=started_at,
                completed_at=datetime.now()
            )
