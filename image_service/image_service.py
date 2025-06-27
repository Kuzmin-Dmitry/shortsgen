"""
Image generation service implementation.
"""

import os
import hashlib
import requests
from typing import Dict, Any, Optional
from openai import OpenAI
from config import OPENAI_API_KEY, IMAGES_OUTPUT_DIR, DEFAULT_SIZE, DEFAULT_STYLE, DEFAULT_QUALITY, logger


class ImageService:
    """Image generation service using OpenAI DALL-E API."""
    
    def __init__(self):
        """Initialize image service."""
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required")
        
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self._ensure_output_dir()
    
    def _ensure_output_dir(self) -> None:
        """Ensure output directory exists."""
        os.makedirs(IMAGES_OUTPUT_DIR, exist_ok=True)
    
    def _generate_filename(self, prompt: str, size: str, style: str, quality: str) -> str:
        """Generate unique filename based on parameters.
        
        Args:
            prompt: Input prompt
            size: Image size
            style: Image style
            quality: Image quality
            
        Returns:
            Unique filename
        """
        content_hash = hashlib.md5(
            f"{prompt}_{size}_{style}_{quality}".encode()
        ).hexdigest()[:12]
        return f"image_{content_hash}.png"
    
    async def generate_image_async(
        self,
        prompt: str,
        size: str = DEFAULT_SIZE,
        style: str = DEFAULT_STYLE,
        quality: str = DEFAULT_QUALITY,
    ) -> Dict[str, Any]:
        """Generate image asynchronously.
        
        Args:
            prompt: Text prompt for image generation
            size: Image size
            style: Image style
            quality: Image quality
            
        Returns:
            Result dictionary
        """
        try:
            filename = self._generate_filename(prompt, size, style, quality)
            filepath = os.path.join(IMAGES_OUTPUT_DIR, filename)
            
            # Check if file already exists
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                width, height = self._parse_size(size)
                return {
                    "success": True,
                    "message": "Image generated successfully (cached)",
                    "image_url": f"/output/images/{filename}",
                    "file_size": file_size,
                    "filename": filename,
                    "width": width,
                    "height": height,
                }
            
            # Validate and convert parameters to proper types
            valid_sizes = ["1024x1024", "1536x1024", "1024x1536", "256x256", "512x512", "1792x1024", "1024x1792"]
            valid_styles = ["vivid", "natural"]
            valid_qualities = ["standard", "hd"]
            
            # Use defaults if invalid values provided
            if size not in valid_sizes:
                size = DEFAULT_SIZE
            if style not in valid_styles:
                style = DEFAULT_STYLE
            if quality not in valid_qualities:
                quality = DEFAULT_QUALITY
            
            # Generate image using OpenAI DALL-E
            response = self.client.images.generate(
                model="gpt-image-1",
                prompt=prompt,
                size=size,  # type: ignore
                style=style,  # type: ignore
                quality=quality,  # type: ignore
                n=1,
            )
            
            # Download and save image
            if not response.data or not response.data[0].url:
                raise ValueError("No image URL returned from OpenAI")
                
            image_url = response.data[0].url
            image_response = requests.get(image_url)
            image_response.raise_for_status()
            
            with open(filepath, "wb") as f:
                f.write(image_response.content)
            
            file_size = os.path.getsize(filepath)
            width, height = self._parse_size(size)
            
            logger.info(f"Generated image: {filename} ({file_size} bytes)")
            
            return {
                "success": True,
                "message": "Image generated successfully",
                "image_url": f"/output/images/{filename}",
                "file_size": file_size,
                "filename": filename,
                "width": width,
                "height": height,
            }
            
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            return {
                "success": False,
                "message": f"Image generation failed: {str(e)}",
            }
    
    def _parse_size(self, size: str) -> tuple[int, int]:
        """Parse size string to width and height.
        
        Args:
            size: Size string like "1024x1024"
            
        Returns:
            Tuple of (width, height)
        """
        try:
            width, height = map(int, size.split('x'))
            return width, height
        except ValueError:
            return 1024, 1024
    
    def generate_image(self, request) -> Any:
        """Synchronous wrapper for backward compatibility."""
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            self.generate_image_async(
                prompt=request.prompt,
                size=getattr(request, 'size', DEFAULT_SIZE),
                style=getattr(request, 'style', DEFAULT_STYLE),
                quality=getattr(request, 'quality', DEFAULT_QUALITY),
            )
        )
        
        # Convert to response object for compatibility
        from models import ImageGenerationResponse
        
        return ImageGenerationResponse(
            success=result["success"],
            message=result["message"],
            image_url=result.get("image_url"),
            file_size=result.get("file_size"),
            width=result.get("width"),
            height=result.get("height"),
        )


def get_image_service() -> ImageService:
    """Get image service instance."""
    return ImageService()
