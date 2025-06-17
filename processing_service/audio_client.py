"""
Audio API Client - HTTP client for communicating with the Audio Service.

This module provides a simple HTTP client for making API calls to the
audio service microservice via REST API.
"""

import requests
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import os

logger = logging.getLogger(__name__)


class AudioClient:
    """
    HTTP client for communicating with the Audio Service API.
    
    This client makes HTTP requests to the audio service microservice
    and handles API communication errors.
    """
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the audio client.
        
        Args:
            base_url: Base URL of the audio service API
        """
        self.base_url = (base_url or os.getenv("AUDIO_SERVICE_URL", "http://audio-service:8003")).rstrip('/')
        self.session = requests.Session()
        logger.info(f"AudioClient initialized with base URL: {self.base_url}")
        
    def health_check(self) -> bool:
        """
        Check if the audio service is healthy.
        
        Returns:
            bool: True if service is healthy, False otherwise
        """
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Audio service health check failed: {e}")
            return False
    
    def generate_audio_stream(self, 
                             text: str, 
                             output_path: str,
                             language: str = "ru",
                             voice: Optional[str] = None,
                             timeout: int = 120) -> bool:
        """
        Generate audio file using the audio service API and save to file.
        
        Args:
            text: Text to convert to speech
            output_path: Path where to save the audio file
            language: Language code for the speech
            voice: Optional voice identifier
            timeout: Request timeout in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            payload = {
                "text": text,
                "language": language
            }
            
            if voice:
                payload["voice"] = voice
            
            logger.debug(f"Making audio generation request for {len(text)} characters")
            
            response = self.session.post(
                f"{self.base_url}/generate-stream",
                json=payload,
                stream=True,
                timeout=timeout
            )
            response.raise_for_status()
            
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save the streamed audio content
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Verify file was created and has content
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                file_size = os.path.getsize(output_path)
                logger.info(f"Audio file saved successfully: {output_path} ({file_size} bytes)")
                return True
            else:
                logger.error(f"Audio file was not created or is empty: {output_path}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Audio generation API request failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during audio generation: {e}")
            return False

    def generate_audio_file(self, 
                           text: str, 
                           language: str = "ru",
                           voice: Optional[str] = None,
                           format: Optional[str] = None,
                           timeout: int = 120) -> Dict[str, Any]:
        """
        Generate audio file using the audio service API and return file info.
        
        Args:
            text: Text to convert to speech
            language: Language code for the speech
            voice: Optional voice identifier
            format: Audio format (mp3, wav, etc.)
            timeout: Request timeout in seconds
            
        Returns:
            Dict containing success status and file information
        """
        try:
            payload = {
                "text": text,
                "language": language
            }
            
            if voice:
                payload["voice"] = voice
            if format:
                payload["format"] = format
            
            logger.debug(f"Making audio file generation request for {len(text)} characters")
            
            response = self.session.post(
                f"{self.base_url}/generate",
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Audio file generation completed: {result}")
            return result
                
        except requests.RequestException as e:
            logger.error(f"Audio generation API request failed: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error during audio generation: {e}")
            return {"success": False, "error": str(e)}
