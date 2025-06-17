"""
Client for Audio Service API.

This module provides a client class for communicating with the audio microservice.
"""

import requests
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path
import io

logger = logging.getLogger(__name__)


class AudioServiceClient:
    """Client for communicating with the audio microservice."""
    
    def __init__(self, base_url: str = "http://localhost:8003"):
        """
        Initialize the audio service client.
        
        Args:
            base_url: Base URL of the audio service
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
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
            logger.error(f"Health check failed: {e}")
            return False
    
    def generate_audio_file(self, 
                           text: str, 
                           language: str = "ru",
                           voice: Optional[str] = None,
                           format: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate audio file using the audio service.
        
        Args:
            text: Text to convert to speech
            language: Language of the text (en or ru)
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            format: Audio format (mp3, opus, aac, flac, wav, pcm)
            
        Returns:
            Dict containing generation result metadata
            
        Raises:
            requests.RequestException: If the API call fails
        """
        payload = {
            "text": text,
            "language": language
        }
        
        if voice:
            payload["voice"] = voice
        if format:
            payload["format"] = format
            
        try:
            response = self.session.post(
                f"{self.base_url}/generate",
                json=payload,
                timeout=60  # TTS can take time for long texts
            )
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Audio generation request failed: {e}")
            raise
    
    def generate_audio_stream(self, 
                             text: str, 
                             output_path: Union[str, Path],
                             language: str = "ru",
                             voice: Optional[str] = None,
                             format: Optional[str] = None) -> bool:
        """
        Generate audio and stream it directly to a file.
        
        Args:
            text: Text to convert to speech
            output_path: Path where to save the audio file
            language: Language of the text (en or ru)
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            format: Audio format (mp3, opus, aac, flac, wav, pcm)
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            requests.RequestException: If the API call fails
        """
        payload = {
            "text": text,
            "language": language
        }
        
        if voice:
            payload["voice"] = voice
        if format:
            payload["format"] = format
            
        try:
            response = self.session.post(
                f"{self.base_url}/generate-stream",
                json=payload,
                timeout=60,  # TTS can take time for long texts
                stream=True
            )
            response.raise_for_status()
            
            # Convert to Path object if needed
            if isinstance(output_path, str):
                output_path = Path(output_path)
                
            # Ensure directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save streamed content to file
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Audio saved to {output_path}")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Audio generation stream request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Error saving audio file: {e}")
            return False
    
    def generate_audio_bytes(self, 
                            text: str, 
                            language: str = "ru",
                            voice: Optional[str] = None,
                            format: Optional[str] = None) -> bytes:
        """
        Generate audio and return raw bytes.
        
        Args:
            text: Text to convert to speech
            language: Language of the text (en or ru)
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            format: Audio format (mp3, opus, aac, flac, wav, pcm)
            
        Returns:
            bytes: Raw audio data
            
        Raises:
            requests.RequestException: If the API call fails
        """
        payload = {
            "text": text,
            "language": language
        }
        
        if voice:
            payload["voice"] = voice
        if format:
            payload["format"] = format
            
        try:
            response = self.session.post(
                f"{self.base_url}/generate-stream",
                json=payload,
                timeout=60  # TTS can take time for long texts
            )
            response.raise_for_status()
            
            return response.content
            
        except requests.RequestException as e:
            logger.error(f"Audio generation bytes request failed: {e}")
            raise
