"""
Video composition and editing service.

Provides functionality for creating professional-quality videos from still images
and audio tracks with transitions, effects, and text overlays.
"""

import os
import random
import textwrap
import logging
import time
from pathlib import Path
from typing import List, Tuple, Optional, Union, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum

import numpy as np
from PIL import Image, ImageFile
# Enable loading of truncated images
ImageFile.LOAD_TRUNCATED_IMAGES = True

from moviepy import (
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    concatenate_videoclips,
    ColorClip,
    VideoClip,
)
from moviepy.video.fx import FadeIn, FadeOut

from config import (
    CHUNK_SIZE,
    FONTSIZE,
    HORIZONTAL_SIZE,
    DIRS
)

# Get module logger
logger = logging.getLogger(__name__)

class TransitionType(Enum):
    """Available video transition types."""
    NONE = "none"
    FADE = "fade"
    CROSSFADE = "crossfade"
    SLIDE = "slide"

class TextPosition(Enum):
    """Standard positions for text overlays."""
    TOP = "top"
    BOTTOM = "bottom"
    CENTER = "center"
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"

@dataclass
class VideoSettings:
    """Configuration settings for video generation."""
    fps: int = 24
    width: int = 1024
    height: int = 1024
    text_fontsize: int = FONTSIZE
    chunk_size: int = CHUNK_SIZE
    fade_duration: float = 0.5
    text_color: str = "white"
    bg_color: str = "black"
    font: str = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    text_position: TextPosition = TextPosition.BOTTOM
    transition_type: TransitionType = TransitionType.FADE

