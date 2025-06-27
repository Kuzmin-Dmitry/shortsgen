"""
Video generation service optimized for MoviePy ≥ 2.2.1.
Key improvements:
  - Fixed Ken Burns effect implementation
  - Memory optimization for large videos
  - Proper resource handling
  - Resolution consistency
  - Updated MoviePy 2.x API usage
"""

import os
import logging
import hashlib
import asyncio
from typing import Dict, List, Any, Tuple
from PIL import Image
import numpy as np

from config import (
    VIDEO_OUTPUT_DIR,
    DEFAULT_FPS,
    DEFAULT_RESOLUTION,
    DEFAULT_SLIDE_DURATION,
    DEFAULT_TRANSITION_DURATION,
    DEFAULT_ZOOM_FACTOR,
)

logger = logging.getLogger(__name__)


# MoviePy v2.2.1 style imports. Don't use deprecated v1.x imports!
# https://zulko.github.io/moviepy/reference/reference/moviepy.video.fx.FadeIn.html#module-moviepy.video.fx.FadeIn
# https://zulko.github.io/moviepy/reference/reference/moviepy.video.fx.FadeOut.html#module-moviepy.video.fx.FadeOut
# https://zulko.github.io/moviepy/reference/reference/moviepy.video.fx.Resize.html#module-moviepy.video.fx.Resize
from moviepy.video.fx import Resize, FadeIn, FadeOut, Crop
from moviepy.video.VideoClip import VideoClip, ImageClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.compositing.CompositeVideoClip import concatenate_videoclips


