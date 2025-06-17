"""
Workflow Orchestrator - Coordinates video generation pipeline.
"""

import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

from content_generator import ContentGenerator
from media_processor import MediaProcessor
from workflow_state import WorkflowState, WorkflowResult, StageStatus
from resilience import with_retry, RetryConfig

logger = logging.getLogger(__name__)

class GenerationStrategy(Enum):
    AI_GENERATED = "ai_generated"
    WEB_SEARCH = "web_search"

class WorkflowOrchestrator:
    """Orchestrates the video generation workflow."""
    
    def __init__(self):
        self.content_generator = ContentGenerator()
        self.media_processor = MediaProcessor()
        logger.info("WorkflowOrchestrator initialized")
    
    def execute_workflow(
        self, 
        strategy: GenerationStrategy, 
        custom_prompt: Optional[str] = None
    ) -> WorkflowResult:
        """Execute the complete video generation workflow."""
        workflow_start = time.time()
        state = WorkflowState()
        
        try:
            logger.info(f"Starting workflow with strategy: {strategy.value}")
            
            # Step 1: Generate narrative content
            narrative_result = self.content_generator.generate_narrative(custom_prompt)
            state.add_result("narrative", narrative_result)
            
            if narrative_result.status != StageStatus.COMPLETED:
                return self._create_failure_result(
                    "Failed to generate narrative", state, workflow_start
                )
            
            # Step 2: Generate content based on strategy
            if strategy == GenerationStrategy.AI_GENERATED:
                # Generate scene descriptions for AI image generation
                scenes_result = self.content_generator.generate_scene_descriptions(
                    narrative_result.data
                )
                state.add_result("scene_descriptions", scenes_result)
                
                if scenes_result.status != StageStatus.COMPLETED:
                    return self._create_failure_result(
                        "Failed to generate scene descriptions", state, workflow_start
                    )
                
                # Generate AI images
                images_result = self.media_processor.generate_scene_images(
                    scenes_result.data
                )
                state.add_result("images", images_result)
                
            else:  # WEB_SEARCH strategy
                # Generate search queries
                queries_result = self.content_generator.generate_search_queries(
                    narrative_result.data
                )
                state.add_result("search_queries", queries_result)
                
                if queries_result.status != StageStatus.COMPLETED:
                    return self._create_failure_result(
                        "Failed to generate search queries", state, workflow_start
                    )
                
                # Find web images
                images_result = self.media_processor.find_web_images(
                    queries_result.data
                )
                state.add_result("images", images_result)
            
            if images_result.status != StageStatus.COMPLETED:
                return self._create_failure_result(
                    "Failed to generate/find images", state, workflow_start
                )
            
            # Step 3: Generate audio
            audio_result = self.media_processor.generate_audio(narrative_result.data)
            state.add_result("audio", audio_result)
            
            if audio_result.status != StageStatus.COMPLETED:
                return self._create_failure_result(
                    "Failed to generate audio", state, workflow_start
                )
            
            # Step 4: Compose video
            video_result = self.media_processor.compose_video(
                images_result.data, audio_result.data
            )
            state.add_result("video", video_result)
            
            if video_result.status != StageStatus.COMPLETED:
                return self._create_failure_result(
                    "Failed to compose video", state, workflow_start
                )
            
            # Mark workflow as completed
            state.completed_at = datetime.now()
            elapsed_time = time.time() - workflow_start
            
            logger.info(f"Workflow completed successfully in {elapsed_time:.2f}s")
            
            return WorkflowResult(
                success=True,
                output_path=video_result.data,
                state=state,
                elapsed_time=elapsed_time
            )
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return self._create_failure_result(str(e), state, workflow_start)
    
    def _create_failure_result(
        self, 
        error_message: str, 
        state: WorkflowState, 
        start_time: float
    ) -> WorkflowResult:
        """Create a failure result with proper state tracking."""
        state.completed_at = datetime.now()
        elapsed_time = time.time() - start_time
        
        return WorkflowResult(
            success=False,
            error_message=error_message,
            state=state,
            elapsed_time=elapsed_time
        )
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get status of a workflow (placeholder for future enhancement)."""
        # This would integrate with a workflow tracking system
        return {
            "workflow_id": workflow_id,
            "status": "not_implemented",
            "message": "Workflow status tracking not yet implemented"
        }
