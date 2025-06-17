"""
Unit tests for video service.
"""

import unittest
import tempfile
import os
from pathlib import Path
import shutil
from video_editor import VideoEditor, VideoSettings, TransitionType, TextPosition

class TestVideoService(unittest.TestCase):
    """Test cases for video service functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.video_editor = VideoEditor()
        
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_video_settings_creation(self):
        """Test video settings creation."""
        settings = VideoSettings(
            fps=30,
            width=1920,
            height=1080,
            transition_type=TransitionType.FADE
        )
        
        self.assertEqual(settings.fps, 30)
        self.assertEqual(settings.width, 1920)
        self.assertEqual(settings.height, 1080)
        self.assertEqual(settings.transition_type, TransitionType.FADE)
    
    def test_video_editor_initialization(self):
        """Test video editor initialization."""
        editor = VideoEditor()
        self.assertIsNotNone(editor.settings)
        self.assertEqual(editor.settings.fps, 24)  # Default value
        
        custom_settings = VideoSettings(fps=30)
        custom_editor = VideoEditor(custom_settings)
        self.assertEqual(custom_editor.settings.fps, 30)
    
    def test_validate_resources_missing_folder(self):
        """Test resource validation with missing folder."""
        with self.assertRaises(FileNotFoundError):
            self.video_editor.validate_resources("/nonexistent/folder", "/nonexistent/audio.mp3")
    
    def test_transition_types(self):
        """Test transition type enumeration."""
        self.assertEqual(TransitionType.NONE.value, "none")
        self.assertEqual(TransitionType.FADE.value, "fade")
        self.assertEqual(TransitionType.CROSSFADE.value, "crossfade")
        self.assertEqual(TransitionType.SLIDE.value, "slide")
    
    def test_text_positions(self):
        """Test text position enumeration."""
        self.assertEqual(TextPosition.TOP.value, "top")
        self.assertEqual(TextPosition.BOTTOM.value, "bottom")
        self.assertEqual(TextPosition.CENTER.value, "center")
        self.assertEqual(TextPosition.TOP_LEFT.value, "top_left")
    
    def test_settings_defaults(self):
        """Test default settings values."""
        settings = VideoSettings()
        self.assertEqual(settings.fps, 24)
        self.assertEqual(settings.width, 1024)
        self.assertEqual(settings.height, 1024)
        self.assertEqual(settings.text_color, "white")
        self.assertEqual(settings.bg_color, "black")

if __name__ == "__main__":
    unittest.main()
