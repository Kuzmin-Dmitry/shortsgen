"""FastAPI routes for text generation."""

import logging
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any

from models import TextGenerationRequest, TextGenerationResponse, HealthResponse
from models.domain import ModelType
from service import TextGenerationService
from exceptions import ModelException

logger = logging.getLogger(__name__)
router = APIRouter()

# Service instance
text_service = TextGenerationService()

@router.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="online",
        service="Text Service",
        version="1.0.0"
    )

@router.get("/health", response_model=HealthResponse)
async def health():
    """Detailed health check endpoint."""
    return HealthResponse(
        status="healthy",
        service="Text Service", 
        version="1.0.0"
    )

@router.post("/generate", response_model=TextGenerationResponse)
async def generate_text(request: TextGenerationRequest):
    """Generate text using the specified model and parameters."""
    try:
        logger.info(f"Received text generation request with model: {request.model}")
        
        # Check if mock mode is enabled
        if request.mock:
            logger.info("Mock mode enabled - returning simulated text generation response")
            mock_content = f"Mock generated text for prompt: '{request.prompt[:50]}...' using {request.model} model"
            
            return TextGenerationResponse(
                content=mock_content,
                success=True,
                model_used=request.model,
                tokens_generated=len(mock_content.split())
            )
        
        # Validate model type
        try:
            model_type = ModelType(request.model.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid model type: {request.model}. Supported: openai, gemma"
            )
        
        # Generate text
        result = text_service.generate_text(
            prompt=request.prompt,
            functions=request.functions,
            max_tokens=request.max_tokens,
            model=model_type,
            temperature=request.temperature,
            system_prompt=request.system_prompt
        )
        
        # Calculate tokens (approximate)
        tokens_generated = None
        if isinstance(result, str):
            tokens_generated = len(result.split())
        
        logger.info(f"Text generation completed successfully with model: {request.model}")
        
        return TextGenerationResponse(
            content=result,
            success=True,
            model_used=request.model,
            tokens_generated=tokens_generated
        )
        
    except ModelException as e:
        logger.error(f"Model error during text generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Text generation failed: {e}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during text generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {e}"
        )

@router.post("/extract-queries")
async def extract_queries(tool_call_result: Dict[str, Any]):
    """Extract search queries from tool call result."""
    try:
        logger.info("Received query extraction request")
        
        queries = text_service.extract_queries_from_tool_call(tool_call_result)
        
        logger.info(f"Extracted {len(queries)} queries successfully")
        
        return {
            "queries": queries,
            "success": True,
            "count": len(queries)
        }
        
    except Exception as e:
        logger.error(f"Error extracting queries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query extraction failed: {e}"
        )