class VideoService:
    """Service for generating videos with images and audio using MoviePy ≥ 2."""

    def __init__(self) -> None:
        self.output_dir = VIDEO_OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)

    async def generate_video_async(
        self,
        audio_path: str,
        image_paths: List[str],
        fps: int = DEFAULT_FPS,
        resolution: Tuple[int, int] = DEFAULT_RESOLUTION,
        slide_duration: float = DEFAULT_SLIDE_DURATION,
        transition_duration: float = DEFAULT_TRANSITION_DURATION,
        enable_ken_burns: bool = True,
        zoom_factor: float = DEFAULT_ZOOM_FACTOR,
    ) -> Dict[str, Any]:

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                self._generate_video_sync,
                audio_path,
                image_paths,
                fps,
                resolution,
                slide_duration,
                transition_duration,
                enable_ken_burns,
                zoom_factor,
            )
        except Exception as exc:  # pragma: no cover
            logger.exception("Video generation failed: %s", exc)
            return {"success": False, "message": f"Video generation failed: {exc}"}

    # ---------------------------------------------------------------------
    # Synchronous core – optimized for MoviePy ≥ 2.2.1
    # ---------------------------------------------------------------------

    def _generate_video_sync(
        self,
        audio_path: str,
        image_paths: List[str],
        fps: int,
        resolution: Tuple[int, int],
        slide_duration: float,
        transition_duration: float,
        enable_ken_burns: bool,
        zoom_factor: float,
    ) -> Dict[str, Any]:
        # ---- Input validation ------------------------------------------------
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        valid_images = [p for p in image_paths if os.path.exists(p)]
        for missing in set(image_paths) - set(valid_images):
            logger.warning("Image not found: %s", missing)
        if not valid_images:
            raise ValueError("No valid images found")

        # ---- Load audio & derive timing --------------------------------------
        with AudioFileClip(audio_path) as audio_clip:
            total_audio_duration: float = audio_clip.duration
            total_slides = len(valid_images)
            
            # Calculate adjusted slide duration
            available_time = total_audio_duration - (total_slides - 1) * transition_duration
            slide_duration_adj = max(1.0, available_time / total_slides)

            logger.info(
                "Creating video: %d slides, %.2fs each (total audio %.2fs)",
                total_slides,
                slide_duration_adj,
                total_audio_duration,
            )

            # ---- Build image clips -------------------------------------------
            clips = []
            for idx, img_path in enumerate(valid_images):
                clip = self._create_image_clip(
                    img_path=img_path,
                    duration=slide_duration_adj,
                    resolution=resolution,
                    fps=fps,
                    enable_ken_burns=enable_ken_burns,
                    zoom_factor=zoom_factor,
                )

                # Apply transitions
                if idx == 0:  # First clip
                    clip = clip.with_effects([FadeIn(duration=transition_duration / 2)])
                elif idx == total_slides - 1:  # Last clip
                    clip = clip.with_effects([FadeOut(duration=transition_duration / 2)])
                else:  # Middle clips
                    clip = clip.with_effects([
                        FadeIn(duration=transition_duration / 2),
                        FadeOut(duration=transition_duration / 2)
                    ])

                clips.append(clip)

            # ---- Concatenate clips -------------------------------------------
            final_video = concatenate_videoclips(clips, method="compose")

            # ---- Synchronize with audio --------------------------------------
            video_duration = final_video.duration
            if video_duration > total_audio_duration:
                final_video = final_video.subclipped(0, total_audio_duration)
            elif video_duration < total_audio_duration:
                # Create padding with last frame
                last_frame = final_video.get_frame(video_duration - 0.1)
                padding = ImageClip(last_frame, duration=total_audio_duration - video_duration)
                padding = padding.with_effects([Resize(new_size=resolution)])
                final_video = concatenate_videoclips([final_video, padding])

            # Add audio
            final_video = final_video.with_audio(audio_clip)

            # ---- Render video ------------------------------------------------
            outfile = os.path.join(self.output_dir, self._generate_filename(audio_path, valid_images))
            final_video.write_videofile(
                outfile,
                fps=fps,
                threads=4,  # Optimize for multi-core
                preset='medium',
                codec="libx264",
                audio_codec="aac",
                temp_audiofile="temp-audio.m4a",
                remove_temp=True,
                logger=None,  # mute moviepy progress bar
            )

            # Explicit cleanup
            final_video.close()
            for c in clips:
                c.close()

        return {
            "success": True,
            "message": "Video generated successfully",
            "video_path": outfile,
            "video_url": f"/video/{os.path.basename(outfile)}",
            "duration": total_audio_duration,
            "file_size": os.path.getsize(outfile),
            "resolution": resolution,
        }

    # ---------------------------------------------------------------------
    # Image processing helpers
    # ---------------------------------------------------------------------

    def _create_image_clip(
        self,
        img_path: str,
        duration: float,
        resolution: Tuple[int, int],
        fps: int,
        enable_ken_burns: bool = True,
        zoom_factor: float = 1.1,
    ) -> VideoClip:
        # Create initial clip
        clip = ImageClip(img_path).with_duration(duration)

        # Get original dimensions
        w, h = clip.size
        target_w, target_h = resolution
        
        # Calculate scale factor to cover target resolution (avoiding black bars)
        scale_w = target_w / w
        scale_h = target_h / h
        scale = max(scale_w, scale_h)  # Use max to ensure coverage
        
        # Resize maintaining aspect ratio
        new_size = (int(w * scale), int(h * scale))
        clip = clip.with_effects([Resize(new_size=new_size)])
        
        # Center crop to exact target resolution
        if new_size != resolution:
            x_offset = (new_size[0] - target_w) // 2
            y_offset = (new_size[1] - target_h) // 2
            clip = clip.with_effects([
                Crop(x1=x_offset, y1=y_offset, 
                     x2=x_offset + target_w, y2=y_offset + target_h)
            ])

        # Apply Ken Burns effect if enabled
        if enable_ken_burns and duration > 1.0:
            clip = self._apply_ken_burns_effect(
                clip=clip,
                zoom_factor=zoom_factor,
                duration=duration,
                target_resolution=resolution
            )

        return clip.with_fps(fps)  # type: ignore

    def _apply_ken_burns_effect(
        self, 
        clip: ImageClip, 
        zoom_factor: float, 
        duration: float,
        target_resolution: Tuple[int, int]
    ) -> VideoClip:
        """Apply optimized Ken Burns effect with PIL for memory efficiency."""
        # Pre-calculate zoom parameters
        start_zoom = 1.0
        end_zoom = zoom_factor
        zoom_delta = end_zoom - start_zoom
        
        # Get original frame as PIL Image
        original_frame = clip.get_frame(0)
        original_pil = Image.fromarray(original_frame)
        orig_w, orig_h = original_pil.size
        
        def make_frame(t: float) -> np.ndarray:
            # Calculate current zoom level
            progress = min(1.0, t / duration)
            current_zoom = start_zoom + zoom_delta * progress
            
            # Calculate new dimensions
            new_w = int(orig_w * current_zoom)
            new_h = int(orig_h * current_zoom)
            
            # Resize with high-quality interpolation
            resized = original_pil.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            # Convert to numpy array
            resized_np = np.array(resized)
            
            # Center crop to target resolution
            x_center = new_w // 2
            y_center = new_h // 2
            crop_x1 = max(0, x_center - target_resolution[0] // 2)
            crop_y1 = max(0, y_center - target_resolution[1] // 2)
            crop_x2 = min(new_w, crop_x1 + target_resolution[0])
            crop_y2 = min(new_h, crop_y1 + target_resolution[1])
            
            return resized_np[crop_y1:crop_y2, crop_x1:crop_x2]

        return VideoClip(make_frame, duration=duration)

    @staticmethod
    def _generate_filename(audio_path: str, image_paths: List[str]) -> str:
        hash_input = audio_path + "|" + "|".join(sorted(image_paths))
        return f"video_{hashlib.md5(hash_input.encode()).hexdigest()[:12]}.mp4"