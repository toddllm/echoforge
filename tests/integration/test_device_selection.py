"""
Integration tests for device selection in voice generation.

These tests verify that the device selection functionality works
properly across different endpoints and device types.
"""

import os
import time
import pytest
import requests
import json
import torch
import torchaudio
import numpy as np
from pathlib import Path

# Server configuration
BASE_URL = os.environ.get("TEST_SERVER_URL", "http://localhost:8765")
API_PREFIX = "/api"

# Test configuration
TEST_TEXT = "This is a test of the voice generation system."
TEST_SPEAKER_ID = 1
TEST_TEMPERATURE = 0.7
TEST_TOP_K = 50
TEST_STYLE = "default"

# Skip tests that require CUDA if not available
skip_if_no_cuda = pytest.mark.skipif(
    not torch.cuda.is_available(),
    reason="CUDA not available on this system"
)


class TestDeviceSelection:
    """Test device selection functionality."""

    def setup_method(self):
        """Set up test environment."""
        # Ensure server is running
        try:
            response = requests.get(f"{BASE_URL}{API_PREFIX}/health")
            assert response.status_code == 200
        except Exception as e:
            pytest.skip(f"Test server not available at {BASE_URL}: {str(e)}")
        
        # Create output directory for test files
        self.output_dir = Path("test_outputs")
        os.makedirs(self.output_dir, exist_ok=True)
    
    def teardown_method(self):
        """Clean up after test."""
        # Clean up test files
        # (commented out to preserve files for inspection)
        # for file in self.output_dir.glob("*.wav"):
        #     file.unlink()

    def test_health_check(self):
        """Test health check endpoint."""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
    
    def test_diagnostic_endpoint(self):
        """Test diagnostic endpoint."""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/diagnostic")
        assert response.status_code == 200
        data = response.json()
        
        # Verify system information
        assert "system" in data
        assert "os" in data["system"]
        assert "python_version" in data["system"]
        
        # Verify CUDA information
        assert "cuda" in data
        assert "cuda_available" in data["cuda"]
        
        # Verify model information
        assert "model" in data
        assert "model_loaded" in data["model"]
        
        # Verify task information
        assert "tasks" in data
    
    def generate_voice(self, device):
        """Generate voice using the specified device."""
        url = f"{BASE_URL}{API_PREFIX}/generate"
        payload = {
            "text": f"{TEST_TEXT} Using {device} device.",
            "speaker_id": TEST_SPEAKER_ID,
            "temperature": TEST_TEMPERATURE,
            "top_k": TEST_TOP_K,
            "style": TEST_STYLE,
            "device": device
        }
        
        # Submit generation request
        response = requests.post(url, json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert "status" in data
        assert data["status"] == "processing"
        
        task_id = data["task_id"]
        output_file = None
        
        # Poll for task completion
        max_attempts = 30
        for attempt in range(max_attempts):
            task_url = f"{BASE_URL}{API_PREFIX}/tasks/{task_id}"
            task_response = requests.get(task_url)
            assert task_response.status_code == 200
            task_data = task_response.json()
            
            if task_data["status"] == "completed":
                assert "result" in task_data
                assert "file_url" in task_data["result"]
                
                # Download generated audio file
                file_url = task_data["result"]["file_url"]
                audio_url = f"{BASE_URL}{file_url}"
                audio_response = requests.get(audio_url)
                assert audio_response.status_code == 200
                
                # Save audio file
                output_file = self.output_dir / f"voice_{device}_{task_id}.wav"
                with open(output_file, "wb") as f:
                    f.write(audio_response.content)
                
                break
            elif task_data["status"] == "failed":
                assert False, f"Task failed: {task_data.get('error', 'Unknown error')}"
            
            time.sleep(1)
        
        assert output_file is not None, f"Task did not complete within {max_attempts} seconds"
        return output_file
    
    def test_cpu_generation(self):
        """Test voice generation using CPU device."""
        output_file = self.generate_voice("cpu")
        assert output_file.exists()
        
        # Verify audio file
        audio, sample_rate = torchaudio.load(output_file)
        assert audio.shape[0] == 1  # Mono channel
        assert sample_rate == 24000
        assert audio.shape[1] > 0   # Has samples
    
    @skip_if_no_cuda
    def test_cuda_generation(self):
        """Test voice generation using CUDA device."""
        output_file = self.generate_voice("cuda")
        assert output_file.exists()
        
        # Verify audio file
        audio, sample_rate = torchaudio.load(output_file)
        assert audio.shape[0] == 1  # Mono channel
        assert sample_rate == 24000
        assert audio.shape[1] > 0   # Has samples
    
    def test_auto_generation(self):
        """Test voice generation using auto device selection."""
        output_file = self.generate_voice("auto")
        assert output_file.exists()
        
        # Verify audio file
        audio, sample_rate = torchaudio.load(output_file)
        assert audio.shape[0] == 1  # Mono channel
        assert sample_rate == 24000
        assert audio.shape[1] > 0   # Has samples
    
    def test_device_consistency(self):
        """Test that all devices produce consistent results."""
        # Generate with all devices
        cpu_file = self.generate_voice("cpu")
        
        # Skip CUDA test if not available
        if torch.cuda.is_available():
            cuda_file = self.generate_voice("cuda")
            auto_file = self.generate_voice("auto")
            
            # Load audio files
            cpu_audio, _ = torchaudio.load(cpu_file)
            cuda_audio, _ = torchaudio.load(cuda_file)
            auto_audio, _ = torchaudio.load(auto_file)
            
            # Compare file sizes
            assert cpu_file.stat().st_size > 0
            assert cuda_file.stat().st_size > 0
            assert auto_file.stat().st_size > 0
            
            # Compare audio shapes
            assert cpu_audio.shape == cuda_audio.shape
            assert cpu_audio.shape == auto_audio.shape
            
            # Compare audio properties
            assert -1.0 <= cpu_audio.min().item() <= 0
            assert 0 <= cpu_audio.max().item() <= 1.0
            
            # Check similarity (may not be identical due to non-deterministic behavior)
            cpu_cuda_sim = torch.nn.functional.cosine_similarity(
                cpu_audio.flatten(), cuda_audio.flatten(), dim=0
            ).item()
            cpu_auto_sim = torch.nn.functional.cosine_similarity(
                cpu_audio.flatten(), auto_audio.flatten(), dim=0
            ).item()
            cuda_auto_sim = torch.nn.functional.cosine_similarity(
                cuda_audio.flatten(), auto_audio.flatten(), dim=0
            ).item()
            
            # Print similarity for debugging
            print(f"CPU-CUDA similarity: {cpu_cuda_sim}")
            print(f"CPU-Auto similarity: {cpu_auto_sim}")
            print(f"CUDA-Auto similarity: {cuda_auto_sim}")
        else:
            pytest.skip("CUDA not available, skipping device consistency test")


if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 