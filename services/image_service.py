import os
import requests
import re
import logging
from config import (
    OPENAI_API_KEY,
    DEFAULT_IMAGE_SIZE,
    DEFAULT_IMAGES_OUTPUT_DIR,
    DALLE_MODEL,
    TEST_IMAGES
)
from openai import OpenAI

logger = logging.getLogger(__name__)

class ImageService:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info(f"ImageService initialized with DALL-E model: {DALLE_MODEL}, test_mode: {TEST_IMAGES}")

    def generate_image_url(self, prompt: str, size: str = DEFAULT_IMAGE_SIZE, dalle_model=DALLE_MODEL) -> str:
        """
        Generates an image based on a text prompt using DALL-E.
        
        Args:
            prompt: The text prompt to generate the image.
            size: The desired image dimensions (default is "1024x1024").
            
        Returns:
            The URL of the generated image, or None if no URL could be retrieved.
        """
        prompt_truncated = prompt[:30] + "..." if len(prompt) > 30 else prompt
        logger.info(f"Generating image with DALL-E model: {dalle_model}, size: {size}")
        logger.debug(f"Image prompt: {prompt_truncated}")
        
        try:
            response = self.client.images.generate(
                model=dalle_model,
                prompt=prompt,
                n=1,
                size=size
            )
            image_url = response.data[0].url if response.data else None
            
            if image_url:
                logger.info("Image URL successfully generated")
                logger.debug(f"Image URL: {image_url[:50]}...")
                return image_url
            else:
                logger.warning("No image URL returned from DALL-E API")
                return None
        except Exception as e:
            logger.error(f"Error generating image URL: {str(e)}", exc_info=True)
            return None

    def download_image(self, image_url: str, output_path: str) -> bool:
        """
        Downloads an image from the specified URL and saves it to the given path.
        
        Args:
            image_url: The URL of the image to download.
            output_path: The local file path where the image should be saved.
            
        Returns:
            True if the image was successfully saved, otherwise False.
        """
        logger.info(f"Downloading image to {output_path}")
        
        try:
            img_data = requests.get(image_url).content
            with open(output_path, "wb") as f:
                f.write(img_data)
                
            file_size_kb = os.path.getsize(output_path) / 1024
            logger.info(f"Image downloaded successfully ({file_size_kb:.2f} KB)")
            return True
        except Exception as e:
            logger.error(f"Error downloading image: {str(e)}", exc_info=True)
            return False

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitizes a string to be used as a valid filename.
        
        Args:
            filename: The string to sanitize.
            
        Returns:
            A sanitized string that can be used as a filename.
        """
        sanitized = re.sub(r'[\\/*?:"<>|]', "", filename)
        if sanitized != filename:
            logger.debug(f"Filename sanitized: '{filename}' -> '{sanitized}'")
        return sanitized

    def process_prompt(self, prompt: str, output_dir: str, image_filename: str, size: str = DEFAULT_IMAGE_SIZE) -> bool:
        """
        Processes a single prompt with TEST_VIDEO check.
        """
        try:
            sanitized_image_filename = self.sanitize_filename(image_filename)
            output_path = os.path.join(DEFAULT_IMAGES_OUTPUT_DIR, sanitized_image_filename)
            logger.debug(f"Processing prompt for image: {sanitized_image_filename}")
            
            # TEST_IMAGES check
            if TEST_IMAGES and os.path.isfile(output_path):
                logger.info(f"Using existing image: {output_path} [TEST_MODE]")
                return True
                
            image_url = self.generate_image_url(prompt, size)
            if not image_url:
                logger.error("Failed to generate image URL")
                return False
                
            return self.download_image(image_url, output_path)
        except Exception as e:
            logger.error(f"Error processing image prompt: {str(e)}", exc_info=True)
            return False

    def generate_image(self, prompt: str, output_dir: str, image_filename: str, size: str = DEFAULT_IMAGE_SIZE) -> bool:
        """
        Generates an image with TEST_VIDEO awareness.
        """
        logger.info(f"Generating image: {image_filename}")
        
        # Create output directory if it doesn't exist
        sanitized_output_dir = DEFAULT_IMAGES_OUTPUT_DIR
        os.makedirs(sanitized_output_dir, exist_ok=True)
        logger.debug(f"Ensuring output directory exists: {sanitized_output_dir}")
        
        result = self.process_prompt(
            prompt=prompt,
            output_dir=sanitized_output_dir,
            image_filename=image_filename,
            size=size
        )
        
        if result:
            logger.info(f"Image {image_filename} generated successfully")
        else:
            logger.error(f"Failed to generate image {image_filename}")
            
        return result