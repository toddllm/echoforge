"""
Unit tests for the VoiceGenerator class.
"""

import os
import uuid
import time
import tempfile
import unittest
import torch
from unittest.mock import patch, MagicMock, call
from pathlib import Path

from app.api.voice_generator import VoiceGenerator
from app.models import CSMModel, PlaceholderCSMModel, CSMModelError


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

    @patch('app.api.voice_generator.os.makedirs')
    @patch('app.api.voice_generator.logger')
    def test_init(self, mock_logger, mock_makedirs):
        """Test initialization of VoiceGenerator."""
        # Test with default parameters
        generator = VoiceGenerator()
        mock_logger.info.assert_called()
        
        # Test with custom parameters
        custom_model_path = "/path/to/model"
        custom_output_dir = "/path/to/output"
        generator = VoiceGenerator(model_path=custom_model_path, output_dir=custom_output_dir)
        self.assertEqual(generator.model_path, custom_model_path)
        self.assertEqual(generator.output_dir, custom_output_dir)
        
        # Test with use_placeholder parameter
        generator = VoiceGenerator(use_placeholder=True)
        self.assertTrue(generator.use_placeholder)

    @patch('app.api.voice_generator.create_csm_model')
    @patch('app.api.voice_generator.logger')
    def test_load_model_success(self, mock_logger, mock_create_csm_model):
        """Test successful model loading."""
        # Setup mock CSM model
        mock_model = MagicMock(spec=CSMModel)
        mock_create_csm_model.return_value = mock_model
        
        # Set is_test_mode to False to avoid using mock model
        self.voice_generator.is_test_mode = False
        
        # Mock _determine_device to return 'cpu'
        with patch.object(self.voice_generator, '_determine_device', return_value='cpu'):
            # Test loading
            self.voice_generator.model = None  # Reset model
            result = self.voice_generator.load_model()
            
            # Verify
            self.assertTrue(result)
            self.assertIsNotNone(self.voice_generator.model)
            mock_logger.info.assert_any_call("CSM model loaded successfully on device: %s", 'cpu')
            
            # Verify create_csm_model was called with the right parameters
            mock_create_csm_model.assert_called_once()
            args, kwargs = mock_create_csm_model.call_args
            self.assertEqual(kwargs["model_path"], self.voice_generator.model_path)
            self.assertEqual(kwargs["use_placeholder"], self.voice_generator.use_placeholder)

    @patch('app.api.voice_generator.create_csm_model')
    @patch('app.api.voice_generator.logger')
    def test_load_model_placeholder(self, mock_logger, mock_create_csm_model):
        """Test loading with placeholder model."""
        # Setup mock placeholder model
        mock_model = MagicMock(spec=PlaceholderCSMModel)
        mock_create_csm_model.return_value = mock_model
        
        # Set is_test_mode to False to avoid using mock model
        self.voice_generator.is_test_mode = False
        
        # Test loading
        self.voice_generator.model = None  # Reset model
        result = self.voice_generator.load_model()
        
        # Verify
        self.assertTrue(result)
        self.assertIsNotNone(self.voice_generator.model)
        mock_logger.warning.assert_called_with("Using placeholder CSM model - real model not available")

    @patch('app.api.voice_generator.create_csm_model')
    @patch('app.api.voice_generator.logger')
    def test_load_model_failure(self, mock_logger, mock_create_csm_model):
        """Test model loading failure."""
        # Setup mock to raise exception
        mock_create_csm_model.side_effect = Exception("Model loading failed")
        
        # Set is_test_mode to False to avoid using mock model
        self.voice_generator.is_test_mode = False
        
        # Test loading
        self.voice_generator.model = None  # Reset model
        result = self.voice_generator.load_model()
        
        # Verify
        self.assertFalse(result)
        self.assertIsNone(self.voice_generator.model)
        mock_logger.error.assert_called_with("Could not load CSM model: %s", "Model loading failed")

    @patch('app.api.voice_generator.torch.cuda.is_available')
    @patch('app.api.voice_generator.torch.cuda.get_device_properties')
    @patch('app.api.voice_generator.torch.cuda.memory_allocated')
    @patch('app.api.voice_generator.logger')
    def test_determine_device_cuda_available(self, mock_logger, mock_memory_allocated, mock_get_device_properties, mock_cuda_available):
        """Test device determination when CUDA is available with enough memory."""
        # Setup mocks
        mock_cuda_available.return_value = True
        mock_device = MagicMock()
        mock_device.total_memory = 8 * 1024 * 1024 * 1024  # 8 GB
        mock_get_device_properties.return_value = mock_device
        mock_memory_allocated.return_value = 0
        
        # Test device determination
        device = self.voice_generator._determine_device()
        
        # Verify
        self.assertEqual(device, "cuda")
        mock_logger.info.assert_called_with(f"Using CUDA device with {8.00:.2f} GB free memory")

    @patch('app.api.voice_generator.torch.cuda.is_available')
    @patch('app.api.voice_generator.torch.cuda.get_device_properties')
    @patch('app.api.voice_generator.torch.cuda.memory_allocated')
    @patch('app.api.voice_generator.logger')
    def test_determine_device_not_enough_memory(self, mock_logger, mock_memory_allocated, mock_get_device_properties, mock_cuda_available):
        """Test device determination when CUDA is available but not enough memory."""
        # Setup mocks
        mock_cuda_available.return_value = True
        mock_device = MagicMock()
        mock_device.total_memory = 2 * 1024 * 1024 * 1024  # 2 GB
        mock_get_device_properties.return_value = mock_device
        mock_memory_allocated.return_value = 1.5 * 1024 * 1024 * 1024  # 1.5 GB used
        
        # Test device determination
        device = self.voice_generator._determine_device()
        
        # Verify
        self.assertEqual(device, "cpu")
        mock_logger.warning.assert_called_with(f"Not enough GPU memory ({0.50:.2f} GB free), falling back to CPU")

    @patch('app.api.voice_generator.torch.cuda.is_available')
    @patch('app.api.voice_generator.logger')
    def test_determine_device_cuda_not_available(self, mock_logger, mock_cuda_available):
        """Test device determination when CUDA is not available."""
        # Setup mocks
        mock_cuda_available.return_value = False
        
        # Test device determination
        device = self.voice_generator._determine_device()
        
        # Verify
        self.assertEqual(device, "cpu")
        mock_logger.info.assert_called_with("CUDA not available, using CPU")

    @patch('app.api.voice_generator.logger')
    def test_generate_with_csm_model(self, mock_logger):
        """Test speech generation with CSM model."""
        # Setup mock model
        mock_model = MagicMock()
        mock_model.generate_speech.return_value = (torch.zeros(24000), 24000)
        self.voice_generator.model = mock_model
        
        # Test generation
        with patch('os.path.exists', return_value=True):
            output_path, url = self.voice_generator.generate(
                text="Hello world",
                speaker_id=1,
                temperature=0.7,
                top_k=30
            )
        
        # Verify
        self.assertIsNotNone(output_path)
        self.assertIsNotNone(url)
        self.assertTrue(output_path.endswith(".wav"))
        self.assertTrue(url.startswith("/voices/"))
        
        # Verify model was called with the right parameters
        mock_model.generate_speech.assert_called_once()
        args, kwargs = mock_model.generate_speech.call_args
        self.assertEqual(kwargs["text"], "Hello world")
        self.assertEqual(kwargs["speaker_id"], 1)
        self.assertEqual(kwargs["temperature"], 0.7)
        self.assertEqual(kwargs["top_k"], 30)
        
        # Verify audio was saved
        mock_model.save_audio.assert_called_once()
        args, kwargs = mock_model.save_audio.call_args
        self.assertEqual(args[0].shape, torch.Size([24000]))
        self.assertEqual(args[1], 24000)
        self.assertEqual(args[2], output_path)

    @patch('app.api.voice_generator.logger')
    def test_generate_model_not_loaded(self, mock_logger):
        """Test generation when model is not loaded."""
        # Setup
        self.voice_generator.model = None
        
        # Mock load_model to fail
        with patch.object(self.voice_generator, 'load_model', return_value=False):
            # Test generation
            output_path, url = self.voice_generator.generate("Hello world")
        
        # Verify
        self.assertIsNone(output_path)
        self.assertIsNone(url)
        mock_logger.error.assert_called_with("Failed to load model")

    @patch('app.api.voice_generator.logger')
    def test_generate_model_error(self, mock_logger):
        """Test generation when model raises an error."""
        # Setup mock model to raise an error
        mock_model = MagicMock()
        mock_model.generate_speech.side_effect = CSMModelError("Generation failed")
        self.voice_generator.model = mock_model
        
        # Test generation
        output_path, url = self.voice_generator.generate("Hello world")
        
        # Verify
        self.assertIsNone(output_path)
        self.assertIsNone(url)
        mock_logger.error.assert_called_with("CSM model error: Generation failed")

    @patch('app.api.voice_generator.logger')
    def test_generate_file_not_created(self, mock_logger):
        """Test generation when output file is not created."""
        # Setup mock model
        mock_model = MagicMock()
        mock_model.generate_speech.return_value = (torch.zeros(24000), 24000)
        self.voice_generator.model = mock_model
        
        # Test generation with file not existing
        with patch('os.path.exists', return_value=False):
            output_path, url = self.voice_generator.generate("Hello world")
        
        # Verify
        self.assertIsNone(output_path)
        self.assertIsNone(url)
        # Check that error was logged, but don't check the exact message
        mock_logger.error.assert_called()
        self.assertIn("Output file not created", mock_logger.error.call_args[0][0])

    @patch('app.api.voice_generator.Path')
    def test_list_available_voices(self, mock_path):
        """Test listing available voices."""
        # Setup mock files
        mock_dir = MagicMock()
        mock_path.return_value = mock_dir
        mock_dir.exists.return_value = True
        
        # Create mock WAV files
        mock_file1 = MagicMock()
        mock_file1.name = "voice_1234567890_abcdef.wav"
        mock_file1.stat.return_value.st_size = 1000
        mock_file1.stat.return_value.st_ctime = 1000000
        mock_file1.stat.return_value.st_mtime = 1000001
        mock_file1.relative_to.return_value = Path("voice_1234567890_abcdef.wav")
        
        mock_file2 = MagicMock()
        mock_file2.name = "voice_9876543210_ghijkl.wav"
        mock_file2.stat.return_value.st_size = 2000
        mock_file2.stat.return_value.st_ctime = 2000000
        mock_file2.stat.return_value.st_mtime = 2000001
        mock_file2.relative_to.return_value = Path("voice_9876543210_ghijkl.wav")
        
        mock_dir.glob.return_value = [mock_file1, mock_file2]
        
        # Test listing voices
        voices = self.voice_generator.list_available_voices()
        
        # Verify
        self.assertEqual(len(voices), 2)
        self.assertEqual(voices[0]["filename"], "voice_9876543210_ghijkl.wav")
        self.assertEqual(voices[0]["url"], "/voices/voice_9876543210_ghijkl.wav")
        self.assertEqual(voices[0]["size_bytes"], 2000)
        self.assertEqual(voices[1]["filename"], "voice_1234567890_abcdef.wav")
        self.assertEqual(voices[1]["url"], "/voices/voice_1234567890_abcdef.wav")
        self.assertEqual(voices[1]["size_bytes"], 1000)

    @patch('app.api.voice_generator.logger')
    @patch('app.api.voice_generator.Path')
    def test_cleanup_old_files(self, mock_path, mock_logger):
        """Test cleaning up old files."""
        # Setup mock files
        mock_dir = MagicMock()
        mock_path.return_value = mock_dir
        mock_dir.exists.return_value = True
        
        # Create mock WAV files
        mock_file1 = MagicMock()
        mock_file1.stat.return_value.st_mtime = time.time() - 3600  # 1 hour old
        
        mock_file2 = MagicMock()
        mock_file2.stat.return_value.st_mtime = time.time() - 86400  # 24 hours old
        
        mock_file3 = MagicMock()
        mock_file3.stat.return_value.st_mtime = time.time() - 172800  # 48 hours old
        
        mock_dir.glob.return_value = [mock_file1, mock_file2, mock_file3]
        
        # Test cleanup with 12 hour max age
        deleted = self.voice_generator.cleanup_old_files(max_age_hours=12)
        
        # Verify
        self.assertEqual(deleted, 2)  # 2 files older than 12 hours
        mock_file1.unlink.assert_not_called()
        mock_file2.unlink.assert_called_once()
        mock_file3.unlink.assert_called_once()
        # Check that info was logged, but don't check the exact message
        mock_logger.info.assert_called()
        self.assertIn("Cleaned up", mock_logger.info.call_args[0][0])

    @patch('app.api.voice_generator.logger')
    @patch('app.api.voice_generator.Path')
    def test_cleanup_error(self, mock_path, mock_logger):
        """Test error handling during cleanup."""
        # Setup mock to raise exception
        mock_dir = MagicMock()
        mock_path.return_value = mock_dir
        mock_dir.exists.return_value = True
        mock_dir.glob.side_effect = Exception("Glob error")
        
        # Test cleanup
        deleted = self.voice_generator.cleanup_old_files()
        
        # Verify
        self.assertEqual(deleted, 0)
        mock_logger.error.assert_called_with("Error cleaning up old files: Glob error")


