"""
Client for communicating with the video service.
"""

import requests
import logging
from typing import Optional, Dict, Any
from config import VIDEO_SERVICE_URL

logger = logging.getLogger(__name__)

class VideoClient:
    """Client for video service API calls."""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize video client.
        
        Args:
            base_url: Base URL for video service. If None, uses config default.
        """
        self.base_url = base_url or VIDEO_SERVICE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        logger.info(f"VideoClient initialized with base URL: {self.base_url}")
    
    def health_check(self) -> bool:
        """
        Check if video service is healthy.
        
        Returns:
            bool: True if service is healthy, False otherwise
        """
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Video service health check failed: {str(e)}")
            return False
    
    def generate_video(self, images_folder: str, audio_file: str, 
                      settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate video from images and audio.
        
        Args:
            images_folder: Path to folder containing images
            audio_file: Path to audio file
            settings: Optional video generation settings
              Returns:
            Dict with generation result
        """
        try:
            payload: Dict[str, Any] = {
                "images_folder": images_folder,
                "audio_file": audio_file
            }
            
            if settings:
                # Ensure settings is properly serializable
                payload["settings"] = settings
            
            logger.info(f"Requesting video generation from {images_folder} with audio {audio_file}")
            
            response = self.session.post(
                f"{self.base_url}/generate",
                json=payload,
                timeout=300  # 5 minutes timeout for video generation
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Video generation successful: {result.get('video_path', 'N/A')}")
                return result
            else:
                error_msg = f"Video generation failed with status {response.status_code}: {response.text}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "message": error_msg
                }
                
        except requests.exceptions.Timeout:
            error_msg = "Video generation timed out"
            logger.error(error_msg)
            return {
                "success": False,
                "message": error_msg
            }
        except Exception as e:
            error_msg = f"Error calling video service: {str(e)}"
            logger.exception(error_msg)
            return {
                "success": False,
                "message": error_msg
            }
    
    def download_video(self, filename: str, save_path: str) -> bool:
        """
        Download video file from video service.
        
        Args:
            filename: Name of video file to download
            save_path: Local path to save the file
            
        Returns:
            bool: True if download successful, False otherwise
        """
        try:
            logger.info(f"Downloading video {filename} to {save_path}")
            
            response = self.session.get(
                f"{self.base_url}/download/{filename}",
                stream=True,
                timeout=60
            )
            
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info(f"Video downloaded successfully to {save_path}")
                return True
            else:
                logger.error(f"Failed to download video: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.exception(f"Error downloading video: {str(e)}")
            return False
