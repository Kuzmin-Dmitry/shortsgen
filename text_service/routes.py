"""
Text Service Routes - API endpoints for text generation operations.
"""

import logging
from fastapi import APIRouter, HTTPException
from models import TextGenerationRequest, TextGenerationResponse
from openai_service import get_openai_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Health check endpoint for service monitoring.
    
    Returns:
        dict: Service health status information
    """
    return {
        "status": "healthy",
        "service": "Text Service", 
        "version": "1.0.0"
    }

@router.post("/generateText", response_model=TextGenerationResponse)
async def generate_text(request: TextGenerationRequest):
    """
    Generate text based on the provided request.
    
    Args:
        request: Text generation request
        
    Returns:
    Returns:
        TextGenerationResponse: Generated text response
    """
    try:
        openai_service = get_openai_service()
        response = openai_service.generate_text(request)
        
        if not response.success:
            raise HTTPException(status_code=500, detail=response.message)
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
