import pytest
from unittest.mock import MagicMock, patch

from app.core.voice_generator import VoiceGenerator


class TestVoiceGenerator:
    def setup_method(self):
        self.generator = VoiceGenerator()
        
    def test_generate_voice_validates_inputs(self):
        # Test with empty text
        with pytest.raises(ValueError, match="Text cannot be empty"):
            self.generator.generate("", speaker_id=1)
            
        # Test with invalid speaker ID
        with pytest.raises(ValueError, match="Invalid speaker ID"):
            self.generator.generate("Hello world", speaker_id=-1)
    
    @patch("app.core.voice_generator.VoiceGenerator._load_model")
    def test_generate_voice_produces_output(self, mock_load_model):
        # Mock the model
        mock_model = MagicMock()
        mock_model.generate.return_value = b"audio_data"
        mock_load_model.return_value = mock_model
        
        # Generate voice
        result = self.generator.generate("Hello world", speaker_id=1)
        
        # Assert result
        assert result is not None
        assert isinstance(result, bytes)
        assert result == b"audio_data"
        
        # Verify model called with correct parameters
        mock_model.generate.assert_called_once()
        args, kwargs = mock_model.generate.call_args
        assert "Hello world" in args or kwargs.values()
        assert 1 in args or kwargs.values() 