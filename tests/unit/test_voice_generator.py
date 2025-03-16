"""
Unit tests for the VoiceGenerator class.
"""

import os
import uuid
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

from app.api.voice_generator import VoiceGenerator


class TestVoiceGenerator(unittest.TestCase):
    """Test suite for VoiceGenerator class."""

    def setUp(self):
        """Set up test case with a temporary output directory."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = self.temp_dir.name
        
        # Create voice generator with temp output dir
        self.voice_generator = VoiceGenerator(output_dir=self.output_dir)
        
        # Create a mock for the model
        self.mock_model = MagicMock()
        self.voice_generator.model = self.mock_model

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    @patch('app.api.voice_generator.os.path.exists')
    @patch('app.api.voice_generator.logger')
    def test_init(self, mock_logger, mock_exists):
        """Test initialization of VoiceGenerator."""
        # Test with default parameters
        generator = VoiceGenerator()
        mock_logger.info.assert_called_once()
        
        # Test with custom parameters
        custom_model_path = "/path/to/model"
        custom_output_dir = "/path/to/output"
        generator = VoiceGenerator(model_path=custom_model_path, output_dir=custom_output_dir)
        self.assertEqual(generator.model_path, custom_model_path)
        self.assertEqual(generator.output_dir, custom_output_dir)

    @patch('app.api.voice_generator.logger')
    def test_load_model_success(self, mock_logger):
        """Test successful model loading."""
        # Setup mock imports and classes
        with patch('app.api.voice_generator.CSMModel', autospec=True) as mock_csm_model:
            mock_model = MagicMock()
            mock_csm_model.from_pretrained.return_value = mock_model
            
            # Test loading
            self.voice_generator.model = None  # Reset model
            result = self.voice_generator.load_model()
            
            # Verify
            self.assertTrue(result)
            self.assertIsNotNone(self.voice_generator.model)
            mock_logger.info.assert_called_with("Model loaded successfully")

    @patch('app.api.voice_generator.logger')
    def test_load_model_fallback(self, mock_logger):
        """Test fallback to VoiceCloner if CSMModel isn't available."""
        # Setup mock to raise ImportError for CSMModel but succeed with VoiceCloner
        with patch('app.api.voice_generator.CSMModel', side_effect=ImportError), \
             patch('app.api.voice_generator.VoiceCloner', autospec=True) as mock_voice_cloner:
            
            mock_model = MagicMock()
            mock_voice_cloner.return_value = mock_model
            
            # Test loading
            self.voice_generator.model = None  # Reset model
            result = self.voice_generator.load_model()
            
            # Verify
            self.assertTrue(result)
            self.assertIsNotNone(self.voice_generator.model)
            mock_logger.info.assert_called_with("Loaded model using VoiceCloner")

    @patch('app.api.voice_generator.logger')
    def test_load_model_failure(self, mock_logger):
        """Test model loading failure."""
        # Setup mocks to fail on both import attempts
        with patch('app.api.voice_generator.CSMModel', side_effect=ImportError), \
             patch('app.api.voice_generator.VoiceCloner', side_effect=ImportError):
            
            # Test loading
            self.voice_generator.model = None  # Reset model
            result = self.voice_generator.load_model()
            
            # Verify
            self.assertFalse(result)
            self.assertIsNone(self.voice_generator.model)
            mock_logger.error.assert_called_with("Could not import CSM model or VoiceCloner")

    @patch('app.api.voice_generator.logger')
    def test_generate_with_csm_model(self, mock_logger):
        """Test generation with CSMModel."""
        # Setup mock model with generate_speech method
        self.voice_generator.model = MagicMock()
        self.voice_generator.model.generate_speech = MagicMock()
        
        # Mock os.path.exists to return True for the output file
        with patch('app.api.voice_generator.os.path.exists', return_value=True), \
             patch('app.api.voice_generator.uuid.uuid4', return_value=MagicMock(hex='12345678')):
            
            # Test generation
            output_path, error = self.voice_generator.generate(
                text="Hello world",
                speaker_id=1,
                temperature=0.5,
                top_k=80,
                style="short"
            )
            
            # Verify
            self.assertIsNotNone(output_path)
            self.assertIsNone(error)
            self.voice_generator.model.generate_speech.assert_called_once()
            self.assertIn('voice_1_12345678.wav', output_path)

    @patch('app.api.voice_generator.logger')
    def test_generate_with_voice_cloner(self, mock_logger):
        """Test generation with VoiceCloner."""
        # Setup mock model with generate_direct method
        self.voice_generator.model = MagicMock()
        self.voice_generator.model.generate_speech = None
        self.voice_generator.model.generate_direct = MagicMock()
        
        # Mock os.path.exists to return True for the output file
        with patch('app.api.voice_generator.os.path.exists', return_value=True), \
             patch('app.api.voice_generator.uuid.uuid4', return_value=MagicMock(hex='12345678')):
            
            # Test generation
            output_path, error = self.voice_generator.generate(
                text="Hello world",
                speaker_id=1,
                temperature=0.5,
                top_k=80,
                style="short"
            )
            
            # Verify
            self.assertIsNotNone(output_path)
            self.assertIsNone(error)
            self.voice_generator.model.generate_direct.assert_called_once()
            self.assertIn('voice_1_12345678.wav', output_path)

    @patch('app.api.voice_generator.logger')
    def test_generate_model_not_loaded(self, mock_logger):
        """Test generation when model is not loaded."""
        # Setup
        self.voice_generator.model = None
        
        # Mock load_model to return False
        with patch.object(self.voice_generator, 'load_model', return_value=False):
            # Test generation
            output_path, error = self.voice_generator.generate(text="Hello world")
            
            # Verify
            self.assertIsNone(output_path)
            self.assertEqual(error, "Failed to load voice model")

    @patch('app.api.voice_generator.logger')
    def test_generate_model_error(self, mock_logger):
        """Test generation when model raises an error."""
        # Setup mock model that raises an exception
        self.voice_generator.model = MagicMock()
        self.voice_generator.model.generate_speech = MagicMock(side_effect=RuntimeError("Test error"))
        
        # Test generation
        output_path, error = self.voice_generator.generate(text="Hello world")
        
        # Verify
        self.assertIsNone(output_path)
        self.assertIn("Error generating voice", error)
        mock_logger.error.assert_called()

    @patch('app.api.voice_generator.logger')
    def test_generate_file_not_created(self, mock_logger):
        """Test generation when output file is not created."""
        # Setup mock model
        self.voice_generator.model = MagicMock()
        self.voice_generator.model.generate_speech = MagicMock()
        
        # Mock os.path.exists to return False for the output file
        with patch('app.api.voice_generator.os.path.exists', return_value=False):
            # Test generation
            output_path, error = self.voice_generator.generate(text="Hello world")
            
            # Verify
            self.assertIsNone(output_path)
            self.assertEqual(error, "Voice file was not created")

    def test_list_available_voices(self):
        """Test listing available voices."""
        voices = self.voice_generator.list_available_voices()
        
        # Verify returned list format
        self.assertIsInstance(voices, list)
        self.assertGreater(len(voices), 0)
        
        # Check voice structure
        for voice in voices:
            self.assertIn("speaker_id", voice)
            self.assertIn("name", voice)
            self.assertIn("gender", voice)
            self.assertIn("description", voice)

    @patch('app.api.voice_generator.logger')
    @patch('app.api.voice_generator.Path')
    def test_cleanup_old_files(self, mock_path, mock_logger):
        """Test cleaning up old files."""
        # Create mock files
        mock_files = [MagicMock(), MagicMock(), MagicMock()]
        mock_path.return_value.glob.return_value = mock_files
        
        # Make old files
        for mock_file in mock_files:
            mock_file.stat.return_value.st_mtime = time.time() - (25 * 3600)  # 25 hours ago
            mock_file.unlink = MagicMock()
        
        # Test cleanup
        count = self.voice_generator.cleanup_old_files(max_age_hours=24)
        
        # Verify
        self.assertEqual(count, 3)
        for mock_file in mock_files:
            mock_file.unlink.assert_called_once()
        mock_logger.info.assert_called_with("Cleaned up 3 old voice files")

    @patch('app.api.voice_generator.logger')
    @patch('app.api.voice_generator.Path')
    def test_cleanup_error(self, mock_path, mock_logger):
        """Test error handling during cleanup."""
        # Mock Path.glob to raise an exception
        mock_path.return_value.glob.side_effect = RuntimeError("Test error")
        
        # Test cleanup
        count = self.voice_generator.cleanup_old_files()
        
        # Verify
        self.assertEqual(count, 0)
        mock_logger.error.assert_called()


if __name__ == '__main__':
    unittest.main() 