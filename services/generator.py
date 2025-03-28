import os
import logging
from services.audio_service import AudioService
from services.video_service import VideoEditor
from services.chat_service import ChatService
from services.image_service import ImageService
from config import (
    FRAMES_PROMPT_TEMPLATE,
    DEFAULT_IMAGES_OUTPUT_DIR, 
    VOICE_FILE_PATH, 
    VIDEO_FILE_PATH, 
    DEFAULT_VOICE_OUTPUT_DIR, 
    DEFAULT_VIDEO_OUTPUT_DIR,
    NOVELLA_PROMPT,
    NUMBER_OF_THE_SCENES,
    LOCAL
)

logger = logging.getLogger(__name__)

class Generator:
    def __init__(self):
        logger.debug("Initializing Generator class")
        self.audio_service = AudioService()
        self.chat_service = ChatService()
        self.image_service = ImageService()
        self.video_editor = VideoEditor()
        logger.debug("Generator class initialized")

    def generate(self):
        """Main method coordinating the video creation process"""
        logger.info("Starting video generation process")
        
        # Sequential execution of all video creation stages
        novella_text = self._generate_novella_text()
        if not novella_text:
            return False
            
        frames_text = self._generate_scene_descriptions(novella_text)
        if not frames_text:
            return False
            
        if not self._generate_scene_images(frames_text):
            return False
            
        if not self._generate_voice_from_text(novella_text):
            return False
            
        if not self._compose_video_with_audio(novella_text):
            return False
            
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
        try:
            result = operation_func()
            if isinstance(result, str):
                logger.info(f"Generated {operation_name}:")
                logger.info(f"{result[:preview_length]}..." if result else "Empty result")
            return result
        except Exception as error:
            logger.error(f"Error during {operation_name}: {error}", exc_info=True)
            return None
    
    def _generate_novella_text(self):
        """Generation of mini-novella text"""
        def operation():
            novella_prompt = NOVELLA_PROMPT
            logger.debug(f"Using novella prompt: {novella_prompt[:40] + '...'}")
            
            # Use unified interface
            logger.info(f"Generating novella text using {'local Gemma' if LOCAL else 'OpenAI'} model")
            return self.chat_service.generate_text(novella_prompt)
                
        return self._execute_operation(operation, "novella text generation")
    
    def _generate_scene_descriptions(self, novella_text):
        """Dividing the novella into key scenes"""
        def operation():
            count_scenes = NUMBER_OF_THE_SCENES
            logger.debug(f"Dividing novella into {count_scenes} scenes")
            frames_prompt = FRAMES_PROMPT_TEMPLATE.format(count_scenes=count_scenes, novella_text=novella_text)
            logger.debug(f"Using frames prompt: {frames_prompt}")
            
            # Use unified interface
            logger.info(f"Generating frames text using {'local Gemma' if LOCAL else 'OpenAI'} model")
            return self.chat_service.generate_text(
                frames_prompt, 
                max_tokens=count_scenes * 100 + 200
            )
        
        return self._execute_operation(operation, "scene descriptions")
    
    def _generate_scene_images(self, frames_text):
        """Generation of images for each scene"""
        def operation():
            count_scenes = NUMBER_OF_THE_SCENES
            logger.info(f"Checking/creating directory: {DEFAULT_IMAGES_OUTPUT_DIR}")
            os.makedirs(DEFAULT_IMAGES_OUTPUT_DIR, exist_ok=True)
            
            for scene in range(1, count_scenes + 1):
                logger.info(f"Generating image for scene: {scene}")
                prompt_for_image = (
                    f"Visually define and describe the scene number \"{scene}\" in the text: \"{frames_text}\". "
                    f"Create a brief, vivid, and atmospheric prompt (up to 50 words) for image generation for scene \"{scene}\" "
                    "conveying the full grim aesthetics of noir. "
                    "Focus on the visual details and mood, using the text as general context."
                )
                
                logger.debug(f"Using prompt for image scene {scene}: {prompt_for_image[:40]}")
                # Use unified interface
                logger.info(f"Generating image prompt for scene {scene}")
                image_prompt = self.chat_service.generate_text(prompt_for_image, max_tokens=100)

                logger.info(f"Generating image for prompt: {image_prompt[:40] + '...'}")
                image_filename = f"image_{scene}.jpg"
                logger.debug(f"Saving image as: {image_filename}")
                
                if not self.image_service.generate_image(image_prompt, DEFAULT_IMAGES_OUTPUT_DIR, image_filename):
                    logger.error(f"Error: Image generation failed for scene {scene}")
                    return False
            
            return True
        
        return self._execute_operation(operation, "scene image generation")
    
    def _generate_voice_from_text(self, novella_text):
        """Generation of audio narrative for the entire novella"""
        def operation():
            logger.info(f"Checking/creating directory: {DEFAULT_VOICE_OUTPUT_DIR}")
            os.makedirs(DEFAULT_VOICE_OUTPUT_DIR, exist_ok=True)
            
            logger.info("Generating audio narration")
            self.audio_service.generate_audio(novella_text, VOICE_FILE_PATH, language='ru')
            logger.info("Audio narration generated successfully")
            return True
        
        return self._execute_operation(operation, "audio narration generation")
    
    def _compose_video_with_audio(self, novella_text):
        """Creation of the final video combining images and audio"""
        def operation():
            logger.info(f"Checking/creating directory: {DEFAULT_VIDEO_OUTPUT_DIR}")
            os.makedirs(DEFAULT_VIDEO_OUTPUT_DIR, exist_ok=True)
            
            logger.info("Creating video with transitions")
            self.video_editor.create_video_with_transitions(
                DEFAULT_IMAGES_OUTPUT_DIR, 
                VOICE_FILE_PATH, 
                VIDEO_FILE_PATH, 
                novella_text, 
                apply_fades=False
            )
            logger.info("Generator created successfully")
            return True
        
        return self._execute_operation(operation, "final video creation")
