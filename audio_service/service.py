import os
import base64
from typing import Dict, Optional, Any, Union, Literal
from dataclasses import dataclass
from pathlib import Path

from openai import OpenAI
import logging

from config import (
    OPENAI_API_KEY, 
    TTS_MODEL, 
    AUDIO_CONFIG, 
    TEST_AUDIO
)

logger = logging.getLogger(__name__)

@dataclass
class AudioGenerationResult:
    """Result of an audio generation operation with detailed metadata."""
    success: bool
    file_path: Optional[Path] = None
    file_size_kb: Optional[float] = None
    duration_seconds: Optional[float] = None
    message: Optional[str] = None
    error: Optional[Exception] = None


class AudioServiceError(Exception):
    """Base exception for all audio service related errors."""
    pass


class ConfigurationError(AudioServiceError):
    """Raised when there's an issue with the audio service configuration."""
    pass


class GenerationError(AudioServiceError):
    """Raised when audio generation fails."""
    pass


class AudioService:
    """
    Service for generating audio content from text.
    
    This service manages text-to-speech operations with support for:
    - OpenAI's TTS models
    - Test mode for development
    - Configurable voice parameters
    - Detailed operation logging
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, 
                 audio_config: Optional[Dict[str, Any]] = None, test_mode: Optional[bool] = None):
        """
        Initialize the AudioService with configuration parameters.
        
        Args:
            api_key: OpenAI API key, defaults to config.OPENAI_API_KEY
            model: Model to use for generation, defaults to config.TTS_MODEL
            audio_config: Voice configuration parameters, defaults to config.AUDIO_CONFIG
            test_mode: Whether to operate in test mode, defaults to config.TEST_AUDIO
            
        Raises:
            ConfigurationError: If required configuration is missing or invalid
        """
        # Use provided values or fall back to configuration defaults
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model or TTS_MODEL
        self.audio_config = audio_config or AUDIO_CONFIG
        self.test_mode = test_mode if test_mode is not None else TEST_AUDIO
        
        # Validate configuration
        if not self.api_key:
            raise ConfigurationError("OpenAI API key is required")
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key)
        
        logger.info(f"AudioService initialized with model={self.model}, test_mode={self.test_mode}")
        
    def validate_input(self, text: str, output_path: Union[str, Path]) -> None:
        """
        Validate input parameters for audio generation.
        
        Args:
            text: The text to convert to speech
            output_path: The file path where the audio will be saved
            
        Raises:
            ValueError: If any input parameters are invalid
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        if not output_path:
            raise ValueError("Output path is required")
            
        # Convert string path to Path object if needed
        if isinstance(output_path, str):
            output_dir = os.path.dirname(output_path)
        else:
            output_dir = output_path.parent
            
        # Check if output directory exists
        if output_dir and not os.path.exists(output_dir):
            raise ValueError(f"Output directory does not exist: {output_dir}")

    def generate_audio(self, 
                      text: str, 
                      output_path: Union[str, Path], 
                      language: Literal['en', 'ru'] = 'ru') -> AudioGenerationResult:
        """
        Generate audio from text and save it to the specified path.
        
        Args:
            text: The text to convert to speech
            output_path: The file path where the audio will be saved
            language: The language of the text, either 'en' or 'ru' (currently not used by OpenAI TTS)
            
        Returns:
            AudioGenerationResult: Result object containing success status and metadata
            
        Raises:
            GenerationError: If audio generation fails
            ValueError: If input parameters are invalid
        """
        # Convert to Path object for consistency
        if isinstance(output_path, str):
            output_path = Path(output_path)
            
        try:
            # Validate inputs
            self.validate_input(text, output_path)
            
            # Log input parameters
            text_preview = text[:30] + "..." if len(text) > 30 else text
            logger.info(f"Generating audio to {output_path}, language={language}")
            logger.debug(f"Text to synthesize: {text_preview}")
            
            # Check for test mode
            if self.test_mode and output_path.exists():
                file_size = output_path.stat().st_size / 1024  # Size in KB
                logger.info(f"Using existing audio: {output_path} [TEST_MODE] ({file_size:.2f} KB)")
                return AudioGenerationResult(
                    success=True,
                    file_path=output_path,
                    file_size_kb=file_size,
                    message="Using existing audio file (test mode)"
                )
                
            # Generate new audio using TTS endpoint
            logger.info(f"Generating audio track using TTS model: {self.model}")
            
            # Create TTS API request
            audio_data = self._call_openai_tts_api(text)
            
            # Ensure the output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save the file
            with open(output_path, "wb") as f:
                f.write(audio_data)
            
            # Get file metadata
            file_size = output_path.stat().st_size / 1024  # Size in KB
            logger.info(f"Audio file saved: {output_path} ({file_size:.2f} KB)")
            
            # Return success result with metadata
            return AudioGenerationResult(
                success=True,
                file_path=output_path,
                file_size_kb=file_size,
                message="Audio generated successfully"
            )
            
        except ValueError as e:
            # Re-raise validation errors
            logger.error(f"Input validation error: {str(e)}")
            raise
            
        except Exception as e:
            # Capture all other errors
            error_msg = f"Audio generation error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            return AudioGenerationResult(
                success=False,
                message=error_msg,
                error=e
            )
    
    def _call_openai_tts_api(self, text: str) -> bytes:
        """
        Make the API call to OpenAI TTS for audio generation.
        
        Args:
            text: The text to convert to speech
            
        Returns:
            bytes: The raw audio data
            
        Raises:
            GenerationError: If the API call fails
        """
        try:
            # Ensure format is valid for OpenAI TTS API
            format_value = self.audio_config.get("format", "mp3")
            valid_formats = ["mp3", "opus", "aac", "flac", "wav", "pcm"]
            if format_value not in valid_formats:
                format_value = "mp3"  # Default to mp3 if invalid format
                
            response = self.client.audio.speech.create(
                model=self.model,
                voice=self.audio_config.get("voice", "alloy"),  # Default to "alloy" if not specified
                input=text,
                response_format=format_value  # type: ignore
            )
            return response.content
        except Exception as e:
            # Wrap API errors in our custom exception
            raise GenerationError(f"OpenAI TTS API call failed: {str(e)}") from e

    def generate_audio_in_memory(self, text: str, language: Literal['en', 'ru'] = 'ru') -> bytes:
        """
        Generate audio from text and return raw audio data without saving to file.
        
        Args:
            text: The text to convert to speech
            language: The language of the text, either 'en' or 'ru'
            
        Returns:
            bytes: The raw audio data
            
        Raises:
            GenerationError: If audio generation fails
            ValueError: If input parameters are invalid
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
            
        try:
            # Log input parameters
            text_preview = text[:30] + "..." if len(text) > 30 else text
            logger.info(f"Generating audio in memory, language={language}")
            logger.debug(f"Text to synthesize: {text_preview}")
            
            # Generate audio using TTS endpoint
            logger.info(f"Generating audio track using TTS model: {self.model}")
            
            # Create TTS API request
            audio_data = self._call_openai_tts_api(text)
            
            logger.info(f"Audio generated successfully ({len(audio_data)} bytes)")
            
            return audio_data
            
        except ValueError as e:
            # Re-raise validation errors
            logger.error(f"Input validation error: {str(e)}")
            raise
            
        except Exception as e:
            # Capture all other errors
            error_msg = f"Audio generation error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise GenerationError(error_msg) from e
