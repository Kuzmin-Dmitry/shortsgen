"""
Module for creating the final video from images and an audio track.
Uses MoviePy to compile clips and add effects.
"""

import os
from moviepy import *
import random
from moviepy.video.fx import Crop, FadeIn, FadeOut
from PIL import Image
import numpy as np
from moviepy import ImageClip
from moviepy.video.VideoClip import VideoClip
import textwrap
from moviepy import TextClip, concatenate_videoclips, ColorClip


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
    """
    Create a video clip from an image with an optional Ken Burns effect and fades.
    
    Args:
        img_path (str): Path to the image file.
        duration (float): Duration of the clip in seconds.
        apply_fades (bool): Whether to apply fade-in and fade-out effects.
        fade_duration (float): Duration of fade effects in seconds.
    
    Returns:
        VideoClip: A MoviePy VideoClip object with the Ken Burns effect applied.
    """
    # Load the image as an ImageClip and set its duration
    clip = ImageClip(img_path).with_duration(duration)
    
    # Get image dimensions
    w, h = clip.size
    zoom_factor = 1.2  # Zoom in by 20%
    
    # Randomly select start and end positions for panning, ensuring crop stays within image
    start_x = random.randint(0, int(w * (1 - 1 / zoom_factor)))
    start_y = random.randint(0, int(h * (1 - 1 / zoom_factor)))
    end_x = random.randint(0, int(w * (1 - 1 / zoom_factor)))
    end_y = random.randint(0, int(h * (1 - 1 / zoom_factor)))
    def make_frame(t):
        """
        Generate a frame at time t with the Ken Burns effect (zoom and pan).
        
        Args:
            t (float): Time in seconds.
        
        Returns:
            np.ndarray: The frame as a NumPy array with shape (h, w, 3).
        """
        # Get the base image frame (same for all t since it's a still image)
        frame = clip.get_frame(t)
        
        # Calculate current zoom and position
        zoom = 1 + (zoom_factor - 1) * (t / duration)
        crop_w = max(1, int(w / zoom))  # Ensure crop width is at least 1
        crop_h = max(1, int(h / zoom))  # Ensure crop height is at least 1
        x = int(start_x + (end_x - start_x) * (t / duration))
        y = int(start_y + (end_y - start_y) * (t / duration))
        
        # Clamp x and y to ensure the crop region stays within the image
        x = max(0, min(x, w - crop_w))
        y = max(0, min(y, h - crop_h))
        
        # Crop the frame using NumPy slicing
        cropped_frame = frame[y:y + crop_h, x:x + crop_w]
        
        # Resize the cropped frame back to the original size
        pil_img = Image.fromarray(cropped_frame)
        resized_img = pil_img.resize((w, h), Image.LANCZOS)  # High-quality resampling
        
        return np.array(resized_img)
    
    # Create a VideoClip with the Ken Burns effect
    ken_burns_clip = VideoClip(make_frame, duration=duration)
    
    # Apply fade-in and fade-out effects if requested
    if apply_fades:
        ken_burns_clip = ken_burns_clip.fx(fadein, fade_duration).fx(fadeout, fade_duration)
    
    return ken_burns_clip

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

def create_text_video(text, duration, chunk_size=40, fontsize=50, color='white', 
                     bg_color='black', size=(1024, 100), font_path='arial.ttf'):
    chunks = textwrap.wrap(text, width=chunk_size, break_long_words=False)
    num_chunks = len(chunks)
    
    if num_chunks == 0:
        if bg_color is None:
            return ColorClip(size, color=(0, 0, 0), duration=duration)
        return ColorClip(size, color=bg_color, duration=duration)
    
    chunk_duration = duration / num_chunks
    clips = [
        TextClip(
            text=chunk,
            font=font_path,  # Обязательный параметр!
            font_size=fontsize,
            color=color,
            bg_color=bg_color,
            size=size,  # Исправлено: размер должен соответствовать видео
            method='label'  # Оптимальный метод рендеринга
        ).with_duration(chunk_duration)
        for chunk in chunks
    ]
    return concatenate_videoclips(clips)

def create_translated_text_video(text, duration, chunk_size=40, fontsize=50, color='white', 
                     bg_color='black', size=(1024, 100), font_path='arial.ttf'):
    chunks = textwrap.wrap(text, width=chunk_size, break_long_words=False)
    num_chunks = len(chunks)
    
    if num_chunks == 0:
        if bg_color is None:
            return ColorClip(size, color=(0, 0, 0), duration=duration)
        return ColorClip(size, color=bg_color, duration=duration)
    
    chunk_duration = duration / num_chunks
    clips = [
        TextClip(
            text=chunk,
            font=font_path,  # Обязательный параметр!
            font_size=fontsize,
            color=color,
            bg_color=bg_color,
            size=size,  # Исправлено: размер должен соответствовать видео
            method='label'  # Оптимальный метод рендеринга
        ).with_duration(chunk_duration)
        for chunk in chunks
    ]
    return concatenate_videoclips(clips)

def create_video_with_transitions(image_folder: str, audio_file: str, output_file: str, text: str, translation_text: str,
                                  apply_fades: bool = False, fade_duration: float = 0.5, fps: int = 24) -> None:
    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
    
    # Validate resources
    image_files = validate_resources(image_folder, audio_file, valid_extensions)
    
    # Load audio
    audio_clip = AudioFileClip(audio_file)
    
    # Calculate per-image duration
    per_image_duration = audio_clip.duration / len(image_files)
    
    # Create image clips
    clips = create_video_clips(image_files, per_image_duration, apply_fades, fade_duration)
    
    # Concatenate image clips
    image_video = concatenate_videoclips(clips, method="compose")
    
    # Create and overlay text video if text is provided
    if text:
        text_video = create_text_video(
            text,
            duration=image_video.duration,
            color='white',
            fontsize=50,
            chunk_size=35,
            bg_color=None  # Transparent background
        )
    #     first_clip = CompositeVideoClip([image_video, text_video.with_position((1,200))])
    # else:
    #     first_clip = image_video
    
    # Convert to grayscale
    #final_clip = final_clip.fx(blackwhite)

    if translation_text:
        text_translated_video = create_translated_text_video(
            translation_text,
            duration=image_video.duration,
            color='white',
            fontsize=50,
            chunk_size=35,
            bg_color=None  # Transparent background
        )
        final_clip = CompositeVideoClip([image_video, text_video.with_position((1,600)),text_translated_video.with_position((1,200))])
    else:
        final_clip = image_video
    
    
    # Set audio
    final_clip = final_clip.with_audio(audio_clip)
    
    # Write the final video
    final_clip.write_videofile(output_file, codec='libx264', audio_codec='aac', fps=fps)
