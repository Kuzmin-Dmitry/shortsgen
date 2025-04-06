import os
import logging
import time
import yaml
from services.audio_service import AudioService
from services.video_service import VideoEditor
from services.chat_service import ChatService
from services.image_service import ImageService
from utils import file_utils
from config import (
    FRAMES_PROMPT_TEMPLATE,
    DEFAULT_SCENES_OUTPUT_DIR, 
    VOICE_FILE_PATH, 
    VIDEO_FILE_PATH, 
    DEFAULT_VOICE_OUTPUT_DIR, 
    DEFAULT_VIDEO_OUTPUT_DIR,
    NOVELLA_PROMPT,
    NUMBER_OF_THE_SCENES,
    SEARCH_REQUEST_TEMPLATE,
    DEFAULT_SCENES_OUTPUT_DIR,
    LOCAL
)

logger = logging.getLogger(__name__)

class Generator:
    def __init__(self):
        self.audio_service = AudioService()
        self.chat_service = ChatService()
        self.image_service = ImageService()
        self.video_editor = VideoEditor()
        logger.info("Generator initialized with all required services")

    def find_and_generate(self):
        """Method to find related images from the internet and generate a video"""
        logger.info("Starting the find and generate process")
        start_time = time.time()

        # Sequential execution of all video creation stages
        novella_text = self._generate_novella_text()
        if not novella_text:
            logger.error("Video generation aborted: Failed to generate novella text")
            return False

        image_requests_text = self._generate_image_requests(novella_text)
        if not image_requests_text:
            logger.error("Video generation aborted: Failed to generate scene descriptions")
            return False
    
        # Find related images from the internet and download them
        os.makedirs(DEFAULT_SCENES_OUTPUT_DIR, exist_ok=True)
        logger.info(f"Searching and downloading {NUMBER_OF_THE_SCENES} images from the internet")
        
        successful_downloads = 0
        for scene in range(NUMBER_OF_THE_SCENES):
            search_query = image_requests_text[scene]
            logger.info(f"Searching for image {scene}/{NUMBER_OF_THE_SCENES}: {search_query[:40]}...")
            
            # Try up to 3 times to find and download an image
            max_retries = 5
            attempt = 0
            success = False
            
            while attempt < max_retries and not success:
                attempt += 1
                if attempt > 1:
                    logger.info(f"Retry attempt {attempt}/{max_retries} for scene {scene}")
                    
                # Find image URL using the search query
                image_url = self.image_service.find_image_url_by_prompt(search_query)
                if not image_url:
                    logger.error(f"Failed to find image URL for scene {scene}")
                    continue
                
                # Download the image
                image_filename = f"image_{scene}.jpg"
                image_path = os.path.join(DEFAULT_SCENES_OUTPUT_DIR, image_filename)
                
                if self.image_service.download_image_from_url(image_url, image_path):
                    logger.info(f"Downloaded image for scene {scene}")
                    successful_downloads += 1
                    success = True
                else:
                    logger.error(f"Failed to download image for scene {scene}, attempt {attempt}")
            
            if not success:
                logger.error(f"All attempts to download image for scene {scene} failed")
        
        if successful_downloads == 0:
            logger.error("Video generation aborted: Failed to download any images")
            return False
        
        if not self._generate_voice_from_text(novella_text):
            logger.error("Video generation aborted: Failed to generate voice narration")
            return False
            
        if not self._compose_video_with_audio(novella_text):
            logger.error("Video generation aborted: Failed to compose final video")
            return False
        
        elapsed_time = time.time() - start_time
        logger.info(f"Find and generate process completed successfully in {elapsed_time:.2f} seconds")
        return True

    def generate(self):
        """Main method coordinating the video creation process"""
        logger.info("Starting video generation process")
        start_time = time.time()
        
        # Sequential execution of all video creation stages
        novella_text = self._generate_novella_text()
        if not novella_text:
            logger.error("Video generation aborted: Failed to generate novella text")
            return False
            
        frames_text = self._generate_scene_descriptions(novella_text)
        if not frames_text:
            logger.error("Video generation aborted: Failed to generate scene descriptions")
            return False
            
        if not self._generate_scene_images(frames_text):
            logger.error("Video generation aborted: Failed to generate scene images")
            return False
            
        if not self._generate_voice_from_text(novella_text):
            logger.error("Video generation aborted: Failed to generate voice narration")
            return False
            
        if not self._compose_video_with_audio(novella_text):
            logger.error("Video generation aborted: Failed to compose final video")
            return False
        
        elapsed_time = time.time() - start_time
        logger.info(f"Video generation completed successfully in {elapsed_time:.2f} seconds")
        return True
    
    def _execute_operation(self, operation_func, operation_name, preview_length=40):
        """
        Executes an operation with error handling and result logging
        
        Args:
            operation_func: Function performing the operation
            operation_name: Operation name for logging
            preview_length: Length of result preview
            
        Returns:
            Result of operation_func execution or None in case of error
        """
        logger.info(f"Starting operation: {operation_name}")
        start_time = time.time()
        
        try:
            result = operation_func()
            elapsed_time = time.time() - start_time
            
            if result:
                if isinstance(result, str):
                    result_preview = (result[:preview_length] + "...") if len(result) > preview_length else result
                    logger.info(f"Operation '{operation_name}' completed successfully in {elapsed_time:.2f}s")
                    logger.debug(f"Result preview: {result_preview}")
                else:
                    logger.info(f"Operation '{operation_name}' completed successfully in {elapsed_time:.2f}s")
            else:
                logger.warning(f"Operation '{operation_name}' returned empty result in {elapsed_time:.2f}s")
                
            return result
        except Exception as error:
            elapsed_time = time.time() - start_time
            logger.error(f"Operation '{operation_name}' failed after {elapsed_time:.2f}s: {str(error)}", exc_info=True)
            return None
    
    def _generate_novella_text(self):
        """Generation of mini-novella text"""
        def operation():
            novella_prompt = NOVELLA_PROMPT
            logger.debug(f"Using novella prompt: {novella_prompt[:50]}...")
            
            # Use unified interface
            return self.chat_service.generate_text(novella_prompt)
                
        return self._execute_operation(operation, "novella text generation")
    
    def _generate_scene_descriptions(self, novella_text):
        """Dividing the novella into key scenes"""
        def operation():
            count_scenes = NUMBER_OF_THE_SCENES
            logger.debug(f"Generating scene descriptions for {count_scenes} scenes")
            
            frames_prompt = FRAMES_PROMPT_TEMPLATE.format(count_scenes=count_scenes, novella_text=novella_text)
            
            # Use unified interface
            return self.chat_service.generate_text(
                frames_prompt, 
                max_tokens=count_scenes * 100 + 200
            )
        
        return self._execute_operation(operation, "scene descriptions")

    def _generate_image_requests(self, novella_text):
        """Dividing the novella into key scenes and generating search queries"""
        def operation():
            count_scenes = NUMBER_OF_THE_SCENES
            logger.debug(f"Generating descriptions for web search request to find {count_scenes} scenes")
            
            search_prompt = SEARCH_REQUEST_TEMPLATE.format(count_scenes=count_scenes, novella_text=novella_text)
            
            # Use unified interface to get YAML response
            yaml_response = self.chat_service.generate_text(
                search_prompt,
                max_tokens=count_scenes * 30 + 100
            )
            
            # Parse YAML to extract the list of image search queries
            try:
                parsed_yaml = yaml.safe_load(yaml_response)
                if not parsed_yaml or 'image_search_queries' not in parsed_yaml:
                    logger.error("Invalid YAML response: missing 'image_search_queries' key")
                    return None
                
                search_queries = parsed_yaml['image_search_queries']
                logger.debug(f"Successfully parsed {len(search_queries)} image search queries")
                return search_queries
                
            except yaml.YAMLError as e:
                logger.error(f"Failed to parse YAML response: {str(e)}")
                logger.debug(f"Raw YAML response: {yaml_response}")
                return None

        return self._execute_operation(operation, "web request descriptions")

    def _generate_scene_images(self, frames_text):
        """Generation of images for each scene"""
        def operation():
            count_scenes = NUMBER_OF_THE_SCENES
            logger.info(f"Generating {count_scenes} scene images")
            
            os.makedirs(DEFAULT_SCENES_OUTPUT_DIR, exist_ok=True)
            logger.debug(f"Created output directory: {DEFAULT_SCENES_OUTPUT_DIR}")
            
            for scene in range(1, count_scenes + 1):
                logger.info(f"Processing scene {scene}/{count_scenes}")
                
                prompt_for_image = (
                    f"Visually define and describe the scene number \"{scene}\" in the text: \"{frames_text}\". "
                    f"Create a brief, vivid, and atmospheric prompt (up to 50 words) for image generation for scene \"{scene}\" "
                    "conveying the full grim aesthetics of noir. "
                    "Focus on the visual details and mood, using the text as general context."
                )
                
                # Use unified interface
                image_prompt = self.chat_service.generate_text(prompt_for_image, max_tokens=100)
                logger.debug(f"Image prompt for scene {scene}: {image_prompt[:50]}...")

                image_filename = f"image_{scene}.jpg"
                
                if not self.image_service.generate_image(image_prompt, DEFAULT_SCENES_OUTPUT_DIR, image_filename):
                    logger.error(f"Failed to generate image for scene {scene}")
                    return False
                
                logger.info(f"Image for scene {scene} generated successfully")
            
            return True
        
        return self._execute_operation(operation, "scene image generation")
    
    def _generate_voice_from_text(self, novella_text):
        """Generation of audio narrative for the entire novella"""
        def operation():
            os.makedirs(DEFAULT_VOICE_OUTPUT_DIR, exist_ok=True)
            logger.debug(f"Created voice output directory: {DEFAULT_VOICE_OUTPUT_DIR}")
            
            logger.info(f"Generating audio narration to {VOICE_FILE_PATH}")
            result = self.audio_service.generate_audio(novella_text, VOICE_FILE_PATH, language='ru')
            
            if result:
                logger.info("Audio narration generated successfully")
            else:
                logger.error("Failed to generate audio narration")
                
            return result
        
        return self._execute_operation(operation, "audio narration generation")
    
    def _compose_video_with_audio(self, novella_text):
        """Creation of the final video combining images and audio"""
        def operation():
            os.makedirs(DEFAULT_VIDEO_OUTPUT_DIR, exist_ok=True)
            logger.debug(f"Created video output directory: {DEFAULT_VIDEO_OUTPUT_DIR}")
            
            logger.info(f"Creating final video at {VIDEO_FILE_PATH}")
            
            self.video_editor.create_video_with_transitions(
                DEFAULT_SCENES_OUTPUT_DIR, 
                VOICE_FILE_PATH, 
                VIDEO_FILE_PATH, 
                novella_text, 
                apply_fades=False
            )
            
            if os.path.exists(VIDEO_FILE_PATH):
                file_size_mb = os.path.getsize(VIDEO_FILE_PATH) / (1024 * 1024)
                logger.info(f"Final video created successfully: {VIDEO_FILE_PATH} ({file_size_mb:.2f} MB)")
                return True
            else:
                logger.error(f"Video file was not created at expected location: {VIDEO_FILE_PATH}")
                return False
        
        return self._execute_operation(operation, "final video creation")
