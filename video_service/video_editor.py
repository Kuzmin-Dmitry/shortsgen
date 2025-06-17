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

from moviepy.editor import ( # type: ignore
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    concatenate_videoclips,
    ColorClip,
    VideoClip,
    vfx
)

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
            image_folder: Path to folder containing images
            audio_file: Path to audio file
            valid_extensions: Tuple of valid image file extensions
            
        Returns:
            List of valid image file paths sorted by name
            
        Raises:
            FileNotFoundError: If resources are missing
            ValueError: If no valid images found
        """
        logger.info(f"Validating resources - images: {image_folder}, audio: {audio_file}")
        
        # Check if image folder exists
        if not os.path.exists(image_folder):
            raise FileNotFoundError(f"Image folder not found: {image_folder}")
        
        # Check if audio file exists
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"Audio file not found: {audio_file}")
        
        # Get all image files from the folder
        image_files = []
        for filename in os.listdir(image_folder):
            if filename.lower().endswith(valid_extensions):
                image_path = os.path.join(image_folder, filename)
                image_files.append(image_path)
        
        # Sort files by name for consistent ordering
        image_files.sort()
        
        if not image_files:
            raise ValueError(f"No valid image files found in {image_folder}")
        
        logger.info(f"Found {len(image_files)} valid images")
        return image_files

    def load_audio_clip(self, audio_file: str) -> AudioFileClip:
        """
        Load audio file and return AudioFileClip.
        
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
                start_x = random.uniform(0, w * (1 - 1/zoom_factor))
                start_y = random.uniform(0, h * (1 - 1/zoom_factor))
                end_x = random.uniform(0, w * (1 - 1/zoom_factor))
                end_y = random.uniform(0, h * (1 - 1/zoom_factor))
                
                # Create resize function for Ken Burns effect
                def ken_burns_effect(get_frame, t):
                    """Apply Ken Burns effect with smooth zoom and pan"""
                    progress = t / duration  # 0 to 1
                    
                    # Calculate current zoom (from 1 to zoom_factor)
                    current_zoom = 1 + (zoom_factor - 1) * progress
                    
                    # Calculate current position (smooth transition from start to end)
                    current_x = start_x + (end_x - start_x) * progress
                    current_y = start_y + (end_y - start_y) * progress
                    
                    # Get the frame
                    frame = get_frame(t)
                    
                    # Apply zoom and crop
                    crop_w = int(w / current_zoom)
                    crop_h = int(h / current_zoom)
                    
                    # Ensure crop stays within bounds
                    crop_x = int(min(max(current_x, 0), w - crop_w))
                    crop_y = int(min(max(current_y, 0), h - crop_h))
                    
                    # Crop and resize
                    cropped = frame[crop_y:crop_y + crop_h, crop_x:crop_x + crop_w]
                    resized = np.array(Image.fromarray(cropped).resize((w, h), Image.Resampling.LANCZOS))
                    
                    return resized
                
                # Apply the Ken Burns effect
                clip = clip.with_fps(self.settings.fps).fl(ken_burns_effect, apply_to=['mask'])
                logger.debug(f"Applied Ken Burns effect to {img_name}")
            
            # Resize clip to match video settings
            clip = clip.resized((self.settings.width, self.settings.height))
            
            # Apply fade effects if requested
            if apply_fades:
                fade_duration = min(self.settings.fade_duration, duration / 4)  # Limit fade to 1/4 of clip duration
                clip = clip.with_effects([vfx.FadeIn(fade_duration), vfx.FadeOut(fade_duration)])
                logger.debug(f"Applied fade effects to {img_name}")
            
            logger.debug(f"Successfully created clip from {img_name}")
            return clip
            
        except Exception as e:
            logger.error(f"Error creating clip from {img_name}: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to create clip from {img_name}: {str(e)}")

    def apply_transition(self, clip1: VideoClip, clip2: VideoClip, 
                        transition_duration: float = 0.5) -> VideoClip:
        """        Apply transition between two video clips.
        
        Args:
            clip1: First video clip
            clip2: Second video clip
            transition_duration: Duration of the transition effect
            
        Returns:
            VideoClip with transition applied
        """
        if self.settings.transition_type == TransitionType.NONE:
            return concatenate_videoclips([clip1, clip2])
        
        elif self.settings.transition_type == TransitionType.FADE:
            # Apply fade out to first clip and fade in to second clip
            clip1_faded = clip1.with_effects([vfx.FadeOut(transition_duration)])
            clip2_faded = clip2.with_effects([vfx.FadeIn(transition_duration)])
            return concatenate_videoclips([clip1_faded, clip2_faded])
        
        elif self.settings.transition_type == TransitionType.CROSSFADE:
            # Overlap clips with crossfade
            transition_duration = min(transition_duration, clip1.duration, clip2.duration)
            clip1_part = clip1.subclipped(0, clip1.duration - transition_duration/2)
            clip1_fade = clip1.subclipped(clip1.duration - transition_duration, clip1.duration).with_effects([vfx.FadeOut(transition_duration)])
            clip2_fade = clip2.subclipped(0, transition_duration).with_effects([vfx.FadeIn(transition_duration)])
            clip2_part = clip2.subclipped(transition_duration/2, clip2.duration)
            
            # Composite the overlapping parts
            overlapping = CompositeVideoClip([clip1_fade, clip2_fade])
            
            return concatenate_videoclips([clip1_part, overlapping, clip2_part])
        
        else:
            # Default to simple concatenation for unsupported transitions
            logger.warning(f"Unsupported transition type: {self.settings.transition_type}")
            return concatenate_videoclips([clip1, clip2])

    def create_text_overlay(self, text: str, video_clip: VideoClip, 
                           start_time: float = 0, 
                           duration: Optional[float] = None) -> VideoClip:
        """
        Add text overlay to a video clip.
        
        Args:
            text: Text to overlay
            video_clip: Video clip to add text to
            start_time: When to start showing the text
            duration: How long to show the text (defaults to remaining clip duration)
            
        Returns:
            CompositeVideoClip with text overlay
        """
        if duration is None:
            duration = video_clip.duration - start_time
        
        logger.debug(f"Creating text overlay: '{text[:50]}...' at {start_time}s for {duration}s")
        
        try:
            # Wrap text for better readability
            wrapped_text = textwrap.fill(text, width=50)
              # Create text clip
            text_clip = TextClip(
                text=wrapped_text,
                font=self.settings.font,
                font_size=self.settings.text_fontsize,
                color=self.settings.text_color,
                bg_color=self.settings.bg_color,
                size=(self.settings.width * 0.8, None)  # 80% of video width
            ).with_duration(duration).with_start(start_time)
            
            # Position text based on settings
            if self.settings.text_position == TextPosition.TOP:
                text_clip = text_clip.with_position(('center', 50))
            elif self.settings.text_position == TextPosition.BOTTOM:
                text_clip = text_clip.with_position(('center', self.settings.height - text_clip.h - 50))
            elif self.settings.text_position == TextPosition.CENTER:
                text_clip = text_clip.with_position('center')
            elif self.settings.text_position == TextPosition.TOP_LEFT:
                text_clip = text_clip.with_position((50, 50))
            elif self.settings.text_position == TextPosition.TOP_RIGHT:
                text_clip = text_clip.with_position((self.settings.width - text_clip.w - 50, 50))
            elif self.settings.text_position == TextPosition.BOTTOM_LEFT:
                text_clip = text_clip.with_position((50, self.settings.height - text_clip.h - 50))
            elif self.settings.text_position == TextPosition.BOTTOM_RIGHT:
                text_clip = text_clip.with_position((self.settings.width - text_clip.w - 50, self.settings.height - text_clip.h - 50))
            else:
                text_clip = text_clip.with_position(('center', self.settings.height - text_clip.h - 50))
            
            # Composite video with text
            composite_clip = CompositeVideoClip([video_clip, text_clip])
            
            logger.debug(f"Successfully created text overlay")
            return composite_clip
            
        except Exception as e:
            logger.error(f"Error creating text overlay: {str(e)}", exc_info=True)
            # Return original clip if text overlay fails
            return video_clip

    def create_video_from_images_and_audio(self, 
                                          image_folder: str, 
                                          audio_file: str, 
                                          output_file: str,
                                          text_overlays: Optional[List[str]] = None,
                                          apply_ken_burns: bool = True,
                                          apply_transitions: bool = True) -> bool:
        """
        Create a video from a folder of images and an audio file.
        
        Args:
            image_folder: Path to folder containing images
            audio_file: Path to audio file
            output_file: Path for output video file
            text_overlays: Optional list of text overlays for each image
            apply_ken_burns: Whether to apply Ken Burns effect to images
            apply_transitions: Whether to apply transitions between clips
            
        Returns:
            bool: True if successful, False otherwise
        """
        start_time = time.time()
        logger.info(f"Starting video creation from {image_folder} with audio {audio_file}")
        
        try:
            # Validate resources
            image_files = self.validate_resources(image_folder, audio_file)
            
            # Load audio
            audio_clip = self.load_audio_clip(audio_file)
            audio_duration = audio_clip.duration
            
            # Calculate duration per image
            num_images = len(image_files)
            duration_per_image = audio_duration / num_images
            
            logger.info(f"Creating video with {num_images} images, "
                       f"audio duration: {audio_duration:.2f}s, "
                       f"duration per image: {duration_per_image:.2f}s")
            
            # Create video clips from images
            video_clips = []
            for i, img_path in enumerate(image_files):
                try:
                    # Create image clip
                    clip = self.create_image_clip(
                        img_path, 
                        duration_per_image,
                        apply_ken_burns=apply_ken_burns,
                        apply_fades=False  # We'll handle transitions separately
                    )
                    
                    # Add text overlay if provided
                    if text_overlays and i < len(text_overlays) and text_overlays[i]:
                        clip = self.create_text_overlay(
                            text_overlays[i], 
                            clip, 
                            start_time=0, 
                            duration=duration_per_image
                        )
                    
                    video_clips.append(clip)
                    logger.debug(f"Created clip {i+1}/{num_images}")
                    
                except Exception as e:
                    logger.error(f"Error processing image {img_path}: {str(e)}")
                    # Continue with other images instead of failing completely
                    continue
            
            if not video_clips:
                raise RuntimeError("No video clips were created successfully")
            
            # Combine clips with transitions
            if apply_transitions and len(video_clips) > 1:
                logger.info("Applying transitions between clips")
                final_clip = video_clips[0]
                for clip in video_clips[1:]:
                    final_clip = self.apply_transition(final_clip, clip, self.settings.fade_duration)
            else:
                logger.info("Concatenating clips without transitions")
                final_clip = concatenate_videoclips(video_clips)
            
            # Set audio
            final_clip = final_clip.with_audio(audio_clip)
            
            # Ensure output directory exists
            output_dir = os.path.dirname(output_file)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # Write video file
            logger.info(f"Writing video to {output_file}")
            final_clip.write_videofile(
                output_file,
                fps=self.settings.fps,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                verbose=False,
                logger=None  # Disable moviepy's logger to reduce noise
            )
            
            # Clean up
            audio_clip.close()
            final_clip.close()
            for clip in video_clips:
                clip.close()
            
            elapsed_time = time.time() - start_time
            logger.info(f"Video creation completed successfully in {elapsed_time:.2f} seconds")
            logger.info(f"Output file: {output_file}")
            
            return True
            
        except Exception as e:
            logger.exception(f"Error creating video: {str(e)}")
            return False

    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        Get information about a video file.          Args:
            video_path: Path to the video file
        Returns:
            Dictionary with video information
        """
        try:
            from moviepy.editor import VideoFileClip # type: ignore
            
            with VideoFileClip(video_path) as clip:
                info = {
                    "duration": clip.duration,
                    "fps": clip.fps,
                    "size": clip.size,
                    "width": clip.w,
                    "height": clip.h,
                    "has_audio": clip.audio is not None,
                    "file_size": os.path.getsize(video_path) if os.path.exists(video_path) else 0
                }
                
                if clip.audio:
                    info["audio_duration"] = clip.audio.duration
                    
                return info
                
        except Exception as e:
            logger.error(f"Error getting video info for {video_path}: {str(e)}")
            return {"error": str(e)}
