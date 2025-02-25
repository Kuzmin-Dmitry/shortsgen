"""
Module for generating images using DALL-E with TEST_VIDEO functionality.

When TEST_VIDEO is True in config.py:
- Checks if image already exists in target location
- Skips AI generation if file exists
- Returns True immediately for existing files
"""

import os
import requests
from config import (
    OPENAI_API_KEY,
    DEFAULT_IMAGE_SIZE,
    DEFAULT_IMAGES_OUTPUT_DIR,
    DALLE_MODEL,
    TEST_IMAGES
)
from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_image_url(prompt: str, size: str = DEFAULT_IMAGE_SIZE, dalle_model=DALLE_MODEL) -> str:
    """
    Generates an image based on a text prompt using DALL-E.
    
    Args:
        prompt: The text prompt to generate the image.
        size: The desired image dimensions (default is "1024x1024").
        
    Returns:
        The URL of the generated image, or None if no URL could be retrieved.
    """
    response = client.images.generate(
        model=dalle_model,
        prompt=prompt,
        n=1,
        size=size
    )
    image_url = response.data[0].url if response.data else None
    return image_url

def download_image(image_url: str, output_path: str) -> bool:
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

def process_prompt(prompt: str, output_dir: str, image_filename: str, size: str = DEFAULT_IMAGE_SIZE) -> bool:
    """
    Processes a single prompt with TEST_VIDEO check.
    """
    print(f"Processing prompt: {prompt}")
    try:
        output_path = os.path.join(output_dir, image_filename)
        
        # TEST_IMAGES check
        if TEST_IMAGES and os.path.isfile(output_path):
            print(f"TEST_VIDEO: Using existing image at {output_path}")
            return True
            
        image_url = generate_image_url(prompt, size)
        if not image_url:
            print("Failed to get image URL")
            return False
            
        return download_image(image_url, output_path)
    except Exception as e:
        print(f"Processing error: {e}")
        return False

def generate_image(prompt: str, output_dir: str, image_filename: str, size: str = DEFAULT_IMAGE_SIZE) -> bool:
    """
    Generates an image with TEST_VIDEO awareness.
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    return process_prompt(
        prompt=prompt,
        output_dir=output_dir,
        image_filename=image_filename,
        size=size
    )