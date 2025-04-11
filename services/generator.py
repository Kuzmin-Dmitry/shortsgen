import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Union, Dict, Any, TypeVar, Generic, Tuple

from services.audio_service import AudioService
from services.video_service import VideoEditor
from services.chat_service import ChatService
from services.image_service import ImageService
from utils.logger import LoggerConfigurator, LogLevel
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

# Initialize the custom logger
logger_configurator = LoggerConfigurator()
logger = logger_configurator.get_logger("generator")

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
    Central service that coordinates the video generation workflow.
    
    This service integrates multiple specialized services to create
    a complete video generation pipeline, from text to final video.
    It supports different generation strategies and provides detailed
    feedback on the generation process.
    """
    
    def __init__(self):
        """Initialize generator with all required services."""
        self.audio_service = AudioService()
        self.chat_service = ChatService()
        self.image_service = ImageService()
        self.video_editor = VideoEditor()
        logger.info("Generator initialized with all required services")

    def find_and_generate(self, custom_prompt: Optional[str] = None) -> OperationResult[str]:
        """
        Generate a video by finding and using images from the internet.
        
        This method coordinates the generation of a video using images found
        through web searches, combining them with AI-generated narrative and audio.
        
        Args:
            custom_prompt: Optional custom narrative prompt to override default
            
        Returns:
            OperationResult with success status and output video path
        """
        custom_prompt = custom_prompt or NOVELLA_PROMPT
        logger.info("Starting the find and generate process")
        logger.debug(f"Using novella prompt: {custom_prompt}")
        start_time = time.time()

        # Generate the novella text
        novella_result = self._generate_novella_text(custom_prompt)
        if not novella_result:
            return OperationResult(
                success=False,
                error_message=f"Video generation aborted: {novella_result.error_message}",
                stage=GenerationStage.NOVELLA_TEXT
            )
        novella_text = novella_result.data
        logger.debug(f"Generated novella text: {novella_text}")

        # Generate image search queries
        queries_result = self._generate_image_web_requests(novella_text, SEARCH_QUERY_FUNCTION)
        if not queries_result:
            return OperationResult(
                success=False,
                error_message=f"Video generation aborted: {queries_result.error_message}",
                stage=GenerationStage.IMAGE_SEARCH_QUERIES
            )
        image_requests_text = queries_result.data
        logger.debug(f"Generated image requests: {image_requests_text}")
    
        # Find and download images
        images_result = self._download_images_from_web(image_requests_text)
        if not images_result:
            return OperationResult(
                success=False,
                error_message=f"Video generation aborted: {images_result.error_message}",
                stage=GenerationStage.SCENE_IMAGES
            )
            
        # Generate voice narration
        voice_result = self._generate_voice_from_text(novella_text)
        if not voice_result:
            return OperationResult(
                success=False,
                error_message=f"Video generation aborted: {voice_result.error_message}",
                stage=GenerationStage.VOICE_NARRATION
            )
            
        # Compose final video
        video_result = self._compose_video_with_audio(novella_text)
        if not video_result:
            return OperationResult(
                success=False,
                error_message=f"Video generation aborted: {video_result.error_message}",
                stage=GenerationStage.VIDEO_COMPOSITION
            )
        
        elapsed_time = time.time() - start_time
        logger.info(f"Find and generate process completed successfully in {elapsed_time:.2f} seconds")
        
        return OperationResult(
            success=True,
            data=VIDEO_FILE_PATH,
            elapsed_time=elapsed_time
        )

    def generate(self) -> OperationResult[str]:
        """
        Generate a complete video using AI for all content.
        
        This method coordinates the end-to-end generation of a video
        using AI-generated text, images, and audio narration.
        
        Returns:
            OperationResult with success status and output video path
        """
        logger.info("Starting AI-based video generation process")
        start_time = time.time()
        
        # Generate the narrative text
        novella_result = self._generate_novella_text()
        if not novella_result:
            return OperationResult(
                success=False,
                error_message=f"Video generation aborted: {novella_result.error_message}",
                stage=GenerationStage.NOVELLA_TEXT
            )
        novella_text = novella_result.data
        logger.debug(f"Generated novella text: {novella_text}")
            
        # Generate scene descriptions
        frames_result = self._generate_scene_descriptions(novella_text)
        if not frames_result:
            return OperationResult(
                success=False,
                error_message=f"Video generation aborted: {frames_result.error_message}",
                stage=GenerationStage.SCENE_DESCRIPTIONS
            )
        frames_text = frames_result.data
            
        # Generate scene images
        images_result = self._generate_scene_images(frames_text)
        if not images_result:
            return OperationResult(
                success=False,
                error_message=f"Video generation aborted: {images_result.error_message}",
                stage=GenerationStage.SCENE_IMAGES
            )
            
        # Generate voice narration
        voice_result = self._generate_voice_from_text(novella_text)
        if not voice_result:
            return OperationResult(
                success=False,
                error_message=f"Video generation aborted: {voice_result.error_message}",
                stage=GenerationStage.VOICE_NARRATION
            )
            
        # Compose final video
        video_result = self._compose_video_with_audio(novella_text)
        if not video_result:
            return OperationResult(
                success=False,
                error_message=f"Video generation aborted: {video_result.error_message}",
                stage=GenerationStage.VIDEO_COMPOSITION
            )
        
        elapsed_time = time.time() - start_time
        logger.info(f"Video generation completed successfully in {elapsed_time:.2f} seconds")
        
        return OperationResult(
            success=True,
            data=VIDEO_FILE_PATH,
            elapsed_time=elapsed_time
        )
    
    def _execute_operation(self, 
                          operation_func: callable, 
                          operation_name: str, 
                          stage: GenerationStage,
                          preview_length: int = 40) -> OperationResult[Any]:
        """
        Executes an operation with standardized error handling and result logging.
        
        Args:
            operation_func: Function performing the operation
            operation_name: Operation name for logging
            stage: Generation stage this operation belongs to
            preview_length: Length of result preview in logs
            
        Returns:
            OperationResult with operation outcome and metadata
        """
        logger.info(f"Starting operation: {operation_name}")
        logger.debug(f"Operation '{operation_name}' started")
        start_time = time.time()
        
        try:
            result = operation_func()
            elapsed_time = time.time() - start_time
            
            if result is not None:
                if isinstance(result, str):
                    result_preview = (result[:preview_length] + "...") if len(result) > preview_length else result
                    logger.info(f"Operation '{operation_name}' completed successfully in {elapsed_time:.2f}s")
                    logger.debug(f"Result preview: {result_preview}")
                else:
                    logger.info(f"Operation '{operation_name}' completed successfully in {elapsed_time:.2f}s")
                    logger.debug(f"Operation '{operation_name}' result: {result}")
                
                return OperationResult(
                    success=True,
                    data=result,
                    elapsed_time=elapsed_time,
                    stage=stage
                )
            else:
                logger.warning(f"Operation '{operation_name}' returned empty result in {elapsed_time:.2f}s")
                return OperationResult(
                    success=False,
                    error_message=f"Operation '{operation_name}' returned empty result",
                    elapsed_time=elapsed_time,
                    stage=stage
                )
                
        except Exception as error:
            elapsed_time = time.time() - start_time
            logger.error(f"Operation '{operation_name}' failed after {elapsed_time:.2f}s: {str(error)}", exc_info=True)
            
            return OperationResult(
                success=False,
                error_message=str(error),
                elapsed_time=elapsed_time,
                stage=stage
            )
    
    def _generate_novella_text(self, custom_prompt: Optional[str] = None) -> OperationResult[str]:
        """
        Generate the narrative text for the video.
        
        Args:
            custom_prompt: Optional custom prompt to use instead of default
            
        Returns:
            OperationResult containing the generated novella text
        """
        novella_prompt = custom_prompt or NOVELLA_PROMPT
        logger.debug(f"Using novella prompt: {novella_prompt[:50]}...")
        
        def operation():
            return self.chat_service.generate_text(novella_prompt)
        
        return self._execute_operation(
            operation, 
            "novella text generation",
            GenerationStage.NOVELLA_TEXT
        )
    
    def _generate_scene_descriptions(self, novella_text: str) -> OperationResult[str]:
        """
        Divide the novella into key scenes with descriptions.
        
        Args:
            novella_text: The complete novella text to divide into scenes
            
        Returns:
            OperationResult containing the scene descriptions
        """
        count_scenes = NUMBER_OF_THE_SCENES
        frames_prompt = FRAMES_PROMPT_TEMPLATE.format(count_scenes=count_scenes, novella_text=novella_text)
        logger.debug(f"Generating scene descriptions for {count_scenes} scenes")
        
        def operation():
            return self.chat_service.generate_text(
                frames_prompt, 
                max_tokens=count_scenes * 100 + 200
            )
        
        return self._execute_operation(
            operation, 
            "scene descriptions generation",
            GenerationStage.SCENE_DESCRIPTIONS
        )

    def _generate_image_web_requests(self, novella_text: str, functions: List[Dict]) -> OperationResult[List[str]]:
        """
        Generate search queries for finding images based on the novella.
        
        Args:
            novella_text: The novella text to base image searches on
            functions: Function definitions for the LLM API call
            
        Returns:
            OperationResult containing a list of search queries
        """
        count_scenes = NUMBER_OF_THE_SCENES
        search_prompt = SEARCH_USER_PROMPT.format(count_scenes=count_scenes, novella_text=novella_text)
        logger.debug(f"Generating queries for {count_scenes} image searches")
        
        def operation():
            # Get response from the API
            response = self.chat_service.generate_text(
                search_prompt,
                functions,
                max_tokens=count_scenes * 50
            )
            
            # Process the response into a standardized list format
            if isinstance(response, list):
                logger.info(f"Received {len(response)} search queries")
                
                # Ensure we have the required number of queries
                if len(response) < count_scenes:
                    logger.warning(f"Received only {len(response)} queries instead of {count_scenes}, duplicating last")
                    last_query = response[-1] if response else "person in noir style city"
                    response.extend([last_query] * (count_scenes - len(response)))
                
                return response[:count_scenes]  # Return exact number of queries
            else:
                # Fallback for text responses
                logger.warning(f"Expected a list of queries, got {type(response)}. Creating generic queries.")
                fallback_queries = []
                
                # Try to split text into lines if it's a string
                if isinstance(response, str):
                    lines = response.strip().split('\n')
                    fallback_queries = [line.strip() for line in lines if line.strip()]
                
                # If no queries could be extracted, create basic ones
                if not fallback_queries:
                    fallback_queries = [f"noir scene {i+1} with dramatic lighting" for i in range(count_scenes)]
                
                # Ensure we have enough queries
                if len(fallback_queries) < count_scenes:
                    last_query = fallback_queries[-1] if fallback_queries else "noir scene with dramatic lighting"
                    fallback_queries.extend([last_query] * (count_scenes - len(fallback_queries)))
                
                logger.debug(f"Fallback queries: {fallback_queries}")
                return fallback_queries[:count_scenes]
        
        return self._execute_operation(
            operation, 
            "image search query generation",
            GenerationStage.IMAGE_SEARCH_QUERIES
        )

    def _download_images_from_web(self, search_queries: List[str]) -> OperationResult[Dict[int, str]]:
        """
        Find and download images from the internet based on search queries.
        
        Args:
            search_queries: List of search queries for finding images
            
        Returns:
            OperationResult containing mapping of scene numbers to downloaded image paths
        """
        def operation():
            count_scenes = NUMBER_OF_THE_SCENES
            os.makedirs(DIRS.scenes, exist_ok=True)
            logger.info(f"Searching and downloading {count_scenes} images from the internet")
            
            downloaded_images = {}
            successful_downloads = 0
            
            for scene, search_query in enumerate(search_queries):
                logger.info(f"Searching for image {scene+1}/{count_scenes}: {search_query[:40]}...")
                
                # Try multiple times to find and download an image
                max_retries = 5
                attempt = 0
                success = False
                
                while attempt < max_retries and not success:
                    attempt += 1
                    if attempt > 1:
                        logger.info(f"Retry attempt {attempt}/{max_retries} for scene {scene+1}")
                        
                    # Find image URL using the search query
                    image_url = self.image_service.find_image_url_by_prompt(search_query)
                    if not image_url:
                        logger.error(f"Failed to find image URL for scene {scene+1}")
                        continue
                    
                    # Download the image
                    image_filename = f"image_{scene+1}.jpg"
                    image_path = os.path.join(DIRS.scenes, image_filename)
                    
                    result = self.image_service.download_image_from_url(image_url, image_path)
                    if result.success:
                        logger.info(f"Downloaded image for scene {scene+1} ({result.size_kb:.2f} KB)")
                        downloaded_images[scene+1] = image_path
                        successful_downloads += 1
                        success = True
                    else:
                        logger.error(f"Failed to download image for scene {scene+1}, attempt {attempt}: {result.error_message}")
                
                if not success:
                    logger.error(f"All attempts to download image for scene {scene+1} failed")
            
            if successful_downloads == 0:
                logger.error("Failed to download any images")
                return None
                
            return downloaded_images
        
        return self._execute_operation(
            operation, 
            "web image download",
            GenerationStage.SCENE_IMAGES
        )

    def _generate_scene_images(self, frames_text: str) -> OperationResult[Dict[int, str]]:
        """
        Generate images for each scene using AI image generation.
        
        Args:
            frames_text: Text descriptions of the scenes
            
        Returns:
            OperationResult containing mapping of scene numbers to generated image paths
        """
        def operation():
            count_scenes = NUMBER_OF_THE_SCENES
            logger.info(f"Generating {count_scenes} scene images")
            
            os.makedirs(DIRS.scenes, exist_ok=True)
            logger.debug(f"Created output directory: {DIRS.scenes}")
            
            generated_images = {}
            success_count = 0
            
            for scene in range(1, count_scenes + 1):
                logger.info(f"Processing scene {scene}/{count_scenes}")
                
                prompt_for_image = (
                    f"Visually define and describe the scene number \"{scene}\" in the text: \"{frames_text}\". "
                    f"Create a brief, vivid, and atmospheric prompt (up to 50 words) for image generation for scene \"{scene}\" "
                    "conveying the full grim aesthetics of noir. "
                    "Focus on the visual details and mood, using the text as general context."
                )
                
                # Generate image prompt
                image_prompt = self.chat_service.generate_text(prompt_for_image, max_tokens=100)
                logger.debug(f"Image prompt for scene {scene}: {image_prompt[:50]}...")

                image_filename = f"image_{scene}.jpg"
                image_path = os.path.join(DIRS.scenes, image_filename)
                
                # Generate the image
                result = self.image_service.generate_image(image_prompt, DIRS.scenes, image_filename)
                
                if result.success:
                    logger.info(f"Image for scene {scene} generated successfully ({result.size_kb:.2f} KB)")
                    generated_images[scene] = image_path
                    success_count += 1
                else:
                    logger.error(f"Failed to generate image for scene {scene}: {result.error_message}")
            
            if success_count == 0:
                logger.error("Failed to generate any scene images")
                return None
                
            return generated_images
        
        return self._execute_operation(
            operation, 
            "scene image generation",
            GenerationStage.SCENE_IMAGES
        )
    
    def _generate_voice_from_text(self, novella_text: str) -> OperationResult[str]:
        """
        Generate audio narration for the novella text.
        
        Args:
            novella_text: The text to convert to audio narration
            
        Returns:
            OperationResult containing the path to the generated audio file
        """
        def operation():
            os.makedirs(DIRS.voice, exist_ok=True)
            logger.debug(f"Created voice output directory: {DIRS.voice}")
            
            logger.info(f"Generating audio narration to {VOICE_FILE_PATH}")
            result = self.audio_service.generate_audio(novella_text, VOICE_FILE_PATH, language='ru')
            
            if result.success:
                logger.info(f"Audio narration generated successfully ({result.file_size_kb:.2f} KB)")
                return VOICE_FILE_PATH
            else:
                logger.error(f"Failed to generate audio narration: {result.message}")
                return None
        
        return self._execute_operation(
            operation, 
            "audio narration generation",
            GenerationStage.VOICE_NARRATION
        )
    
    def _compose_video_with_audio(self, novella_text: str) -> OperationResult[str]:
        """
        Create the final video by combining images and audio.
        
        Args:
            novella_text: The novella text used for scene timing
            
        Returns:
            OperationResult containing the path to the generated video file
        """
        def operation():
            os.makedirs(DIRS.video, exist_ok=True)
            logger.debug(f"Created video output directory: {DIRS.video}")
            
            logger.info(f"Creating final video at {VIDEO_FILE_PATH}")
            
            self.video_editor.create_video(
                DIRS.scenes, 
                VOICE_FILE_PATH, 
                VIDEO_FILE_PATH, 
                novella_text, 
                apply_ken_burns=True,
                apply_fades=False
            )
            
            if os.path.exists(VIDEO_FILE_PATH):
                file_size_mb = os.path.getsize(VIDEO_FILE_PATH) / (1024 * 1024)
                logger.info(f"Final video created successfully: {VIDEO_FILE_PATH} ({file_size_mb:.2f} MB)")
                return VIDEO_FILE_PATH
            else:
                logger.error(f"Video file was not created at expected location: {VIDEO_FILE_PATH}")
                return None
        
        return self._execute_operation(
            operation, 
            "final video creation",
            GenerationStage.VIDEO_COMPOSITION
        )