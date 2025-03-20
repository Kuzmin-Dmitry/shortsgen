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

class Video:
    def __init__(self):
        logger.debug("Initializing Video class")  # Отладочное сообщение при инициализации класса
        self.audio_service = AudioService()
        self.chat_service = ChatService()
        self.image_service = ImageService()
        self.video_editor = VideoEditor()
        logger.debug("Video class initialized")

    def generate(self):
        logger.info("Starting video generation process")  # Общее сообщение о начале процесса
        # Step 1: Generate a mini-novel scenario using ChatGPT.
        novella_prompt = NOVELLA_PROMPT
        logger.debug(f"Using novella prompt: {novella_prompt}")  # Логирование используемого промпта
        if LOCAL:
            logger.info("Generating novella text using local Gemma model")
            novella_text = self.chat_service.generate_chatgpt_text_gemma3(novella_prompt)
        else:   
            logger.info("Generating novella text using OpenAI model")
            novella_text = self.chat_service.generate_chatgpt_text_openai(novella_prompt)
        logger.info("Generated novella scenario:")
        logger.info(novella_text)
        logger.info("\n" + "=" * 80 + "\n")
        
        # Step 2: Divide the scenario into key scenes.
        count_scenes = NUMBER_OF_THE_SCENES  # Expected number of scenes
        logger.debug(f"Dividing novella into {count_scenes} scenes")  # Логирование количества сцен
        frames_prompt = FRAMES_PROMPT_TEMPLATE.format(count_scenes=count_scenes, novella_text=novella_text)
        logger.debug(f"Using frames prompt: {frames_prompt}")  # Логирование используемого промпта
        if LOCAL:
            logger.info("Generating frames text using local Gemma model")
            frames_text = self.chat_service.generate_chatgpt_text_gemma3(frames_prompt, max_tokens=count_scenes * 100 + 200)
        else:
            logger.info("Generating frames text using OpenAI model")
            frames_text = self.chat_service.generate_chatgpt_text_openai(frames_prompt, max_tokens=count_scenes * 100 + 200)

        logger.info("Generated scene descriptions:")
        logger.info(frames_text)
        logger.info("\n" + "=" * 80 + "\n")

        logger.info(f"Checking/creating directory: {DEFAULT_IMAGES_OUTPUT_DIR}")
        os.makedirs(DEFAULT_IMAGES_OUTPUT_DIR, exist_ok=True)

        # Step 3: Generate images for each scene.
        for scene in range(1, count_scenes + 1):
            logger.info(f"Generating image for scene {scene}")  # Логирование номера текущей сцены
            prompt_for_image = (
                f"Visually define and describe the scene number \"{scene}\" in the text: \"{frames_text}\". "
                f"Create a brief, vivid, and atmospheric prompt (up to 50 words) for image generation for scene \"{scene}\" "
                "conveying the full grim aesthetics of noir. "
                "Focus on the visual details and mood, using the text as general context."
            )
            logger.debug(f"Using prompt for image scene {scene}: {prompt_for_image}")  # Логирование промпта для изображения
            if LOCAL:
                logger.info(f"Generating image prompt for scene {scene} using local Gemma model")
                image_prompt = self.chat_service.generate_chatgpt_text_gemma3(prompt_for_image, max_tokens=100)
            else:   
                logger.info(f"Generating image prompt for scene {scene} using OpenAI model")
                image_prompt = self.chat_service.generate_chatgpt_text_openai(prompt_for_image, max_tokens=100)

            logger.info(f"Generating image for prompt: {image_prompt}")
            image_filename = f"image_{scene}.jpg"
            logger.debug(f"Saving image as: {image_filename}")  # Логирование имени файла
            image_gen_result = self.image_service.generate_image(image_prompt, DEFAULT_IMAGES_OUTPUT_DIR, image_filename)
            if not image_gen_result:
                logger.error(f"Error: Image generation failed for scene {scene}. Exiting.")
                return

        # Step 5: Generate audio narration for the entire novella scenario.
        logger.info(f"Checking/creating directory: {DEFAULT_VOICE_OUTPUT_DIR}")
        os.makedirs(DEFAULT_VOICE_OUTPUT_DIR, exist_ok=True)

        try:
            logger.info("Generating audio narration")  # Сообщение о начале генерации аудио
            self.audio_service.generate_audio(novella_text, VOICE_FILE_PATH, language='ru')
            logger.info("Audio narration generated successfully")  # Сообщение об успешной генерации аудио
        except Exception as error:
            logger.error(f"Error during voice creation: {error}", exc_info=True)
            return

        # Step 6: Create the video by combining the generated images and audio.
        logger.info(f"Checking/creating directory: {DEFAULT_VIDEO_OUTPUT_DIR}")
        os.makedirs(DEFAULT_VIDEO_OUTPUT_DIR, exist_ok=True)

        try:
            logger.info("Creating video with transitions")  # Сообщение о начале создания видео
            self.video_editor.create_video_with_transitions(DEFAULT_IMAGES_OUTPUT_DIR, VOICE_FILE_PATH, VIDEO_FILE_PATH, novella_text, apply_fades=False)
            logger.info("Video created successfully")  # Сообщение об успешном создании видео
        except Exception as error:
            logger.error(f"Error during video creation: {error}", exc_info=True)
            return

        logger.info(f"Final video saved at: {VIDEO_FILE_PATH}")
        logger.info("Ending video generation process")  # Общее сообщение об окончании процесса