class VideoEditor:
    """
    Handles video creation and editing from images and audio.
    
    This class provides methods to create videos with effects, transitions, 
    and text overlays from still images and audio tracks.
    """
    
    def __init__(self, settings: Optional[VideoSettings] = None):
        """
        Initialize the video editor with optional custom settings.
        
        Args:
            settings: Optional custom video settings. If None, default settings are used.
        """
        self.settings = settings or VideoSettings()
        logger.info("VideoEditor initialized with settings: "
                   f"resolution={self.settings.width}x{self.settings.height}, "
                   f"fps={self.settings.fps}, "
                   f"transitions={self.settings.transition_type.value}")
    
    def validate_resources(self, image_folder: str, audio_file: str, 
                          valid_extensions: Tuple[str, ...] = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')) -> List[str]:
        """
        Validate that all required resources exist and return list of valid image files.
        
        Args:
            image_folder: Path to the folder containing images
            audio_file: Path to the audio file
            valid_extensions: Tuple of valid file extensions to consider
            
        Returns:
            List of valid image file paths sorted alphabetically
            
        Raises:
            ValueError: If resources are missing or invalid
        """
        logger.info(f"Validating resources: image_folder={image_folder}, audio_file={audio_file}")
        
        # Check image folder exists
        if not os.path.isdir(image_folder):
            logger.error(f"Image folder '{image_folder}' not found")
            raise ValueError(f"Image folder '{image_folder}' not found.")
        
        # Get valid image files and sort them
        image_files = sorted([
            os.path.join(image_folder, f)
            for f in os.listdir(image_folder)
            if f.lower().endswith(valid_extensions)
        ])
        
        # Check if we found any images
        if not image_files:
            logger.error(f"No valid images found in {image_folder}")
            raise ValueError("No images with valid extensions were found in the specified folder.")
        
        logger.info(f"Found {len(image_files)} valid image files")
        logger.debug(f"Image files: {', '.join(os.path.basename(f) for f in image_files)}")
        
        # Check audio file exists
        if not os.path.isfile(audio_file):
            logger.error(f"Audio file '{audio_file}' not found")
            raise ValueError(f"Audio file '{audio_file}' not found.")
        
        logger.info("Resource validation successful")
        return image_files

    def load_audio(self, audio_file: str) -> AudioFileClip:
        """
        Load an audio file and return it as an AudioFileClip.
        
        Args:
            audio_file: Path to the audio file
            
        Returns:
            AudioFileClip object
            
        Raises:
            RuntimeError: If there's an error loading the audio file
        """
        logger.info(f"Loading audio file: {audio_file}")
        try:
            audio_clip = AudioFileClip(audio_file)
            duration = audio_clip.duration
            logger.info(f"Audio loaded successfully, duration: {duration:.2f} seconds")
            return audio_clip
        except Exception as e:
            logger.error(f"Error loading audio file: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to load audio file: {str(e)}")

    def create_image_clip(self, img_path: str, duration: float, 
                         apply_ken_burns: bool = True,
                         apply_fades: bool = False) -> VideoClip:
        """
        Create a video clip from an image with optional Ken Burns effect and fades.
        
        Args:
            img_path: Path to the image file
            duration: Duration of the clip in seconds
            apply_ken_burns: Whether to apply Ken Burns effect (slow zoom and pan)
            apply_fades: Whether to apply fade-in and fade-out effects
            
        Returns:
            MoviePy VideoClip with effects applied
            
        Raises:
            RuntimeError: If there's an error creating the clip
        """
        img_name = os.path.basename(img_path)
        logger.debug(f"Creating image clip from {img_name}, duration={duration}s, "
                    f"ken_burns={apply_ken_burns}, apply_fades={apply_fades}")
        
        try:
            # Load the image as an ImageClip and set its duration
            clip = ImageClip(img_path).with_duration(duration)
            
            # Get image dimensions
            w, h = clip.size
            logger.debug(f"Image dimensions: {w}x{h}")
            
            # Apply Ken Burns effect if requested
            if apply_ken_burns:
                zoom_factor = 1.2  # Zoom in by 20%
                
                # Randomly select start and end positions for panning, ensuring crop stays within image
                start_x = random.randint(0, int(w * (1 - 1 / zoom_factor)))
                start_y = random.randint(0, int(h * (1 - 1 / zoom_factor)))
                end_x = random.randint(0, int(w * (1 - 1 / zoom_factor)))
                end_y = random.randint(0, int(h * (1 - 1 / zoom_factor)))
                
                logger.debug(f"Ken Burns effect: start_pos=({start_x},{start_y}), "
                            f"end_pos=({end_x},{end_y}), zoom_factor={zoom_factor}")
                
                def make_frame(t: float) -> np.ndarray:
                    """
                    Generate a frame at time t with the Ken Burns effect (zoom and pan).
                    
                    Args:
                        t: Time in seconds
                    
                    Returns:
                        Frame as a NumPy array with shape (h, w, 3)
                    """
                    # Get the base image frame
                    frame = clip.get_frame(t)
                    
                    # Calculate current zoom and position
                    progress = t / duration
                    zoom = 1 + (zoom_factor - 1) * progress
                    crop_w = max(1, int(w / zoom))  # Ensure crop width is at least 1
                    crop_h = max(1, int(h / zoom))  # Ensure crop height is at least 1
                    x = int(start_x + (end_x - start_x) * progress)
                    y = int(start_y + (end_y - start_y) * progress)
                    
                    # Clamp x and y to ensure the crop region stays within the image
                    x = max(0, min(x, w - crop_w))
                    y = max(0, min(y, h - crop_h))
                    
                    # Crop the frame
                    cropped_frame = frame[y:y + crop_h, x:x + crop_w]
                    
                    # Resize the cropped frame back to the original size
                    pil_img = Image.fromarray(cropped_frame)
                    resized_img = pil_img.resize((w, h), Image.Resampling.LANCZOS)
                    
                    return np.array(resized_img)
                
                # Create a VideoClip with the Ken Burns effect
                result_clip = VideoClip(make_frame, duration=duration)
                logger.debug(f"Ken Burns effect applied to {img_name}")
            else:
                # Use the original clip without Ken Burns effect
                result_clip = clip
            
            # Apply fade-in and fade-out effects if requested
            if apply_fades:
                fade_duration = min(self.settings.fade_duration, duration / 4)
                logger.debug(f"Applying fade effects with duration={fade_duration}s")
                result_clip = result_clip.fx(FadeIn, fade_duration).fx(FadeOut, fade_duration)
            
            return result_clip
        except Exception as e:
            logger.error(f"Error creating image clip for {img_name}: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to create clip for image {img_name}: {str(e)}")

    def create_video_clips(self, image_files: List[str], per_image_duration: float, 
                          apply_ken_burns: bool = True,
                          apply_fades: bool = False) -> List[VideoClip]:
        """
        Create video clips from a list of image files.
        
        Args:
            image_files: List of image file paths
            per_image_duration: Duration for each image in seconds
            apply_ken_burns: Whether to apply Ken Burns effect
            apply_fades: Whether to apply fade transitions
            
        Returns:
            List of video clips
            
        Raises:
            RuntimeError: If there's an error creating any clip
        """
        logger.info(f"Creating video clips from {len(image_files)} images, "
                   f"duration per image: {per_image_duration:.2f}s, "
                   f"ken_burns={apply_ken_burns}, "
                   f"fades={apply_fades}")
        
        clips = []
        start_time = time.time()
        
        for i, img_path in enumerate(image_files):
            try:
                logger.debug(f"Processing image {i+1}/{len(image_files)}: {os.path.basename(img_path)}")
                clip = self.create_image_clip(
                    img_path, 
                    per_image_duration, 
                    apply_ken_burns=apply_ken_burns,
                    apply_fades=apply_fades
                )
                clips.append(clip)
            except Exception as e:
                logger.error(f"Failed to create clip for image {img_path}: {str(e)}", exc_info=True)
                raise RuntimeError(f"Failed to create clip for image {img_path}: {str(e)}")
        
        elapsed_time = time.time() - start_time
        logger.info(f"Created {len(clips)} video clips in {elapsed_time:.2f}s")
        return clips

    def compose_video(self, clips: List[VideoClip], audio_clip: AudioFileClip, 
                     output_file: str) -> None:
        """
        Compose final video from clips and audio.
        
        Args:
            clips: List of video clips to concatenate
            audio_clip: Audio clip to add to the video
            output_file: Path to save the final video
            
        Raises:
            RuntimeError: If video composition fails
        """
        logger.info(f"Composing final video: {len(clips)} clips, output: {output_file}, fps: {self.settings.fps}")
        
        start_time = time.time()
        try:
            # Create output directory if it doesn't exist
            output_dir = os.path.dirname(output_file)
            os.makedirs(output_dir, exist_ok=True)
            
            # Concatenate clips and add audio
            final_clip = concatenate_videoclips(clips, method="compose")
            final_clip = final_clip.with_audio(audio_clip)
            final_clip.fps = self.settings.fps
            
            # Write video file
            logger.info("Writing video file, this may take some time...")
            final_clip.write_videofile(
                output_file, 
                codec='libx264', 
                audio_codec='aac',
                fps=self.settings.fps,
                logger=None  # Disable moviepy's logger to use our own
            )
            
            # Log completion and file size
            elapsed_time = time.time() - start_time
            if os.path.exists(output_file):
                file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
                logger.info(f"Video composed successfully: {output_file} "
                           f"({file_size_mb:.2f} MB) in {elapsed_time:.2f}s")
            else:
                logger.error(f"Video file not found at expected location: {output_file}")
                raise RuntimeError("Video file was not created successfully")
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"Video composition failed after {elapsed_time:.2f}s: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to compose video: {str(e)}")

    def create_text_clip(self, text: str, duration: float, 
                        position: Union[str, Tuple[str, str]] = None,
                        transparent_bg: bool = True) -> VideoClip:
        """
        Create a video clip with text.
        
        Args:
            text: Text to display
            duration: Duration of the clip in seconds
            position: Position of the text (defaults to settings.text_position)
            transparent_bg: Whether to use a transparent background
            
        Returns:
            MoviePy VideoClip with text
            
        Raises:
            RuntimeError: If text clip creation fails
        """
        logger.info(f"Creating text clip with duration: {duration:.2f}s, "
                  f"fontsize: {self.settings.text_fontsize}")
        logger.debug(f"Text length: {len(text)} characters")
        
        # Use settings position if none provided
        if position is None:
            position = ("center", self.settings.text_position.value)
            if isinstance(position, TextPosition):
                position = ("center", position.value)
        
        # Define the background color
        bg_color = None if transparent_bg else self.settings.bg_color
        
        # Split text into chunks
        chunks = textwrap.wrap(
            text, 
            width=self.settings.chunk_size, 
            break_long_words=False
        )
        num_chunks = len(chunks)
        
        if num_chunks == 0:
            logger.warning("No text chunks to display, creating empty clip")
            return ColorClip(
                (self.settings.width, 100), 
                color=(0, 0, 0, 0) if transparent_bg else (0, 0, 0),
                duration=duration
            )
        
        logger.debug(f"Text split into {num_chunks} chunks, {self.settings.chunk_size} chars per chunk")
        chunk_duration = duration / num_chunks
        
        try:
            clips = []
            for i, chunk in enumerate(chunks):
                logger.debug(f"Creating text clip {i+1}/{num_chunks}, text: '{chunk[:20]}...'")
                clip = TextClip(
                    text=chunk,
                    font=self.settings.font,
                    font_size=self.settings.text_fontsize,
                    color=self.settings.text_color,
                    bg_color=bg_color,
                    size=(self.settings.width, None),  # Width fixed, height automatic
                    method='label'
                ).with_duration(chunk_duration)
                clips.append(clip)
                
            text_video = concatenate_videoclips(clips)
            logger.info(f"Text clip created successfully, duration: {text_video.duration:.2f}s")
            return text_video
        except Exception as e:
            logger.error(f"Error creating text clip: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to create text clip: {str(e)}")

    def create_video(self, 
                    image_folder: str, 
                    audio_file: str, 
                    output_file: str, 
                    text: Optional[str] = None,
                    apply_ken_burns: bool = True,
                    apply_fades: bool = True) -> str:
        """
        Create a complete video from images, audio, and optional text.
        
        This is the main method for creating videos with all effects.
        
        Args:
            image_folder: Path to folder containing image files
            audio_file: Path to audio file
            output_file: Path to save the final video
            text: Optional text to display as overlay
            apply_ken_burns: Whether to apply Ken Burns effect to images
            apply_fades: Whether to apply fade transitions between images
            
        Returns:
            Path to the created video file
            
        Raises:
            Exception: If any part of the video creation process fails
        """
        logger.info(f"Creating video with transitions: {image_folder} → {output_file}")
        logger.debug(f"Options: ken_burns={apply_ken_burns}, fades={apply_fades}, text={bool(text)}")
        
        start_time = time.time()
        valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
        
        try:
            # Validate resources
            logger.info("Validating resources...")
            image_files = self.validate_resources(image_folder, audio_file, valid_extensions)
            
            # Load audio
            logger.info("Loading audio...")
            audio_clip = self.load_audio(audio_file)
            logger.info(f"Audio duration: {audio_clip.duration:.2f}s")
            
            # Calculate per-image duration
            per_image_duration = audio_clip.duration / len(image_files)
            logger.info(f"Calculated duration per image: {per_image_duration:.2f}s")
            
            # Create image clips
            logger.info("Creating image clips with transitions...")
            clips = self.create_video_clips(
                image_files, 
                per_image_duration, 
                apply_ken_burns=apply_ken_burns,
                apply_fades=apply_fades
            )
            
            # Concatenate image clips
            logger.info("Concatenating clips...")
            image_video = concatenate_videoclips(clips, method="compose")
            
            # Create and overlay text video if text is provided
            final_clip = image_video
            if text:
                logger.info("Creating text overlay...")
                text_video = self.create_text_clip(
                    text,
                    duration=image_video.duration,
                    transparent_bg=True
                )
                
                logger.info("Compositing video and text...")
                text_position = ("center", self.settings.text_position.value)
                final_clip = CompositeVideoClip([
                    image_video, 
                    text_video.with_position(text_position)
                ])
                logger.debug("Text overlay added to video")
            else:
                logger.info("No text provided, skipping text overlay")
            
            # Set audio
            logger.info("Adding audio to video...")
            final_clip = final_clip.with_audio(audio_clip)
            
            # Create output directory if needed
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # Write the final video
            logger.info(f"Writing final video to {output_file} (fps={self.settings.fps})...")
            final_clip.write_videofile(
                output_file, 
                codec='libx264', 
                audio_codec='aac', 
                fps=self.settings.fps,
                threads=4,  # Set a reasonable thread count
                logger=None  # Disable moviepy's logger to use our own
            )
            
            # Log completion and file size
            if os.path.exists(output_file):
                file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
                elapsed_time = time.time() - start_time
                logger.info(f"Video created successfully: {output_file} ({file_size_mb:.2f} MB) in {elapsed_time:.2f}s")
                return output_file
            else:
                logger.error(f"Video file not found at expected location: {output_file}")
                raise RuntimeError("Video file was not created successfully")
        
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"Video creation failed after {elapsed_time:.2f}s: {str(e)}", exc_info=True)
            raise
