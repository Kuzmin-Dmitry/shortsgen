"""
Module for generating images using DALL-E.

This module leverages the powerful capabilities of DALL-E to transform your text prompts into creative visuals.
Note: Ensure your API key is kept secure and use detailed prompts for the best results.
"""

import os
import requests
from config import OPENAI_API_KEY, DEFAULT_IMAGE_SIZE, DEFAULT_OUTPUT_DIR, DALLE_MODEL, DEFAULT_IMAGES_OUTPUT_DIR
from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_image_url(prompt: str, size: str = "1024x1024", dalle_model=DALLE_MODEL) -> str:
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
    # Assuming that response.data is a list containing at least one element.
    image_url = response.data[0].url if response.data and len(response.data) > 0 else None
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
        print(f"An error occurred while downloading the image: {e}")
        return False


def process_prompt(prompt: str, output_dir: str, size: str = DEFAULT_IMAGE_SIZE) -> bool:
    """
    Processes a single prompt by performing the following steps:
      1. Generates an image URL from the given text prompt.
      2. Downloads the image from the retrieved URL and saves it locally.
      
    Args:
        prompt: The text prompt to process.
        output_dir: The directory where the image will be saved.
        size: The desired image dimensions (default is "1024x1024").
        
    Returns:
        True if all steps complete successfully, otherwise False.
    """
    print(f"Generating image for prompt: {prompt}")
    try:
        image_url = generate_image_url(prompt, size)
        if image_url:
            image_filename = "generated_image.jpg"
            output_path = os.path.join(output_dir, image_filename)
            return download_image(image_url, output_path)
        else:
            print("Failed to retrieve the image URL.")
            return False
    except Exception as e:
        print(f"An error occurred while generating the image: {e}")
        return False


def generate_image(prompt: str, output_dir: str, size: str = DEFAULT_IMAGE_SIZE) -> bool:
    """
    Generates an image from a text prompt.
    
    The image is saved in the specified directory.
    
    Args:
        prompt: A text prompt.
        output_dir: The directory where the image will be saved.
        size: The desired image dimensions for the generated image (default is "1024x1024").
        
    Returns:
        True if the image was generated and saved successfully, otherwise False.
    """
    return process_prompt(prompt, output_dir, size)
