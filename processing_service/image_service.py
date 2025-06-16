"""
Module for image generation and processing.

This module provides services for generating and acquiring images from various sources
including AI image generation models like DALL-E and web searches.
"""

import os
import requests
import re
import time
import logging
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Union, Any, Tuple, ClassVar
from openai import OpenAI
from duckduckgo_search import DDGS
from config import (
    OPENAI_API_KEY,
    GENERATED_IMAGE_SIZE,
    DIRS,
    DALLE_MODEL,
    TEST_SCENES
)

# Configure module logger
logger = logging.getLogger(__name__)

class ImageSize(Enum):
    """Standard image size configurations."""
    SMALL = "256x256"
    MEDIUM = "512x512"
    LARGE = "1024x1024"
    EXTRA_LARGE = "1792x1024"
    CUSTOM = "custom"

class ImageFormat(Enum):
    """Supported image file formats."""
    PNG = "png"
    JPEG = "jpeg"
    WEBP = "webp"

class ImageSource(Enum):
    """Sources for image acquisition."""
    DALLE = "dalle"
    WEB_SEARCH = "web_search"
    LOCAL = "local"

class ImageException(Exception):
    """Base exception for image-related errors."""
    pass

class GenerationException(ImageException):
    """Exception for image generation errors."""
    pass

class DownloadException(ImageException):
    """Exception for image download errors."""
    pass

class SearchException(ImageException):
    """Exception for image search errors."""
    pass

@dataclass
class ImageRequest:
    """Configuration for an image generation request."""
    prompt: str
    size: Union[ImageSize, str] = ImageSize.LARGE
    model: str = DALLE_MODEL
    n: int = 1
    quality: str = "standard"
    format: ImageFormat = ImageFormat.PNG

@dataclass
class ImageResult:
    """Result of an image operation."""
    success: bool
    file_path: Optional[str] = None
    url: Optional[str] = None
    error_message: Optional[str] = None
    size_bytes: Optional[int] = None
    
    @property
    def size_kb(self) -> Optional[float]:
        """Get image size in KB if available."""
        if self.size_bytes is not None:
            return self.size_bytes / 1024
        return None