class TestMockModel(unittest.TestCase):
    """Test suite for the MockModel class."""
    
    def setUp(self):
        """Set up test case."""
        from app.api.voice_generator import MockModel
        self.mock_model = MockModel()
    
    def test_generate_speech(self):
        """Test generating speech with the mock model."""
        # Test with default parameters
        audio, sample_rate = self.mock_model.generate_speech("Hello world")
        
        # Verify
        self.assertEqual(sample_rate, 24000)
        self.assertGreater(audio.shape[0], 0)
        self.assertLessEqual(audio.max(), 1.0)
        self.assertGreaterEqual(audio.min(), -1.0)
        
        # Test with different parameters
        audio2, _ = self.mock_model.generate_speech("Hello world", speaker_id=2, temperature=0.8, top_k=40)
        
        # Verify different parameters produce different audio
        self.assertFalse(torch.allclose(audio, audio2))
    
    @patch('torchaudio.save')
    def test_save_audio(self, mock_save):
        """Test saving audio with the mock model."""
        # Generate audio
        audio, sample_rate = self.mock_model.generate_speech("Hello world")
        
        # Save audio
        output_path = "/tmp/test.wav"
        saved_path = self.mock_model.save_audio(audio, sample_rate, output_path)
        
        # Verify
        self.assertEqual(saved_path, output_path)
        mock_save.assert_called_once()
        args, kwargs = mock_save.call_args
        self.assertEqual(args[0], output_path)
        self.assertTrue(torch.equal(args[1], audio.unsqueeze(0)))
        self.assertEqual(args[2], sample_rate)


if __name__ == "__main__":
    unittest.main() 