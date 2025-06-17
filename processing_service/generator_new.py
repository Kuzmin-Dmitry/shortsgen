"""
Generator - Legacy wrapper for backward compatibility.
"""

import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Union, Dict, Any, TypeVar, Generic, Tuple, Callable
import logging
from pathlib import Path

from audio_client import AudioClient
from video_client import VideoClient
from text_service import TextService
from image_service import ImageService
from workflow_orchestrator import WorkflowOrchestrator
from workflow_orchestrator import GenerationStrategy as WorkflowStrategy
from config import (
    FRAMES_PROMPT_TEMPLATE,
    DIRS,
    VOICE_FILE_PATH, 
    VIDEO_FILE_PATH, 
    NOVELLA_PROMPT,
    NUMBER_OF_THE_SCENES,
    SEARCH_QUERY_FUNCTION,
    SEARCH_USER_PROMPT
)

# Initialize the logger
logger = logging.getLogger(__name__)

class GenerationStage(Enum):
    """Enumeration of the video generation workflow stages."""
    NOVELLA_TEXT = "novella_text"
    SCENE_DESCRIPTIONS = "scene_descriptions"
    IMAGE_SEARCH_QUERIES = "image_search_queries"
    SCENE_IMAGES = "scene_images"
    VOICE_NARRATION = "voice_narration"
    VIDEO_COMPOSITION = "video_composition"

class GenerationStrategy(Enum):
    """Enumeration of available generation strategies."""
    AI_GENERATED = "ai_generated"
    WEB_SEARCH = "web_search"

T = TypeVar('T')

@dataclass
class OperationResult(Generic[T]):
    """Generic result object for operation outcomes with metadata."""
    success: bool
    data: Optional[T] = None
    error_message: Optional[str] = None
    elapsed_time: Optional[float] = None
    stage: Optional[GenerationStage] = None

    def __bool__(self) -> bool:
        """Allow direct boolean evaluation of result."""
        return self.success

class GenerationError(Exception):
    """Base exception for generation process errors."""
    def __init__(self, message: str, stage: GenerationStage):
        self.stage = stage
        self.message = message
        super().__init__(f"Error in {stage.value}: {message}")

class Generator:
    """
    Legacy wrapper around WorkflowOrchestrator for backward compatibility.
    
    This class maintains the original API while delegating work to the new
    modular architecture. New code should use WorkflowOrchestrator directly.
    """    
    def __init__(self):
        """Initialize generator with workflow orchestrator."""
        self.orchestrator = WorkflowOrchestrator()
        # Legacy clients for direct access if needed
        self.audio_client = AudioClient()
        self.text_service = TextService()
        self.image_service = ImageService()
        self.video_client = VideoClient()
        logger.info("Generator initialized with workflow orchestrator")

    def find_and_generate(self, custom_prompt: Optional[str] = None) -> OperationResult[str]:
        """
        Generate a video by finding and using images from the internet.
        
        This method uses the new workflow orchestrator with web search strategy.
        """
        logger.info("Starting find and generate process (web search strategy)")
        start_time = time.time()
        
        try:
            result = self.orchestrator.execute_workflow(
                strategy=WorkflowStrategy.WEB_SEARCH,
                custom_prompt=custom_prompt
            )
            
            elapsed_time = time.time() - start_time
            
            if result.success:
                return OperationResult(
                    success=True,
                    data=result.output_path,
                    elapsed_time=elapsed_time,
                    stage=GenerationStage.VIDEO_COMPOSITION
                )
            else:
                return OperationResult(
                    success=False,
                    error_message=result.error_message,
                    elapsed_time=elapsed_time,
                    stage=GenerationStage.VIDEO_COMPOSITION
                )
                
        except Exception as e:
            logger.error(f"Find and generate failed: {e}")
            return OperationResult(
                success=False,
                error_message=str(e),
                elapsed_time=time.time() - start_time,
                stage=GenerationStage.VIDEO_COMPOSITION
            )

    def ai_generate(self, custom_prompt: Optional[str] = None) -> OperationResult[str]:
        """
        Generate a video using AI-generated images.
        
        This method uses the new workflow orchestrator with AI generation strategy.
        """
        logger.info("Starting AI generate process (AI image generation strategy)")
        start_time = time.time()
        
        try:
            result = self.orchestrator.execute_workflow(
                strategy=WorkflowStrategy.AI_GENERATED,
                custom_prompt=custom_prompt
            )
            
            elapsed_time = time.time() - start_time
            
            if result.success:
                return OperationResult(
                    success=True,
                    data=result.output_path,
                    elapsed_time=elapsed_time,
                    stage=GenerationStage.VIDEO_COMPOSITION
                )
            else:
                return OperationResult(
                    success=False,
                    error_message=result.error_message,
                    elapsed_time=elapsed_time,
                    stage=GenerationStage.VIDEO_COMPOSITION
                )
                
        except Exception as e:
            logger.error(f"AI generate failed: {e}")
            return OperationResult(
                success=False,
                error_message=str(e),
                elapsed_time=time.time() - start_time,
                stage=GenerationStage.VIDEO_COMPOSITION
            )

    # Legacy methods for backward compatibility
    def generate(self, custom_prompt: Optional[str] = None) -> OperationResult[str]:
        """Legacy method - delegates to find_and_generate."""
        return self.find_and_generate(custom_prompt)
