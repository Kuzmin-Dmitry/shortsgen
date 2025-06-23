"""
Content Generator - Specialized service for generating narrative content and image descriptions.
"""

import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

from text_service import TextService
from workflow_state import StageResult, StageStatus
from resilience import with_retry, RetryConfig
from config import NOVELLA_PROMPT, FRAMES_PROMPT_TEMPLATE, SEARCH_QUERY_FUNCTION, SEARCH_USER_PROMPT

logger = logging.getLogger(__name__)

class ContentGenerator:
    """Service responsible for generating narrative content and scene descriptions."""
    
    def __init__(self):
        self.text_service = TextService()
        self.retry_config = RetryConfig(max_attempts=3, base_delay=1.0)
        logger.info("ContentGenerator initialized")
    
    @with_retry(RetryConfig())
    def generate_narrative(self, custom_prompt: Optional[str] = None) -> StageResult:
        """Generate narrative text for the video."""
        stage_name = "narrative_generation"
        started_at = datetime.now()
        
        try:
            prompt = custom_prompt or NOVELLA_PROMPT
            logger.info(f"Generating narrative with prompt: {prompt[:100]}...")
            
            narrative_text = self.text_service.generate_text(prompt)
            
            if not narrative_text or len(str(narrative_text).strip()) == 0:
                raise ValueError("Generated narrative is empty")
            
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            
            logger.info(f"Narrative generated successfully in {duration:.2f}s")
            
            return StageResult(
                stage_name=stage_name,
                status=StageStatus.COMPLETED,
                data=str(narrative_text),
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration
            )
            
        except Exception as e:
            logger.error(f"Failed to generate narrative: {e}")
            return StageResult(
                stage_name=stage_name,
                status=StageStatus.FAILED,
                error_message=str(e),
                started_at=started_at,
                completed_at=datetime.now()
            )
    
    @with_retry(RetryConfig())
    def generate_scene_descriptions(self, narrative_text: str) -> StageResult:
        """Generate scene descriptions from narrative text."""
        stage_name = "scene_descriptions"
        started_at = datetime.now()
        
        try:
            logger.info("Generating scene descriptions from narrative")
            
            prompt = FRAMES_PROMPT_TEMPLATE.format(novella_text=narrative_text)
            scene_descriptions = self.text_service.generate_text(prompt)
            
            if not scene_descriptions:
                raise ValueError("Generated scene descriptions are empty")
            
            # Parse scenes if they're in a structured format
            scenes = self._parse_scene_descriptions(str(scene_descriptions))
            
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            
            logger.info(f"Generated {len(scenes)} scene descriptions in {duration:.2f}s")
            
            return StageResult(
                stage_name=stage_name,
                status=StageStatus.COMPLETED,
                data=scenes,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration
            )
            
        except Exception as e:
            logger.error(f"Failed to generate scene descriptions: {e}")
            return StageResult(
                stage_name=stage_name,
                status=StageStatus.FAILED,
                error_message=str(e),
                started_at=started_at,
                completed_at=datetime.now()
            )
    
    @with_retry(RetryConfig())
    def generate_search_queries(self, narrative_text: str, count_scenes: int = 6) -> StageResult:
        """Generate search queries for finding images."""
        stage_name = "search_queries"
        started_at = datetime.now()
        
        try:
            logger.info("Generating search queries for image search")
            
            search_result = self.text_service.generate_text(
                prompt=SEARCH_USER_PROMPT.format(
                    novella_text=narrative_text,
                    count_scenes=count_scenes
                ),
                functions=SEARCH_QUERY_FUNCTION
            )
            
            if not search_result:
                raise ValueError("Generated search queries are empty")
            
            # Extract search queries from the result
            queries = self._extract_search_queries(search_result)
            
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            
            logger.info(f"Generated {len(queries)} search queries in {duration:.2f}s")
            
            return StageResult(
                stage_name=stage_name,
                status=StageStatus.COMPLETED,
                data=queries,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration
            )
            
        except Exception as e:
            logger.error(f"Failed to generate search queries: {e}")
            return StageResult(
                stage_name=stage_name,
                status=StageStatus.FAILED,
                error_message=str(e),
                started_at=started_at,
                completed_at=datetime.now()
            )
    
    def _parse_scene_descriptions(self, raw_descriptions: str) -> List[str]:
        """Parse scene descriptions from raw text."""
        try:
            # Simple parsing - split by numbers or scene markers
            lines = raw_descriptions.strip().split('\n')
            scenes = []
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Remove scene numbers like "1.", "Scene 1:", etc.
                    import re
                    clean_line = re.sub(r'^\d+[\.\):]?\s*', '', line)
                    clean_line = re.sub(r'^Scene\s+\d+[\.\):]?\s*', '', clean_line, flags=re.IGNORECASE)
                    
                    if clean_line:
                        scenes.append(clean_line)
            
            return scenes[:6]  # Limit to 6 scenes
            
        except Exception as e:
            logger.warning(f"Failed to parse scenes, using raw text: {e}")
            return [raw_descriptions]
    
    def _extract_search_queries(self, search_result: Any) -> List[str]:
        """Extract search queries from the text service result."""
        try:
            if isinstance(search_result, dict):
                if "function_call" in search_result:
                    # Extract from function call
                    args = search_result["function_call"].get("arguments", "{}")
                    import json
                    parsed_args = json.loads(args) if isinstance(args, str) else args
                    return parsed_args.get("queries", [])
                elif "tool_calls" in search_result:
                    # Extract from tool calls
                    queries = []
                    for tool_call in search_result["tool_calls"]:
                        if tool_call.get("function", {}).get("name") == "generate_search_queries":
                            args = tool_call["function"].get("arguments", "{}")
                            import json
                            parsed_args = json.loads(args) if isinstance(args, str) else args
                            queries.extend(parsed_args.get("queries", []))
                    return queries
                elif "content" in search_result:
                    # Parse from content
                    return self._parse_queries_from_text(search_result["content"])
            
            # Fallback to parsing from string
            return self._parse_queries_from_text(str(search_result))
            
        except Exception as e:
            logger.warning(f"Failed to extract search queries: {e}")
            return ["nature scene", "landscape", "environment", "scenery", "outdoor view", "natural setting"]
    
    def _parse_queries_from_text(self, text: str) -> List[str]:
        """Parse queries from plain text."""
        try:
            lines = text.strip().split('\n')
            queries = []
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Remove numbering and clean up
                    import re
                    clean_line = re.sub(r'^\d+[\.\):]?\s*', '', line)
                    clean_line = clean_line.strip('"\'')
                    
                    if clean_line and len(clean_line) > 3:
                        queries.append(clean_line)
            
            return queries[:6] if queries else ["nature scene", "landscape", "environment"]
            
        except Exception:
            return ["nature scene", "landscape", "environment", "scenery", "outdoor view", "natural setting"]
