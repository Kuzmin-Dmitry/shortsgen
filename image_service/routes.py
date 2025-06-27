"""Image Service Routes - API endpoints for image generation operations."""

import logging
from fastapi import APIRouter, HTTPException
from models import ImageGenerationRequest, ImageGenerationResponse

logger = logging.getLogger(__name__)
router = APIRouter()


def get_image_service():
    """Get image service instance when needed."""
    from image_generator import ImageService
    return ImageService()


@router.post("/generateImage", response_model=ImageGenerationResponse)
async def generate_image(request: ImageGenerationRequest):
    """Generate image from text prompt using DALL-E.
    
    Args:
        request: Image generation request containing prompt and parameters
        
    Returns:
        ImageGenerationResponse: Generated image response with metadata
        
    Raises:
        HTTPException: If image generation fails
    """
    try:
        logger.info(f"Generating image for prompt: {request.prompt[:100]}...")
        
        image_service = get_image_service()
        result = await image_service.generate_image_async(
            prompt=request.prompt,
            size=request.size,
            background=request.background,
            quality=request.quality,
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["message"])
        
        return ImageGenerationResponse(
            success=result["success"],
            message=result["message"],
            image_url=result.get("image_url"),
            file_size=result.get("file_size"),
            width=result.get("width"),
            height=result.get("height"),
        )
        
    except Exception as e:
        logger.error(f"Image generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
