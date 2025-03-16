"""
Direct API tests for device selection commands.

These tests call the API directly with the exact commands used in manual testing,
validating that the documented commands work as expected.
"""

import os
import pytest
import subprocess
import json
import time
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:8765"
TEST_OUTPUT_DIR = Path("test_outputs/api_commands")


class TestDeviceAPI:
    """Test device selection API commands directly."""
    
    def setup_method(self):
        """Set up test environment."""
        # Create output directory
        os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
    
    def run_cmd(self, cmd):
        """Run a shell command and return the output."""
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True
        )
        return result.stdout, result.returncode
    
    def test_health_check(self):
        """Test health check endpoint."""
        cmd = f"curl -s {BASE_URL}/api/health"
        output, code = self.run_cmd(cmd)
        
        assert code == 0
        data = json.loads(output)
        assert data["status"] == "ok"
        assert "version" in data
    
    def test_diagnostic_endpoint(self):
        """Test diagnostic endpoint."""
        cmd = f"curl -s {BASE_URL}/api/diagnostic | python -m json.tool"
        output, code = self.run_cmd(cmd)
        
        assert code == 0
        # Check if output looks like valid JSON
        assert '"system":' in output
        assert '"cuda":' in output
        assert '"model":' in output
    
    def test_cpu_generation(self):
        """Test CPU generation using the documented command."""
        # The exact command from documentation
        cmd = f"""curl -X POST {BASE_URL}/api/generate -H "Content-Type: application/json" \\
            -d '{{"text": "Testing voice generation with CPU device selection.", "speaker_id": 1, "temperature": 0.7, "top_k": 50, "style": "default", "device": "cpu"}}' -s"""
        
        output, code = self.run_cmd(cmd)
        assert code == 0
        
        data = json.loads(output)
        assert "task_id" in data
        assert "status" in data
        assert data["status"] == "processing"
        
        # Get task ID
        task_id = data["task_id"]
        
        # Wait for task to complete
        self.wait_for_task(task_id)
    
    @pytest.mark.skipif(
        not os.popen("python -c \"import torch; print(torch.cuda.is_available())\"").read().strip() == "True",
        reason="CUDA not available"
    )
    def test_cuda_generation(self):
        """Test CUDA generation using the documented command."""
        # The exact command from documentation
        cmd = f"""curl -X POST {BASE_URL}/api/generate -H "Content-Type: application/json" \\
            -d '{{"text": "Testing voice generation with CUDA device selection.", "speaker_id": 1, "temperature": 0.7, "top_k": 50, "style": "default", "device": "cuda"}}' -s"""
        
        output, code = self.run_cmd(cmd)
        assert code == 0
        
        data = json.loads(output)
        assert "task_id" in data
        assert "status" in data
        assert data["status"] == "processing"
        
        # Get task ID
        task_id = data["task_id"]
        
        # Wait for task to complete
        self.wait_for_task(task_id)
    
    def test_auto_generation(self):
        """Test auto device selection using the documented command."""
        # The exact command from documentation
        cmd = f"""curl -X POST {BASE_URL}/api/generate -H "Content-Type: application/json" \\
            -d '{{"text": "Testing voice generation with auto device selection.", "speaker_id": 1, "temperature": 0.7, "top_k": 50, "style": "default", "device": "auto"}}' -s"""
        
        output, code = self.run_cmd(cmd)
        assert code == 0
        
        data = json.loads(output)
        assert "task_id" in data
        assert "status" in data
        assert data["status"] == "processing"
        
        # Get task ID
        task_id = data["task_id"]
        
        # Wait for task to complete
        self.wait_for_task(task_id)
    
    def wait_for_task(self, task_id, max_attempts=30):
        """Wait for a task to complete."""
        for attempt in range(max_attempts):
            # Check task status
            cmd = f"curl -s {BASE_URL}/api/tasks/{task_id}"
            output, code = self.run_cmd(cmd)
            
            assert code == 0
            data = json.loads(output)
            
            if data["status"] == "completed":
                # Task completed successfully
                assert "result" in data
                assert "file_url" in data["result"]
                
                # Download the file
                file_url = data["result"]["file_url"]
                file_name = f"api_test_{task_id}.wav"
                download_path = TEST_OUTPUT_DIR / file_name
                
                download_cmd = f"curl -s {BASE_URL}{file_url} -o {download_path}"
                _, download_code = self.run_cmd(download_cmd)
                
                assert download_code == 0
                assert download_path.exists()
                
                # Save the task info
                with open(TEST_OUTPUT_DIR / f"task_{task_id}.json", "w") as f:
                    json.dump(data, f, indent=2)
                
                return True
            
            elif data["status"] == "failed":
                pytest.fail(f"Task failed: {data.get('error', 'Unknown error')}")
            
            time.sleep(1)
        
        pytest.fail(f"Task did not complete within {max_attempts} seconds")
    
    def test_script_generation(self):
        """Test script-based generation with CPU."""
        # The exact command from documentation
        cmd = "cd ~/echoforge && source .venv/bin/activate && python -m scripts.generate_voice --text \"This is a test of voice generation using CPU.\" --device cpu"
        
        output, code = self.run_cmd(cmd)
        assert code == 0
        
        # Check if the output contains the path to the generated file
        assert "Generated speech saved to:" in output
    
    def test_audio_file_analysis(self):
        """Test audio file analysis command."""
        # First generate a file if not already exist
        self.test_cpu_generation()
        
        # Find a generated file
        wav_files = list(TEST_OUTPUT_DIR.glob("*.wav"))
        if not wav_files:
            pytest.skip("No WAV files found for analysis")
        
        # Python command to analyze properties (simplified from documentation)
        cmd = f"python -c \"import torchaudio; audio, sr = torchaudio.load('{wav_files[0]}'); print(f'Shape: {{audio.shape}}'); print(f'Sample rate: {{sr}}'); print(f'Min: {{audio.min().item()}}, Max: {{audio.max().item()}}')\""
        
        output, code = self.run_cmd(cmd)
        assert code == 0
        
        # Check if output contains audio properties
        assert "Shape:" in output
        assert "Sample rate:" in output
        assert "Min:" in output and "Max:" in output


if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 