#!/usr/bin/env python3
"""
Main script orchestrating the entire video generation process:
1. Audio generation (narration of the scenario)
2. Video creation based on generated images and audio

This script dynamically generates a mini-novel scenario, divides it into key scenes,
refines each scene into an image generation prompt, synthesizes images and audio,
and finally combines them into a video.
"""

import os
from services.audio_service import generate_audio
from services.video_service import create_video_with_transitions
from services.chat_service import generate_chatgpt_text
from services.image_service import generate_images
from config import DEFAULT_IMAGES_OUTPUT_DIR, VOICE_FILE_PATH, VIDEO_FILE_PATH, DEFAULT_VOICE_OUTPUT_DIR, DEFAULT_VIDEO_OUTPUT_DIR

def main():
    # Step 1: Generate a mini-novel scenario using ChatGPT.
    # The prompt instructs the model to create a mini-novel (up to 100 words)
    # in the style of Sin City with a blend of noir aesthetics and meme-inspired quotes.
    novella_prompt = (
        "Create a mini-novel (up to 100 words) in the style of Sin City, where dark noir "
        "and striking visual contrasts combine with top-notch meme quotes. "
        "Let the story unfold on shadowy streets, where every dialogue is a burst of biting sarcasm "
        "or a palette of irony, reflecting the reality we live in. "
        "The characters, composed of cold-blooded resolve and daring courage, speak in the language of zoomers and alphas, "
        "where memes are a means of communication and everything around is a game of manipulation. "
        "Add unexpected twists and sharp phrases so that every line makes you think: "
        "\"Oh, this isn’t trash and isn’t suffocating! Like and subscribe, damn it!\""
    )
    novella_responses = generate_chatgpt_text(novella_prompt, max_tokens=300, count=1)
    novella_text = novella_responses[0]

    print("Generated novella scenario:")
    print(novella_text)
    print("\n" + "=" * 80 + "\n")

    # Step 2: Divide the scenario into key scenes.
    # The model is prompted to split the text into a specified number of iconic scenes,
    # each with a brief (up to 50 words) description conveying atmosphere, visual details, and mood.
    count_scenes = 4  # Expected number of scenes
    frames_prompt = (
        f"Divide the following text into {count_scenes} iconic and striking scenes. "
        "Each frame should have a minimalist style with vivid comic-style visuals. "
        "For each scene, create a brief description (up to 50 words) that conveys the atmosphere, visual details, and mood.\n\n"
        f"Text: {novella_text}"
    )
    frames_responses = generate_chatgpt_text(frames_prompt, max_tokens=500, count=1)
    frames_text = frames_responses[0]

    print("Generated scene descriptions:")
    print(frames_text)
    print("\n" + "=" * 80 + "\n")

    # Attempt to split the generated text into individual scenes.
    scenes = []
    # Split by double newlines to avoid breaking titles and descriptions.
    for block in frames_text.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        # If a block starts with a header marker, extract the content after the colon.
        if block.startswith("###"):
            if ":" in block:
                scene_desc = block.split(":", 1)[1].strip()
                scenes.append(scene_desc)
            else:
                scenes.append(block)
        else:
            scenes.append(block)

    # If, for any reason, the number of scenes is less than expected, use the entire text as one scene.
    if len(scenes) < count_scenes:
        scenes = [frames_text]

    # Step 3: Refine the prompt for image generation for each scene.
    image_prompts = []
    for scene in scenes:
        prompt_for_image = (
            f"Visually describe the scene: \"{scene}\". "
            "Create a brief, vivid, and atmospheric prompt (up to 50 words) for image generation, "
            "conveying the full grim aesthetics of noir."
        )
        image_response = generate_chatgpt_text(prompt_for_image, max_tokens=100, count=1)
        image_prompts.append(image_response[0])

    print("Generated image prompts for each scene:")
    for i, prompt in enumerate(image_prompts, start=1):
        print(f"Scene {i}: {prompt}")
    print("\n" + "=" * 80 + "\n")

    # Step 4: Prepare directories and generate images.
    # Create a temporary directory for storing the generated images.
    print(f"Checking/creating directory: {DEFAULT_IMAGES_OUTPUT_DIR}")
    os.makedirs(DEFAULT_IMAGES_OUTPUT_DIR, exist_ok=True)

    # Generate images based on the refined prompts.
    # image_gen_results = generate_images(image_prompts, DEFAULT_IMAGES_OUTPUT_DIR)
    # if not all(image_gen_results):
    #     print("Error: Some images failed to generate. Exiting.")
    #     return

    # Step 5: Generate audio narration for the entire novella scenario.
    # Note: The same novella text is used to generate the audio narration.
    print(f"Checking/creating directory: {DEFAULT_VOICE_OUTPUT_DIR}")
    os.makedirs(DEFAULT_VOICE_OUTPUT_DIR, exist_ok=True)

    if not generate_audio(novella_text, VOICE_FILE_PATH, language='ru'):
        print("Error: Audio generation failed. Exiting.")
        return

    # Step 6: Create the video by combining the generated images and audio.
    print(f"Checking/creating directory: {DEFAULT_VIDEO_OUTPUT_DIR}")
    os.makedirs(DEFAULT_VIDEO_OUTPUT_DIR, exist_ok=True)

    try:
        create_video_with_transitions(DEFAULT_IMAGES_OUTPUT_DIR, VOICE_FILE_PATH, VIDEO_FILE_PATH, apply_fades=False)
    except Exception as error:
        print(f"Error during video creation: {error}")
        return

    print("All stages completed successfully!")
    print(f"Final video saved at: {VIDEO_FILE_PATH}")

if __name__ == "__main__":
    main()
