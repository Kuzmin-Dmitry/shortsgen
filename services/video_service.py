"""
Module for creating the final video from images and an audio track.
Uses MoviePy to compile clips and add effects.
"""

import os
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips

def validate_resources(image_folder: str, audio_file: str, valid_extensions: tuple) -> list:
    if not os.path.isdir(image_folder):
        raise ValueError(f"Image folder '{image_folder}' not found.")
    
    image_files = sorted([
        os.path.join(image_folder, f)
        for f in os.listdir(image_folder)
        if f.lower().endswith(valid_extensions)
    ])
    
    if not image_files:
        raise ValueError("No images with valid extensions were found in the specified folder.")
    
    if not os.path.isfile(audio_file):
        raise ValueError(f"Audio file '{audio_file}' not found.")
    
    return image_files

def load_audio(audio_file: str) -> AudioFileClip:
    return AudioFileClip(audio_file)

def create_image_clip(img_path: str, duration: float, apply_fades: bool = False, fade_duration: float = 0.5):
    clip = ImageClip(img_path).with_duration(duration)
    if apply_fades:
        try:
            from moviepy.video.fx import fadein, fadeout
            clip = clip.with_effects(fadein, duration=fade_duration).with_effects(fadeout, duration=fade_duration)
        except ImportError:
            raise ImportError("Failed to import fadein/fadeout effects. Please ensure you have an up-to-date version of MoviePy.")
    return clip

def create_video_clips(image_files: list, per_image_duration: float, apply_fades: bool = False, fade_duration: float = 0.5) -> list:
    clips = []
    for img_path in image_files:
        try:
            clip = create_image_clip(img_path, per_image_duration, apply_fades, fade_duration)
        except Exception as e:
            raise RuntimeError(f"Failed to create clip for image {img_path}: {e}")
        clips.append(clip)
    return clips

def compose_video(clips: list, audio_clip: AudioFileClip, output_file: str, fps: int = 24) -> None:
    final_clip = concatenate_videoclips(clips, method="compose")
    final_clip = final_clip.with_audio(audio_clip)
    final_clip.fps = fps
    final_clip.write_videofile(output_file, codec='libx264', audio_codec='aac')

def create_video_with_transitions(image_folder: str, audio_file: str, output_file: str,
                                  apply_fades: bool = False, fade_duration: float = 0.5, fps: int = 24) -> None:
    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
    
    # Step 1: Validate and obtain the list of images.
    image_files = validate_resources(image_folder, audio_file, valid_extensions)
    
    # Step 2: Load the audio clip.
    audio_clip = load_audio(audio_file)
    
    # Step 3: Calculate the duration for each image.
    per_image_duration = audio_clip.duration / len(image_files)
    
    # Step 4: Create video clips from the images.
    clips = create_video_clips(image_files, per_image_duration, apply_fades, fade_duration)
    
    # Step 5: Assemble the video clips and save the final video.
    compose_video(clips, audio_clip, output_file, fps)