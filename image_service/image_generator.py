"""Image generation service implementation."""

import os
import base64
import hashlib
import requests
import asyncio
from typing import Dict, Any
from openai import OpenAI
from config import OPENAI_API_KEY, IMAGES_OUTPUT_DIR, DEFAULT_SIZE, DEFAULT_BACKGROUND, DEFAULT_QUALITY, logger


class ImageService:
    """Image generation service using OpenAI DALL-E API."""
    
    def __init__(self):
        """Initialize image service."""
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required")
        
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        os.makedirs(IMAGES_OUTPUT_DIR, exist_ok=True)
    
    def _generate_filename(self, prompt: str, size: str, background: str, quality: str) -> str:
        """Generate unique filename based on parameters."""
        content_hash = hashlib.md5(
            f"{prompt}_{size}_{background}_{quality}".encode()
        ).hexdigest()[:12]
        return f"image_{content_hash}.png"
    
    async def generate_image_async(
        self,
        prompt: str,
        size: str = DEFAULT_SIZE,
        background: str = DEFAULT_BACKGROUND,
        quality: str = DEFAULT_QUALITY,
    ) -> Dict[str, Any]:
        """Generate image asynchronously."""
        try:
            filename = self._generate_filename(prompt, size, background, quality)
            filepath = os.path.join(IMAGES_OUTPUT_DIR, filename)
            
            # Return cached image if exists
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                width, height = self._parse_size(size)
                return {
                    "success": True,
                    "message": "Image generated successfully (cached)",
                    "image_url": f"/output/images/{filename}",
                    "image_path": filepath,
                    "file_size": file_size,
                    "filename": filename,
                    "width": width,
                    "height": height,
                }
            
            # Validate parameters
            valid_sizes = {"1024x1024", "1536x1024", "1024x1536"}
            valid_qualities = {"high", "medium", "low"}
            valid_backgrounds = {"auto", "opaque", "transparent"}
            
            if size not in valid_sizes:
                size = DEFAULT_SIZE
            if background not in valid_backgrounds:
                background = DEFAULT_BACKGROUND
            if quality not in valid_qualities:
                quality = DEFAULT_QUALITY
            
            # Generate image
            response = self.client.images.generate(
                model="gpt-image-1",
                prompt=prompt,
                size=size,  # type: ignore
                background=background,  # type: ignore
                quality=quality,  # type: ignore
                n=1,
            )
            logger.info(f"OpenAI response generated successfully")
            
            if not response.data or not response.data[0]:
                raise ValueError("No image data returned from OpenAI")
            
            # For gpt-image-1, images are returned as base64
            image_data = response.data[0]
            if hasattr(image_data, 'b64_json') and image_data.b64_json:
                # Decode base64 and save
                image_bytes = base64.b64decode(image_data.b64_json)
                with open(filepath, "wb") as f:
                    f.write(image_bytes)
            elif hasattr(image_data, 'url') and image_data.url:
                # Fallback for models that return URLs
                image_response = requests.get(image_data.url)
                image_response.raise_for_status()
                with open(filepath, "wb") as f:
                    f.write(image_response.content)
            else:
                raise ValueError("No image URL or base64 data returned from OpenAI")
            
            file_size = os.path.getsize(filepath)
            width, height = self._parse_size(size)
            
            logger.info(f"Generated image: {filename} ({file_size} bytes)")
            
            return {
                "success": True,
                "message": "Image generated successfully",
                "image_url": f"/output/images/{filename}",
                "image_path": filepath,
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
        """Parse size string to width and height."""
        try:
            width, height = map(int, size.split('x'))
            return width, height
        except ValueError:
            return 1024, 1024
    
    def generate_image(self, request) -> Any:
        """Synchronous wrapper for backward compatibility."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            self.generate_image_async(
                prompt=request.prompt,
                size=getattr(request, 'size', DEFAULT_SIZE),
                background=getattr(request, 'background', DEFAULT_BACKGROUND),
                quality=getattr(request, 'quality', DEFAULT_QUALITY),
            )
        )
        
        from models import ImageGenerationResponse
        
        return ImageGenerationResponse(
            success=result["success"],
            message=result["message"],
            image_url=result.get("image_url"),
            file_size=result.get("file_size"),
            width=result.get("width"),
            height=result.get("height"),
        )
