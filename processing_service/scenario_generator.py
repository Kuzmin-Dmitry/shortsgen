"""
Scenario generator using Jinja2 templates.
"""

import os
import uuid
import yaml
from datetime import datetime
from typing import Any, Dict, List, Optional
from jinja2 import Environment, FileSystemLoader

from config import logger
from models import Scenario, Task


class ScenarioGenerator:
    """Generator for scenarios from YAML templates."""
    
    def __init__(self, template_file: str = "scenaries.yml"):
        """Initialize scenario generator.
        
        Args:
            template_file: Path to YAML template file
        """
        self.template_file = template_file
        self._id_map: Dict[str, str] = {}
    
    def _setup_jinja_env(self) -> Environment:
        """Setup Jinja2 environment with custom functions."""
        env = Environment(
            loader=FileSystemLoader(searchpath=os.getcwd()),
            keep_trailing_newline=True,
            trim_blocks=False,
            lstrip_blocks=False,
        )
        
        def UUID(key: str) -> str:
            """Generate or retrieve UUID for given key."""
            if key not in self._id_map:
                self._id_map[key] = str(uuid.uuid4())
            return self._id_map[key]
        
        def short_uuid(key: str) -> str:
            """Generate or retrieve short UUID for given key."""
            if key not in self._id_map:
                self._id_map[key] = str(uuid.uuid4())[:8]
            return self._id_map[key]
        
        env.globals['UUID'] = UUID
        env.globals['SHORT_UUID'] = short_uuid
        env.globals['now'] = lambda: datetime.now().isoformat()
        
        return env
    
    def _load_scenarios(
        self,
        variables: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Load and render scenarios from template.
        
        Args:
            variables: Template variables
            
        Returns:
            List of rendered scenario dictionaries
        """
        # Reset ID map for each scenario generation
        self._id_map = {}
        
        env = self._setup_jinja_env()
        
        try:
            template = env.get_template(self.template_file)
            rendered = template.render(**variables)
            docs = list(yaml.safe_load_all(rendered))
            return docs
        except Exception as e:
            logger.error(f"Failed to load scenarios: {e}")
            raise
    
    def _expand_tasks_with_count(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Expand tasks with count field into multiple task instances.
        
        Args:
            tasks: List of task dictionaries
            
        Returns:
            Expanded list of tasks
        """
        expanded_tasks = []
        
        for task_data in tasks:
            count = task_data.get('count', 1)
            
            if isinstance(count, str):
                # Try to convert string to int (from template variables)
                try:
                    count = int(count)
                except ValueError:
                    count = 1
            
            if count == 1:
                # Single task - add as is but remove count field
                task_copy = task_data.copy()
                task_copy.pop('count', None)
                expanded_tasks.append(task_copy)
            else:
                # Multiple tasks - create instances
                for i in range(1, count + 1):
                    task_copy = task_data.copy()
                    
                    # Update IDs to be unique
                    original_id = task_copy.get('id', '')
                    if original_id:
                        task_copy['id'] = f"{original_id}_{i}"
                    
                    # Update prompt with index
                    if 'prompt' in task_copy:
                        prompt = str(task_copy['prompt'])
                        if not prompt.endswith(f" {i}"):
                            task_copy['prompt'] = f"{prompt} {i}"
                    
                    # Update reference fields to point to the correct instance
                    if 'slide_prompt_id' in task_copy and task_copy['slide_prompt_id']:
                        orig_prompt_id = task_copy['slide_prompt_id']
                        task_copy['slide_prompt_id'] = f"{orig_prompt_id}_{i}"
                    
                    # Remove count field from individual tasks
                    task_copy.pop('count', None)
                    
                    expanded_tasks.append(task_copy)
        
        return expanded_tasks
    
    def _build_dependency_graph(self, tasks: List[Task]) -> None:
        """Build dependency graph using consumers and queue fields.
        
        Args:
            tasks: List of tasks to process
        """
        task_map = {task.id: task for task in tasks}
        
        # Process dependencies based on task references
        for task in tasks:
            dependencies = []
            
            # Check for various dependency fields
            if task.text_task_id and task.text_task_id in task_map:
                dependencies.append(task.text_task_id)
            
            if task.slide_prompt_id and task.slide_prompt_id in task_map:
                dependencies.append(task.slide_prompt_id)
            
            if task.slide_ids:
                for slide_id in task.slide_ids:
                    if slide_id in task_map:
                        dependencies.append(slide_id)
            
            if task.voice_track_id and task.voice_track_id in task_map:
                dependencies.append(task.voice_track_id)
            
            # Special handling for CreateVideo task - collect all slide tasks
            if task.name == "CreateVideoFromSlides":
                slide_tasks = [t for t in tasks if t.name == "CreateSlide"]
                task.slide_ids = [t.id for t in slide_tasks]
                dependencies.extend(task.slide_ids)
            
            # Set queue count to number of dependencies
            task.queue = len(dependencies)
            
            # Add this task as consumer to its dependencies
            for dep_id in dependencies:
                if dep_id in task_map:
                    dep_task = task_map[dep_id]
                    if task.id not in dep_task.consumers:
                        dep_task.consumers.append(task.id)
    
    def create_video_scenario(
        self,
        description: str,
        slides_count: int = 3
    ) -> Scenario:
        """Create video scenario with slides.
        
        Args:
            description: Video description/prompt
            slides_count: Number of slides to generate
            
        Returns:
            Generated scenario
        """
        variables = {
            'N_SLIDES': slides_count,
            'PROMPT': description,
            'VIDEO_RESOLUTION': '1920x1080',
            'BASE_PROMPT': description,  # Default value to avoid template errors
            'RESOLUTION': '1920x1080',  # Default value to avoid template errors
        }
        
        scenarios = self._load_scenarios(variables)
        
        # Find CreateVideo scenario
        video_scenario = None
        for scenario_data in scenarios:
            if scenario_data.get('name') == 'ScenarioCreateVideo':
                video_scenario = scenario_data
                break
        
        if not video_scenario:
            raise ValueError("ScenarioCreateVideo not found in templates")
        
        # Expand tasks with count
        expanded_tasks = self._expand_tasks_with_count(video_scenario['tasks'])
        
        # Convert to Task objects
        tasks = []
        for task_data in expanded_tasks:
            tasks.append(Task(**task_data))
        
        # Build dependency graph
        self._build_dependency_graph(tasks)
        
        scenario = Scenario(
            scenario_id=video_scenario['scenario_id'],
            version=video_scenario['version'],
            name=video_scenario['name'],
            variables=video_scenario.get('variables', {}),
            tasks=tasks
        )
        
        logger.info(
            f"Generated CreateVideo scenario with {len(tasks)} tasks "
            f"for {slides_count} slides"
        )
        
        return scenario
    
    def create_voice_scenario(self, description: str) -> Scenario:
        """Create voice-only scenario.
        
        Args:
            description: Text to convert to voice
            
        Returns:
            Generated scenario
        """
        variables = {
            'PROMPT': description,
            'N_SLIDES': 0,  # Default value to avoid template errors
        }
        
        scenarios = self._load_scenarios(variables)
        
        # Find CreateVoice scenario
        voice_scenario = None
        for scenario_data in scenarios:
            if scenario_data.get('name') == 'ScenarioCreateVoice':
                voice_scenario = scenario_data
                break
        
        if not voice_scenario:
            raise ValueError("ScenarioCreateVoice not found in templates")
        
        # Expand tasks with count
        expanded_tasks = self._expand_tasks_with_count(voice_scenario['tasks'])
        
        # Convert to Task objects
        tasks = []
        for task_data in expanded_tasks:
            tasks.append(Task(**task_data))
        
        # Build dependency graph
        self._build_dependency_graph(tasks)
        
        scenario = Scenario(
            scenario_id=voice_scenario['scenario_id'],
            version=voice_scenario['version'],
            name=voice_scenario['name'],
            variables=voice_scenario.get('variables', {}),
            tasks=tasks
        )
        
        logger.info(f"Generated CreateVoice scenario with {len(tasks)} tasks")
        
        return scenario
    
    def create_slides_scenario(
        self,
        base_prompt: str,
        slides_count: int = 1
    ) -> Scenario:
        """Create slides-only scenario.
        
        Args:
            base_prompt: Base prompt for slide generation
            slides_count: Number of slides to generate
            
        Returns:
            Generated scenario
        """
        variables = {
            'N_SLIDES': slides_count,
            'BASE_PROMPT': base_prompt,
            'RESOLUTION': '1024x768',
            'PROMPT': base_prompt,  # Default value to avoid template errors
        }
        
        scenarios = self._load_scenarios(variables)
        
        # Find CreateSlides scenario
        slides_scenario = None
        for scenario_data in scenarios:
            if scenario_data.get('name') == 'ScenarioCreateSlides':
                slides_scenario = scenario_data
                break
        
        if not slides_scenario:
            raise ValueError("ScenarioCreateSlides not found in templates")
        
        # Expand tasks with count
        expanded_tasks = self._expand_tasks_with_count(slides_scenario['tasks'])
        
        # Convert to Task objects
        tasks = []
        for task_data in expanded_tasks:
            tasks.append(Task(**task_data))
        
        # Build dependency graph
        self._build_dependency_graph(tasks)
        
        scenario = Scenario(
            scenario_id=slides_scenario['scenario_id'],
            version=slides_scenario['version'],
            name=slides_scenario['name'],
            variables=slides_scenario.get('variables', {}),
            tasks=tasks
        )
        
        logger.info(
            f"Generated CreateSlides scenario with {len(tasks)} tasks "
            f"for {slides_count} slides"
        )
        
        return scenario
