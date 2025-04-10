"""
Module for creating the final video from images and an audio track.
Uses MoviePy to compile clips and add effects.
"""
import os
import random
import textwrap
import logging
import time

import numpy as np
from PIL import Image

from moviepy import (
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    concatenate_videoclips,
    ColorClip,
    VideoClip,
)

from moviepy.video.fx import Crop, FadeIn, FadeOut

from config import (
    CHUNK_SIZE,
    FONTSIZE,
    HORIZONTAL_SIZE
)

logger = logging.getLogger(__name__)

class VideoEditor:
    def __init__(self):
        logger.info("VideoEditor initialized")

    
    def validate_resources(self, image_folder: str, audio_file: str, valid_extensions: tuple) -> list:
        logger.info(f"Validating resources: image_folder={image_folder}, audio_file={audio_file}")
        
        if not os.path.isdir(image_folder):
            logger.error(f"Image folder '{image_folder}' not found")
            raise ValueError(f"Image folder '{image_folder}' not found.")
        
        image_files = sorted([
            os.path.join(image_folder, f)
            for f in os.listdir(image_folder)
            if f.lower().endswith(valid_extensions)
        ])
        
        if not image_files:
            logger.error(f"No valid images found in {image_folder}")
            raise ValueError("No images with valid extensions were found in the specified folder.")
        
        logger.info(f"Found {len(image_files)} valid image files")
        logger.debug(f"Image files: {', '.join(os.path.basename(f) for f in image_files)}")
        
        if not os.path.isfile(audio_file):
            logger.error(f"Audio file '{audio_file}' not found")
            raise ValueError(f"Audio file '{audio_file}' not found.")
        
        logger.info("Resource validation successful")
        return image_files

    def load_audio(self, audio_file: str) -> AudioFileClip:
        logger.info(f"Loading audio file: {audio_file}")
        try:
            audio_clip = AudioFileClip(audio_file)
            duration = audio_clip.duration
            logger.info(f"Audio loaded successfully, duration: {duration:.2f} seconds")
            return audio_clip
        except Exception as e:
            logger.error(f"Error loading audio file: {str(e)}", exc_info=True)
            raise

    def create_image_clip(self, img_path: str, duration: float, apply_fades: bool = False, fade_duration: float = 0.5):
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
        img_name = os.path.basename(img_path)
        logger.debug(f"Creating image clip from {img_name}, duration={duration}s, apply_fades={apply_fades}")
        
        try:
            # Load the image as an ImageClip and set its duration
            clip = ImageClip(img_path).with_duration(duration)
            
            # Get image dimensions
            w, h = clip.size
            logger.debug(f"Image dimensions: {w}x{h}")
            
            zoom_factor = 1.2  # Zoom in by 20%
            
            # Randomly select start and end positions for panning, ensuring crop stays within image
            start_x = random.randint(0, int(w * (1 - 1 / zoom_factor)))
            start_y = random.randint(0, int(h * (1 - 1 / zoom_factor)))
            end_x = random.randint(0, int(w * (1 - 1 / zoom_factor)))
            end_y = random.randint(0, int(h * (1 - 1 / zoom_factor)))
            
            logger.debug(f"Ken Burns effect: start_pos=({start_x},{start_y}), end_pos=({end_x},{end_y}), zoom_factor={zoom_factor}")
            
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
            logger.debug(f"Ken Burns effect applied to {img_name}")
            
            # Apply fade-in and fade-out effects if requested
            if apply_fades:
                logger.debug(f"Applying fade effects with duration={fade_duration}s")
                ken_burns_clip = ken_burns_clip.fx(FadeIn, fade_duration).fx(FadeOut, fade_duration)
            
            return ken_burns_clip
        except Exception as e:
            logger.error(f"Error creating image clip for {img_name}: {str(e)}", exc_info=True)
            raise

    def create_video_clips(self, image_files: list, per_image_duration: float, apply_fades: bool = False, fade_duration: float = 0.5) -> list:
        logger.info(f"Creating video clips from {len(image_files)} images, duration per image: {per_image_duration:.2f}s")
        
        clips = []
        start_time = time.time()
        
        for i, img_path in enumerate(image_files):
            try:
                logger.debug(f"Processing image {i+1}/{len(image_files)}: {os.path.basename(img_path)}")
                clip = self.create_image_clip(img_path, per_image_duration, apply_fades, fade_duration)
                clips.append(clip)
            except Exception as e:
                logger.error(f"Failed to create clip for image {img_path}: {e}", exc_info=True)
                raise RuntimeError(f"Failed to create clip for image {img_path}: {e}")
        
        elapsed_time = time.time() - start_time
        logger.info(f"Created {len(clips)} video clips in {elapsed_time:.2f}s")
        return clips

    def compose_video(clips: list, audio_clip: AudioFileClip, output_file: str, fps: int = 24) -> None:
        logger.info(f"Composing final video: {len(clips)} clips, output: {output_file}, fps: {fps}")
        
        start_time = time.time()
        try:
            final_clip = concatenate_videoclips(clips, method="compose")
            final_clip = final_clip.with_audio(audio_clip)
            final_clip.fps = fps
            
            logger.info("Writing video file, this may take some time...")
            final_clip.write_videofile(output_file, codec='libx264', audio_codec='aac')
            
            elapsed_time = time.time() - start_time
            logger.info(f"Video composed successfully in {elapsed_time:.2f}s")
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"Video composition failed after {elapsed_time:.2f}s: {str(e)}", exc_info=True)
            raise

    def create_text_video(self, text, duration, chunk_size=CHUNK_SIZE, fontsize=FONTSIZE, color='white', 
                        bg_color='black', size=(HORIZONTAL_SIZE, 100), font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
        logger.info(f"Creating text overlay with duration: {duration:.2f}s, fontsize: {fontsize}")
        logger.debug(f"Text length: {len(text)} characters")
        
        chunks = textwrap.wrap(text, width=chunk_size, break_long_words=False)
        num_chunks = len(chunks)
        
        if num_chunks == 0:
            logger.warning("No text chunks to display, creating empty clip")
            if bg_color is None:
                return ColorClip(size, color=(0, 0, 0), duration=duration)
            return ColorClip(size, color=bg_color, duration=duration)
        
        logger.debug(f"Text split into {num_chunks} chunks, {chunk_size} chars per chunk")
        chunk_duration = duration / num_chunks
        
        try:
            clips = []
            for i, chunk in enumerate(chunks):
                logger.debug(f"Creating text clip {i+1}/{num_chunks}, text: '{chunk[:20]}...'")
                clip = TextClip(
                    text=chunk,
                    font=font,
                    font_size=fontsize,
                    color=color,
                    bg_color=bg_color,
                    size=size,
                    method='label'
                ).with_duration(chunk_duration)
                clips.append(clip)
                
            text_video = concatenate_videoclips(clips)
            logger.info(f"Text overlay created successfully, duration: {text_video.duration:.2f}s")
            return text_video
        except Exception as e:
            logger.error(f"Error creating text overlay: {str(e)}", exc_info=True)
            raise

    # def create_translated_text_video(text, duration, chunk_size=40, fontsize=50, color='white', 
    #                      bg_color='black', size=(1024, 100), font_path='arial.ttf'):
    #     chunks = textwrap.wrap(text, width=chunk_size, break_long_words=False)
    #     num_chunks = len(chunks)
        
    #     if num_chunks == 0:
    #         if bg_color is None:
    #             return ColorClip(size, color=(0, 0, 0), duration=duration)
    #         return ColorClip(size, color=bg_color, duration=duration)
        
    #     chunk_duration = duration / num_chunks
    #     clips = [
    #         TextClip(
    #             text=chunk,
    #             font=font_path,  # Required parameter!
    #             font_size=fontsize,
    #             color=color,
    #             bg_color=bg_color,
    #             size=size,  # Fixed: size should match the video
    #             method='label'  # Optimal rendering method
    #         ).with_duration(chunk_duration)
    #         for chunk in chunks
    #     ]
    #     return concatenate_videoclips(clips)

    def create_video_with_transitions(self, image_folder: str, audio_file: str, output_file: str, text: str,
                                    apply_fades: bool = False, fade_duration: float = 0.5, fps: int = 24, font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf') -> None:
        logger.info(f"Creating video with transitions: {image_folder} → {output_file}")
        start_time = time.time()
        
        valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
        
        try:
            # Validate resources
            logger.info("Validating resources...")
            image_files = self.validate_resources(image_folder, audio_file, valid_extensions)
            
            # Load audio
            logger.info("Loading audio...")
            audio_clip = AudioFileClip(audio_file)
            logger.info(f"Audio duration: {audio_clip.duration:.2f}s")
            
            # Calculate per-image duration
            per_image_duration = audio_clip.duration / len(image_files)
            logger.info(f"Calculated duration per image: {per_image_duration:.2f}s")
            
            # Create image clips
            logger.info("Creating image clips with transitions...")
            clips = self.create_video_clips(image_files, per_image_duration, apply_fades, fade_duration)
            
            # Concatenate image clips
            logger.info("Concatenating clips...")
            image_video = concatenate_videoclips(clips, method="compose")
            
            # Create and overlay text video if text is provided
            if text:
                logger.info("Creating text overlay...")
                text_video = self.create_text_video(
                    text,
                    duration=image_video.duration,
                    color='white',
                    fontsize=FONTSIZE,
                    chunk_size=CHUNK_SIZE,
                    bg_color=None  # Transparent background
                    )
                logger.info("Compositing video and text...")
                final_clip = CompositeVideoClip([image_video, text_video.with_position(("center", "bottom"))])
                logger.debug("Text overlay added to video")
            else:
                logger.info("No text provided, skipping text overlay")
                final_clip = image_video
            
            # Set audio
            logger.info("Adding audio to video...")
            final_clip = final_clip.with_audio(audio_clip)
            
            # Write the final video
            logger.info(f"Writing final video to {output_file} (fps={fps})...")
            final_clip.write_videofile(output_file, codec='libx264', audio_codec='aac', fps=fps)
            
            # Log completion and file size
            if os.path.exists(output_file):
                file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
                elapsed_time = time.time() - start_time
                logger.info(f"Video created successfully: {output_file} ({file_size_mb:.2f} MB) in {elapsed_time:.2f}s")
            else:
                logger.error(f"Video file not found at expected location: {output_file}")
        
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"Video creation failed after {elapsed_time:.2f}s: {str(e)}", exc_info=True)
            raise
