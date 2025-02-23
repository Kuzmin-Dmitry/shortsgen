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
from services.image_service import generate_image
from config import (
    DEFAULT_IMAGES_OUTPUT_DIR, 
    VOICE_FILE_PATH, 
    VIDEO_FILE_PATH, 
    DEFAULT_VOICE_OUTPUT_DIR, 
    DEFAULT_VIDEO_OUTPUT_DIR
)

def main():
    # Step 1: Generate a mini-novel scenario using ChatGPT.
    novella_prompt = (
        "Create a mini-novel (up to 200 words) in the style of Sin City, where dark noir "
        "and striking visual contrasts combine with top-notch meme quotes. "
        "Let the story unfold on shadowy streets, where every dialogue is a burst of biting sarcasm "
        "or a palette of irony, reflecting the reality we live in. "
        "The characters, composed of cold-blooded resolve and daring courage, speak in the language of zoomers and alphas, "
        "where memes are a means of communication and everything around is a game of manipulation. "
        "Add unexpected twists and sharp phrases so that every line makes you think: "
        "\"Oh, this isn’t trash and isn’t suffocating! Like and subscribe, damn it!\"."
    )
    novella_text = generate_chatgpt_text(novella_prompt, max_tokens=600)

    print("Generated novella scenario:")
    print(novella_text)
    print("\n" + "=" * 80 + "\n")

    # Step 2: Divide the scenario into key scenes.
    count_scenes = 6  # Expected number of scenes
    frames_prompt = (
        f"Divide the following text into {count_scenes} iconic and striking scenes. "
        "Each frame should have a minimalist style with vivid comic-style visuals. "
        "For each scene, create a brief description (up to 50 words) that conveys the atmosphere, visual details, and mood.\n\n"
        f"Text: {novella_text}\n"
        "Add a General description of the environment as the fifth scene for creating a drawing, up to 100 words long."
    )
    frames_text = generate_chatgpt_text(frames_prompt, max_tokens=count_scenes * 100 + 200)

    print("Generated scene descriptions:")
    print(frames_text)
    print("\n" + "=" * 80 + "\n")

    print(f"Checking/creating directory: {DEFAULT_IMAGES_OUTPUT_DIR}")
    os.makedirs(DEFAULT_IMAGES_OUTPUT_DIR, exist_ok=True)

    # Step 3: Generate images for each scene.
    for scene in range(1, count_scenes + 1):
        prompt_for_image = (
            f"Visually define and describe the scene number \"{scene}\" in the text: \"{frames_text}\". "
            f"Create a brief, vivid, and atmospheric prompt (up to 50 words) for image generation for scene \"{scene}\" "
            "conveying the full grim aesthetics of noir. "
            "Focus on the visual details and mood, using the text as general context."
        )
        image_prompt = generate_chatgpt_text(prompt_for_image, max_tokens=100)

        print(f"Generating image for prompt: {image_prompt}")
        image_filename = f"image_{scene}.jpg"
        image_gen_result = generate_image(image_prompt, DEFAULT_IMAGES_OUTPUT_DIR, image_filename)
        if not image_gen_result:
            print(f"Error: Image generation failed for scene {scene}. Exiting.")
            return

    # Step 5: Generate audio narration for the entire novella scenario.
    print(f"Checking/creating directory: {DEFAULT_VOICE_OUTPUT_DIR}")
    os.makedirs(DEFAULT_VOICE_OUTPUT_DIR, exist_ok=True)

    try:
        generate_audio(novella_text, VOICE_FILE_PATH, language='ru')
    except Exception as error:
        print(f"Error during voice creation: {error}")
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
