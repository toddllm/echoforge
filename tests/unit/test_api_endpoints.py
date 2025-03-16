"""
Unit tests for API endpoints.
"""

import os
import json
import unittest
import asyncio
from unittest.mock import patch, MagicMock

from app.api.router import health_check, system_diagnostic, list_voices, generate_voice, get_task_status, VoiceGenerationRequest
from app.core import config


class TestAPIEndpoints(unittest.TestCase):
    """Test suite for API endpoints."""

    def setUp(self):
        """Set up test environment."""
        # Set test mode environment variable
        os.environ["ECHOFORGE_TEST"] = "true"

    def tearDown(self):
        """Clean up after tests."""
        # Unset test mode environment variable
        if "ECHOFORGE_TEST" in os.environ:
            del os.environ["ECHOFORGE_TEST"]

    def test_health_check(self):
        """Test health check endpoint."""
        # Call the endpoint function directly using asyncio
        response = asyncio.run(health_check())
        
        # Verify response
        self.assertEqual(response["status"], "ok")
        self.assertEqual(response["version"], config.APP_VERSION)

    @patch("app.api.router.platform")
    @patch("app.api.router.psutil")
    @patch("app.api.router.torch")
    def test_diagnostic_endpoint(self, mock_torch, mock_psutil, mock_platform):
        """Test diagnostic endpoint."""
        # Mock platform data
        mock_platform.system.return_value = "Linux"
        mock_platform.version.return_value = "5.10.0"
        mock_platform.python_version.return_value = "3.9.0"
        
        # Mock psutil data
        mock_memory = MagicMock()
        mock_memory.total = 16 * 1024 * 1024 * 1024  # 16 GB
        mock_memory.available = 8 * 1024 * 1024 * 1024  # 8 GB
        mock_psutil.virtual_memory.return_value = mock_memory
        mock_psutil.cpu_count.side_effect = lambda logical: 16 if logical else 8
        
        # Mock torch data
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 1
        mock_torch.version.cuda = "11.1"
        
        # Mock device properties
        mock_device_props = MagicMock()
        mock_device_props.name = "NVIDIA GeForce RTX 3080"
        mock_device_props.total_memory = 10 * 1024 * 1024 * 1024  # 10 GB
        mock_device_props.major = 8
        mock_device_props.minor = 6
        mock_torch.cuda.get_device_properties.return_value = mock_device_props
        
        # Call the endpoint function directly using asyncio
        response = asyncio.run(system_diagnostic())
        
        # Verify response
        self.assertEqual(response["system"]["os"], "Linux")
        self.assertEqual(response["system"]["os_version"], "5.10.0")
        self.assertEqual(response["system"]["python_version"], "3.9.0")
        self.assertEqual(response["system"]["cpu_count"], 8)
        self.assertEqual(response["system"]["logical_cpu_count"], 16)
        self.assertEqual(response["system"]["memory_total_gb"], 16.0)
        self.assertEqual(response["system"]["memory_available_gb"], 8.0)
        
        # Check CUDA info
        self.assertTrue(response["cuda"]["cuda_available"])
        self.assertEqual(response["cuda"]["cuda_device_count"], 1)
        self.assertEqual(response["cuda"]["cuda_version"], "11.1")
        self.assertEqual(len(response["cuda"]["devices"]), 1)
        self.assertEqual(response["cuda"]["devices"][0]["name"], "NVIDIA GeForce RTX 3080")
        self.assertEqual(response["cuda"]["devices"][0]["total_memory_gb"], 10.0)
        self.assertEqual(response["cuda"]["devices"][0]["major"], 8)
        self.assertEqual(response["cuda"]["devices"][0]["minor"], 6)

    @patch("app.api.router.torch.cuda.is_available")
    def test_diagnostic_endpoint_no_cuda(self, mock_cuda_available):
        """Test diagnostic endpoint when CUDA is not available."""
        # Mock CUDA availability
        mock_cuda_available.return_value = False
        
        # Call the endpoint function directly using asyncio
        response = asyncio.run(system_diagnostic())
        
        # Verify response
        self.assertFalse(response["cuda"]["cuda_available"])
        self.assertEqual(response["cuda"]["cuda_device_count"], 0)
        self.assertNotIn("devices", response["cuda"])

    @patch("app.api.router.voice_generator")
    def test_diagnostic_endpoint_with_model(self, mock_voice_generator):
        """Test diagnostic endpoint with model information."""
        # Mock voice generator
        mock_voice_generator.model = MagicMock()
        mock_voice_generator.model_path = "/path/to/model"
        mock_voice_generator.output_dir = "/path/to/output"
        mock_voice_generator.list_available_voices.return_value = [
            {"speaker_id": 1, "name": "Voice 1"},
            {"speaker_id": 2, "name": "Voice 2"}
        ]
        
        # Call the endpoint function directly using asyncio
        response = asyncio.run(system_diagnostic())
        
        # Verify response
        self.assertTrue(response["model"]["model_loaded"])
        self.assertEqual(response["model"]["model_path"], "/path/to/model")
        self.assertEqual(response["model"]["output_dir"], "/path/to/output")
        self.assertEqual(response["model"]["available_voices"], 2)

    @patch("app.api.router.task_manager")
    def test_diagnostic_endpoint_with_tasks(self, mock_task_manager):
        """Test diagnostic endpoint with task information."""
        # Mock task manager
        mock_task_manager.count_active_tasks.return_value = 2
        mock_task_manager.count_completed_tasks.return_value = 5
        mock_task_manager.count_failed_tasks.return_value = 1
        
        # Call the endpoint function directly using asyncio
        response = asyncio.run(system_diagnostic())
        
        # Verify response
        self.assertEqual(response["tasks"]["active_tasks"], 2)
        self.assertEqual(response["tasks"]["completed_tasks"], 5)
        self.assertEqual(response["tasks"]["failed_tasks"], 1)

    def test_list_voices_test_mode(self):
        """Test listing voices in test mode."""
        # Call the endpoint function directly using asyncio
        response = asyncio.run(list_voices())
        
        # Verify response
        self.assertEqual(len(response), 2)
        self.assertEqual(response[0]["speaker_id"], 1)
        self.assertEqual(response[0]["name"], "Male Commander")
        self.assertEqual(response[0]["gender"], "male")
        self.assertEqual(response[1]["speaker_id"], 2)
        self.assertEqual(response[1]["name"], "Female Scientist")
        self.assertEqual(response[1]["gender"], "female")

    @patch("app.api.router.voice_generator")
    def test_list_voices_production_mode(self, mock_voice_generator):
        """Test listing voices in production mode."""
        # Set up mock data
        mock_voices = [
            {
                "speaker_id": 1,
                "name": "Voice 1",
                "gender": "male",
                "description": "Description 1"
            },
            {
                "speaker_id": 2,
                "name": "Voice 2",
                "gender": "female",
                "description": "Description 2"
            },
            {
                "speaker_id": 3,
                "name": "Voice 3",
                "gender": "neutral",
                "description": "Description 3"
            }
        ]
        mock_voice_generator.list_available_voices.return_value = mock_voices
        
        # Temporarily unset test mode
        if "ECHOFORGE_TEST" in os.environ:
            test_mode = os.environ["ECHOFORGE_TEST"]
            del os.environ["ECHOFORGE_TEST"]
        else:
            test_mode = None
        
        try:
            # Call the endpoint function directly using asyncio
            response = asyncio.run(list_voices())
            
            # Verify response
            self.assertEqual(len(response), 3)
            self.assertEqual(response[0]["speaker_id"], 1)
            self.assertEqual(response[0]["name"], "Voice 1")
            self.assertEqual(response[1]["speaker_id"], 2)
            self.assertEqual(response[1]["name"], "Voice 2")
            self.assertEqual(response[2]["speaker_id"], 3)
            self.assertEqual(response[2]["name"], "Voice 3")
        finally:
            # Restore test mode
            if test_mode is not None:
                os.environ["ECHOFORGE_TEST"] = test_mode

    @patch("app.api.router.voice_generator")
    def test_list_voices_error(self, mock_voice_generator):
        """Test listing voices when an error occurs."""
        # Set up mock to raise an exception
        mock_voice_generator.list_available_voices.side_effect = Exception("Test error")
        
        # Temporarily unset test mode
        if "ECHOFORGE_TEST" in os.environ:
            test_mode = os.environ["ECHOFORGE_TEST"]
            del os.environ["ECHOFORGE_TEST"]
        else:
            test_mode = None
        
        try:
            # Call the endpoint function and expect an exception
            with self.assertRaises(Exception):
                asyncio.run(list_voices())
        finally:
            # Restore test mode
            if test_mode is not None:
                os.environ["ECHOFORGE_TEST"] = test_mode

    @patch("app.api.router.BackgroundTasks")
    def test_generate_voice_test_mode(self, mock_background_tasks):
        """Test generating voice in test mode."""
        # Create request
        request = VoiceGenerationRequest(
            text="Hello world",
            speaker_id=1,
            temperature=0.7,
            top_k=50,
            style="default"
        )
        
        # Call the endpoint function directly using asyncio
        response = asyncio.run(generate_voice(mock_background_tasks, request))
        
        # Verify response
        self.assertIn("task_id", response)
        self.assertEqual(response["status"], "processing")
        
        # Verify background task was not added
        mock_background_tasks.add_task.assert_not_called()

    @patch("app.api.router.BackgroundTasks")
    @patch("app.api.router.task_manager")
    def test_generate_voice_production_mode(self, mock_task_manager, mock_background_tasks):
        """Test generating voice in production mode."""
        # Set up mock
        mock_task_id = "test-task-id"
        mock_task_manager.register_task.return_value = mock_task_id
        
        # Create request
        request = VoiceGenerationRequest(
            text="Hello world",
            speaker_id=1,
            temperature=0.7,
            top_k=50,
            style="default"
        )
        
        # Temporarily unset test mode
        if "ECHOFORGE_TEST" in os.environ:
            test_mode = os.environ["ECHOFORGE_TEST"]
            del os.environ["ECHOFORGE_TEST"]
        else:
            test_mode = None
        
        try:
            # Call the endpoint function directly using asyncio
            response = asyncio.run(generate_voice(mock_background_tasks, request))
            
            # Verify response
            self.assertEqual(response["task_id"], mock_task_id)
            self.assertEqual(response["status"], "processing")
            
            # Verify task was registered
            mock_task_manager.register_task.assert_called_once_with("voice_generation")
            
            # Verify background task was added
            mock_background_tasks.add_task.assert_called_once()
            args, kwargs = mock_background_tasks.add_task.call_args
            self.assertEqual(kwargs["task_id"], mock_task_id)
            self.assertEqual(kwargs["text"], "Hello world")
            self.assertEqual(kwargs["speaker_id"], 1)
            self.assertEqual(kwargs["temperature"], 0.7)
            self.assertEqual(kwargs["top_k"], 50)
            self.assertEqual(kwargs["style"], "default")
        finally:
            # Restore test mode
            if test_mode is not None:
                os.environ["ECHOFORGE_TEST"] = test_mode

    @patch("app.api.router.BackgroundTasks")
    def test_generate_voice_empty_text(self, mock_background_tasks):
        """Test generating voice with empty text."""
        # Create request with empty text
        request = VoiceGenerationRequest(
            text="   ",  # Only whitespace
            speaker_id=1,
            temperature=0.7,
            top_k=50,
            style="default"
        )
        
        # Call the endpoint function and expect an exception
        with self.assertRaises(Exception):
            asyncio.run(generate_voice(mock_background_tasks, request))

    def test_get_task_status_test_mode(self):
        """Test getting task status in test mode."""
        # Call the endpoint function directly using asyncio
        response = asyncio.run(get_task_status("test-task-id"))
        
        # Verify response
        self.assertEqual(response["task_id"], "test-task-id")
        self.assertEqual(response["status"], "completed")
        self.assertIn("result", response)
        self.assertEqual(response["result"]["speaker_id"], 1)
        self.assertIn("file_url", response["result"])
        self.assertIn("file_path", response["result"])

    @patch("app.api.router.task_manager")
    def test_get_task_status_production_mode(self, mock_task_manager):
        """Test getting task status in production mode."""
        # Set up mock
        mock_task = {
            "task_id": "test-task-id",
            "status": "completed",
            "result": {
                "text": "Hello world",
                "speaker_id": 2,
                "file_url": "/voices/test.wav",
                "file_path": "/tmp/test.wav"
            }
        }
        mock_task_manager.get_task.return_value = mock_task
        
        # Temporarily unset test mode
        if "ECHOFORGE_TEST" in os.environ:
            test_mode = os.environ["ECHOFORGE_TEST"]
            del os.environ["ECHOFORGE_TEST"]
        else:
            test_mode = None
        
        try:
            # Call the endpoint function directly using asyncio
            response = asyncio.run(get_task_status("test-task-id"))
            
            # Verify response
            self.assertEqual(response, mock_task)
            
            # Verify task was retrieved
            mock_task_manager.get_task.assert_called_once_with("test-task-id")
        finally:
            # Restore test mode
            if test_mode is not None:
                os.environ["ECHOFORGE_TEST"] = test_mode

    @patch("app.api.router.task_manager")
    def test_get_task_status_not_found(self, mock_task_manager):
        """Test getting task status for a non-existent task."""
        # Set up mock
        mock_task_manager.get_task.return_value = None
        
        # Temporarily unset test mode
        if "ECHOFORGE_TEST" in os.environ:
            test_mode = os.environ["ECHOFORGE_TEST"]
            del os.environ["ECHOFORGE_TEST"]
        else:
            test_mode = None
        
        try:
            # Call the endpoint function and expect an exception
            with self.assertRaises(Exception):
                asyncio.run(get_task_status("non-existent-task"))
        finally:
            # Restore test mode
            if test_mode is not None:
                os.environ["ECHOFORGE_TEST"] = test_mode


if __name__ == "__main__":
    unittest.main() 