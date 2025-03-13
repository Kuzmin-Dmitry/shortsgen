import os
import requests
import re
from config import (
    OPENAI_API_KEY,
    DEFAULT_IMAGE_SIZE,
    DEFAULT_IMAGES_OUTPUT_DIR,
    DALLE_MODEL,
    TEST_IMAGES
)
from openai import OpenAI

class ImageService:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def generate_image_url(self, prompt: str, size: str = DEFAULT_IMAGE_SIZE, dalle_model=DALLE_MODEL) -> str:
        """
        Generates an image based on a text prompt using DALL-E.
        
        Args:
            prompt: The text prompt to generate the image.
            size: The desired image dimensions (default is "1024x1024").
            
        Returns:
            The URL of the generated image, or None if no URL could be retrieved.
        """
        response = self.client.images.generate(
            model=dalle_model,
            prompt=prompt,
            n=1,
            size=size
        )
        image_url = response.data[0].url if response.data else None
        return image_url

    def download_image(self, image_url: str, output_path: str) -> bool:
        """
        Downloads an image from the specified URL and saves it to the given path.
        
        Args:
            image_url: The URL of the image to download.
            output_path: The local file path where the image should be saved.
            
        Returns:
            True if the image was successfully saved, otherwise False.
        """
        try:
            print(f"Downloading image from URL: {image_url}")
            img_data = requests.get(image_url).content
            with open(output_path, "wb") as f:
                f.write(img_data)
            print(f"Image saved: {output_path}")
            return True
        except Exception as e:
            print(f"Download error: {e}")
            return False

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitizes a string to be used as a valid filename.
        
        Args:
            filename: The string to sanitize.
            
        Returns:
            A sanitized string that can be used as a filename.
        """
        return re.sub(r'[\\/*?:"<>|]', "", filename)

    def process_prompt(self, prompt: str, output_dir: str, image_filename: str, size: str = DEFAULT_IMAGE_SIZE) -> bool:
        """
        Processes a single prompt with TEST_VIDEO check.
        """
        print(f"Processing prompt: {prompt}")
        try:
            sanitized_output_dir = self.sanitize_filename(output_dir)
            sanitized_image_filename = self.sanitize_filename(image_filename)
            output_path = os.path.join(sanitized_output_dir, sanitized_image_filename)
            
            # TEST_IMAGES check
            if TEST_IMAGES and os.path.isfile(output_path):
                print(f"TEST_VIDEO: Using existing image at {output_path}")
                return True
                
            image_url = self.generate_image_url(prompt, size)
            if not image_url:
                print("Failed to get image URL")
                return False
                
            return self.download_image(image_url, output_path)
        except Exception as e:
            print(f"Processing error: {e}")
            return False

    def generate_image(self, prompt: str, output_dir: str, image_filename: str, size: str = DEFAULT_IMAGE_SIZE) -> bool:
        """
        Generates an image with TEST_VIDEO awareness.
        """
        # Create output directory if it doesn't exist
        sanitized_output_dir = self.sanitize_filename(output_dir)
        os.makedirs(sanitized_output_dir, exist_ok=True)
        
        return self.process_prompt(
            prompt=prompt,
            output_dir=sanitized_output_dir,
            image_filename=image_filename,
            size=size
        )