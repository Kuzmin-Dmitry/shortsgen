import os
import requests
import re
import time
import logging
from typing import Union, List
from config import (
    OPENAI_API_KEY,
    DEFAULT_IMAGE_SIZE,
    DEFAULT_SCENES_OUTPUT_DIR,
    DALLE_MODEL,
    TEST_SCENES
)
from openai import OpenAI
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

class ImageService:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info(f"ImageService initialized with DALL-E model: {DALLE_MODEL}, test_mode: {TEST_SCENES}")

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

    def download_image_from_llm(self, image_url: str, output_path: str) -> bool:
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

    @classmethod
    def find_image_url_by_prompt(cls, prompt: str) -> str:
        """
        Finds a related image based on a single prompt using DuckDuckGo search.
        
        Args:
            prompt: The text prompt to search for related images.
            
        Returns:
            A URL of a related image, or empty string if none found.
        """
        prompt_truncated = prompt[:30] + "..." if len(prompt) > 30 else prompt
        logger.info(f"Searching for related image for prompt: {prompt_truncated}...")
        
        # Retry parameters
        max_results = 1
        max_retries = 3
        retry_count = 0
        base_delay = 2
        
        while retry_count < max_retries:
            try:
                """DuckDuckGo images search. Query params: https://duckduckgo.com/params.

                Args:
                    keywords: keywords for query.
                    region: wt-wt, us-en, uk-en, ru-ru, etc. Defaults to "wt-wt".
                    safesearch: on, moderate, off. Defaults to "moderate".
                    timelimit: Day, Week, Month, Year. Defaults to None.
                    size: Small, Medium, Large, Wallpaper. Defaults to None.
                    color: color, Monochrome, Red, Orange, Yellow, Green, Blue,
                        Purple, Pink, Brown, Black, Gray, Teal, White. Defaults to None.
                    type_image: photo, clipart, gif, transparent, line.
                        Defaults to None.
                    layout: Square, Tall, Wide. Defaults to None.
                    license_image: any (All Creative Commons), Public (PublicDomain),
                        Share (Free to Share and Use), ShareCommercially (Free to Share and Use Commercially),
                        Modify (Free to Modify, Share, and Use), ModifyCommercially (Free to Modify, Share, and
                        Use Commercially). Defaults to None.
                    max_results: max number of results. If None, returns results only from the first response. Defaults to None.

                Returns:
                    List of dictionaries with images search results.
                """
                ddgs = DDGS()
                results = list(ddgs.images(
                    prompt, 
                    max_results=max_results,
                    safesearch="on"
                ))
                
                # Extract first valid image URL
                if results:
                    image_url = results[0]["image"]
                    logger.info(f"Found image for prompt: {prompt_truncated}")
                    return image_url
                else:
                    logger.warning(f"No images found for prompt '{prompt_truncated}' (attempt {retry_count+1}/{max_retries})")
                    
            except Exception as e:
                logger.error(f"Error searching for image with prompt '{prompt_truncated}' (attempt {retry_count+1}/{max_retries}): {str(e)}")
            
            # If we need to retry
            retry_count += 1
            if retry_count < max_retries:
                wait_time = base_delay * (2 ** (retry_count - 1))  # Exponential backoff
                logger.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
        
        logger.warning(f"No image found after {max_retries} attempts")
        return ""
    
    @classmethod
    def download_image_from_url(cls, image_url: str, output_path: str) -> bool:
        """
        Downloads an image from a specified URL and saves it to the given path.
        
        Args:
            image_url: The URL of the image to download.
            output_path: The file path where the image should be saved.
            
        Returns:
            bool: True if the download was successful, False otherwise
        """
        try:
            logger.info(f"Downloading image from {image_url} to {output_path}")
            
            # Ensure the directory exists
            directory = output_path
            if os.path.splitext(output_path)[1]:  # Check if path has a file extension
                directory = os.path.dirname(output_path)
            os.makedirs(directory, exist_ok=True)
            
            # Download the image
            response = requests.get(image_url, stream=True, timeout=30)
            response.raise_for_status()  # Check if the request was successful
            
            # Save the image to the specified path
            with open(output_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
                    
            logger.info(f"Successfully downloaded image to {output_path}")
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
            output_path = os.path.join(DEFAULT_SCENES_OUTPUT_DIR, sanitized_image_filename)
            logger.debug(f"Processing prompt for image: {sanitized_image_filename}")
            
            # TEST_SCENES check
            if TEST_SCENES and os.path.isfile(output_path):
                logger.info(f"Using existing image: {output_path} [TEST_MODE]")
                return True
                
            image_url = self.generate_image_url(prompt, size)
            if not image_url:
                logger.error("Failed to generate image URL")
                return False
                
            return self.download_image_from_llm(image_url, output_path)
        except Exception as e:
            logger.error(f"Error processing image prompt: {str(e)}", exc_info=True)
            return False

    def generate_image(self, prompt: str, output_dir: str, image_filename: str, size: str = DEFAULT_IMAGE_SIZE) -> bool:
        """
        Generates an image with TEST_VIDEO awareness.
        """
        logger.info(f"Generating image: {image_filename}")
        
        # Create output directory if it doesn't exist
        sanitized_output_dir = DEFAULT_SCENES_OUTPUT_DIR
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