class ImageService:
    """
    Service for generating and processing images.
    
    This service provides methods for generating images using AI models,
    downloading from URLs, and finding images through web searches.
    """
    
    # Class constants for retry configuration
    DEFAULT_MAX_RETRIES: ClassVar[int] = 3
    DEFAULT_BASE_DELAY: ClassVar[int] = 2
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the ImageService with optional custom API key.
        
        Args:
            api_key: Optional OpenAI API key. If None, uses key from config.
        """
        self.api_key = api_key or OPENAI_API_KEY
        self.client = OpenAI(api_key=self.api_key)
        logger.info(f"ImageService initialized with DALL-E model: {DALLE_MODEL}, test_mode: {TEST_SCENES}")
        
        # Ensure output directories exist
        os.makedirs(DIRS.scenes, exist_ok=True)
        logger.debug(f"Ensured output directory exists: {DIRS.scenes}")

    def generate_image_url(
        self, 
        prompt: str, 
        size: Union[str, ImageSize] = GENERATED_IMAGE_SIZE, 
        dalle_model: str = DALLE_MODEL
    ) -> Optional[str]:
        """
        Generates an image based on a text prompt using DALL-E.
        
        Args:
            prompt: The text prompt to generate the image
            size: The desired image dimensions (string or ImageSize enum)
            dalle_model: The specific DALL-E model to use
            
        Returns:
            The URL of the generated image, or None if generation failed
            
        Raises:
            GenerationException: If there's an error with the image generation
        """
        # Convert enum to string if needed
        if isinstance(size, ImageSize):
            size = size.value
            
        prompt_truncated = prompt[:30] + "..." if len(prompt) > 30 else prompt
        logger.info(f"Generating image with DALL-E model: {dalle_model}, size: {size}")
        logger.debug(f"Image prompt: {prompt}")
        
        try:
            response = self.client.images.generate(
                model=dalle_model,
                prompt=prompt,
                n=1,
                size=size
            )
            image_url = response.data[0].url if response.data else None
            
            if image_url:
                logger.info("Image URL successfully generated")
                logger.debug(f"Image URL: {image_url[:50]}...")
                return image_url
            else:
                error_message = "No image URL returned from DALL-E API"
                logger.warning(error_message)
                raise GenerationException(error_message)
                
        except Exception as e:
            error_message = f"Error generating image URL: {str(e)}"
            logger.error(error_message, exc_info=True)
            raise GenerationException(error_message) from e

    def download_image_from_llm(self, image_url: str, output_path: str) -> ImageResult:
        """
        Downloads an image from the specified URL and saves it to the given path.
        
        Args:
            image_url: The URL of the image to download
            output_path: The local file path where the image should be saved
            
        Returns:
            ImageResult with download status and file information
            
        Raises:
            DownloadException: If there's an error with the image download
        """
        logger.info(f"Downloading image to {output_path}")
        
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Download the image
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Save the image
            with open(output_path, "wb") as f:
                f.write(response.content)
                
            # Get file size
            size_bytes = os.path.getsize(output_path)
            size_kb = size_bytes / 1024
            
            logger.info(f"Image downloaded successfully ({size_kb:.2f} KB)")
            
            return ImageResult(
                success=True,
                file_path=output_path,
                url=image_url,
                size_bytes=size_bytes
            )
            
        except Exception as e:
            error_message = f"Error downloading image: {str(e)}"
            logger.error(error_message, exc_info=True)
            
            return ImageResult(
                success=False,
                url=image_url,
                error_message=error_message
            )

    def find_image_url_by_prompt(
        self, 
        prompt: str, 
        max_results: int = 1, 
        max_retries: int = DEFAULT_MAX_RETRIES, 
        base_delay: int = DEFAULT_BASE_DELAY
    ) -> Optional[str]:
        """
        Finds a related image based on a single prompt using DuckDuckGo search.
        
        Args:
            prompt: The text prompt to search for related images
            max_results: Maximum number of results to return
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds for exponential backoff
            
        Returns:
            A URL of a related image, or None if none found
            
        Raises:
            SearchException: If there's an error with the image search
        """
        prompt_truncated = prompt[:30] + "..." if len(prompt) > 30 else prompt
        logger.info(f"Searching for related image for prompt: {prompt_truncated}...")
        
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                ddgs = DDGS()
                results = list(ddgs.images(
                    prompt, 
                    max_results=max_results,
                    safesearch="on"
                ))
                
                # Extract first valid image URL
                if results:
                    image_url = results[0]["image"]
                    logger.info(f"Found image for prompt: {prompt_truncated}")
                    return image_url
                else:
                    logger.warning(f"No images found for prompt '{prompt_truncated}' (attempt {retry_count+1}/{max_retries})")
                    
            except Exception as e:
                logger.error(f"Error searching for image with prompt '{prompt_truncated}' (attempt {retry_count+1}/{max_retries}): {str(e)}")
            
            # If we need to retry
            retry_count += 1
            if retry_count < max_retries:
                wait_time = base_delay * (2 ** (retry_count - 1))  # Exponential backoff
                logger.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
        
        logger.warning(f"No image found after {max_retries} attempts")
        return None
    
    def download_image_from_url(self, image_url: str, output_path: str) -> ImageResult:
        """
        Downloads an image from a specified URL and saves it to the given path.
        
        Args:
            image_url: The URL of the image to download
            output_path: The file path where the image should be saved
            
        Returns:
            ImageResult with download status and file information
            
        Raises:
            DownloadException: If there's an error with the image download
        """
        try:
            logger.info(f"Downloading image from URL to {output_path}")
            
            # Ensure the directory exists
            directory = os.path.dirname(output_path)
            os.makedirs(directory, exist_ok=True)
            
            # Download the image
            response = requests.get(image_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Save the image to the specified path
            with open(output_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            
            # Get file size
            size_bytes = os.path.getsize(output_path)
            size_kb = size_bytes / 1024
                    
            logger.info(f"Successfully downloaded image to {output_path} ({size_kb:.2f} KB)")
            
            return ImageResult(
                success=True,
                file_path=output_path,
                url=image_url,
                size_bytes=size_bytes
            )
            
        except Exception as e:
            error_message = f"Error downloading image: {str(e)}"
            logger.error(error_message, exc_info=True)
            
            return ImageResult(
                success=False,
                url=image_url,
                error_message=error_message
            )

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitizes a string to be used as a valid filename.
        
        Args:
            filename: The string to sanitize
            
        Returns:
            A sanitized string that can be used as a filename
        """
        sanitized = re.sub(r'[\\/*?:"<>|]', "", filename)
        if sanitized != filename:
            logger.debug(f"Filename sanitized: '{filename}' -> '{sanitized}'")
        return sanitized

    def process_prompt(
        self, 
        prompt: str, 
        output_dir: str, 
        image_filename: str, 
        size: Union[str, ImageSize] = GENERATED_IMAGE_SIZE
    ) -> ImageResult:
        """
        Processes a single prompt with TEST_SCENES consideration.
        
        Args:
            prompt: The text prompt to generate the image
            output_dir: Directory to save the image
            image_filename: Filename for the generated image
            size: The desired image dimensions
            
        Returns:
            ImageResult with processing status and file information
        """
        try:
            sanitized_image_filename = self.sanitize_filename(image_filename)
            output_path = os.path.join(DIRS.scenes, sanitized_image_filename)
            logger.debug(f"Processing prompt for image: {sanitized_image_filename}")
            
            # TEST_SCENES check
            if TEST_SCENES and os.path.isfile(output_path):
                logger.info(f"Using existing image: {output_path} [TEST_MODE]")
                size_bytes = os.path.getsize(output_path)
                
                return ImageResult(
                    success=True,
                    file_path=output_path,
                    size_bytes=size_bytes
                )
            
            try:
                # Generate image URL
                image_url = self.generate_image_url(prompt, size)
                
                # Download the image
                if image_url:
                    return self.download_image_from_llm(image_url, output_path)
                else:
                    return ImageResult(
                        success=False,
                        error_message="Failed to generate image URL"
                    )
                    
            except GenerationException as e:
                return ImageResult(
                    success=False,
                    error_message=f"Image generation error: {str(e)}"
                )
                
        except Exception as e:
            error_message = f"Error processing image prompt: {str(e)}"
            logger.error(error_message, exc_info=True)
            
            return ImageResult(
                success=False,
                error_message=error_message
            )

    def generate_image(
        self, 
        prompt: str, 
        output_dir: Optional[str] = None, 
        image_filename: Optional[str] = None, 
        size: Union[str, ImageSize] = GENERATED_IMAGE_SIZE
    ) -> ImageResult:
        """
        Generates an image from a prompt and saves it to disk.
        
        Args:
            prompt: The text prompt to generate the image
            output_dir: Directory to save the image (defaults to DIRS.scenes)
            image_filename: Filename for the generated image (defaults to sanitized prompt)
            size: The desired image dimensions
            
        Returns:
            ImageResult with generation status and file information
        """
        # Set defaults if not provided
        output_dir = output_dir or DIRS.scenes
        
        if image_filename is None:
            # Create a filename from the prompt if none provided
            prompt_short = prompt[:30].strip()
            image_filename = f"{self.sanitize_filename(prompt_short)}.png"
            
        logger.info(f"Generating image: {image_filename}")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        logger.debug(f"Ensuring output directory exists: {output_dir}")
        
        result = self.process_prompt(
            prompt=prompt,
            output_dir=output_dir,
            image_filename=image_filename,
            size=size
        )
        
        if result.success:
            logger.info(f"Image {image_filename} generated successfully")
        else:
            logger.error(f"Failed to generate image {image_filename}: {result.error_message}")
            
        return result
    
    def find_and_download_image(
        self, 
        prompt: str, 
        output_dir: Optional[str] = None,
        image_filename: Optional[str] = None
    ) -> ImageResult:
        """
        Finds an image via web search and downloads it.
        
        Args:
            prompt: The search query to find the image
            output_dir: Directory to save the image (defaults to DIRS.scenes)
            image_filename: Filename for the downloaded image (defaults to sanitized prompt)
            
        Returns:
            ImageResult with search and download status
        """
        # Set defaults if not provided
        output_dir = output_dir or DIRS.scenes
        
        if image_filename is None:
            # Create a filename from the prompt if none provided
            prompt_short = prompt[:30].strip()
            image_filename = f"{self.sanitize_filename(prompt_short)}_web.png"
            
        # Full path to save the image
        output_path = os.path.join(output_dir, image_filename)
        
        # TEST_SCENES check
        if TEST_SCENES and os.path.isfile(output_path):
            logger.info(f"Using existing image: {output_path} [TEST_MODE]")
            size_bytes = os.path.getsize(output_path)
            
            return ImageResult(
                success=True,
                file_path=output_path,
                size_bytes=size_bytes
            )
            
        # Search for image
        try:
            image_url = self.find_image_url_by_prompt(prompt)
            
            if not image_url:
                return ImageResult(
                    success=False,
                    error_message=f"No image found for prompt: {prompt}"
                )
                
            # Download the found image
            return self.download_image_from_url(image_url, output_path)
            
        except Exception as e:
            error_message = f"Error finding and downloading image: {str(e)}"
            logger.error(error_message, exc_info=True)
            
            return ImageResult(
                success=False,
                error_message=error_message
            )