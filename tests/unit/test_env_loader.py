"""
Unit tests for the environment loader.
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from app.core.env_loader import load_env_file, load_env_files


class EnvLoaderTest(unittest.TestCase):
    """Test the environment loader functionality."""

    def test_load_env_file(self):
        """Test loading environment variables from a file."""
        # Create a temporary .env file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
            temp.write("TEST_VAR=test_value\n")
            temp.write("# This is a comment\n")
            temp.write("EMPTY_VAR=\n")
            temp.write("QUOTED_VAR=\"quoted value\"\n")
            temp_path = temp.name

        try:
            # Clear environment and load the file
            with patch.dict(os.environ, {}, clear=True):
                load_env_file(temp_path)
                
                # Check that variables were loaded correctly
                self.assertEqual(os.environ.get("TEST_VAR"), "test_value")
                self.assertEqual(os.environ.get("EMPTY_VAR"), "")
                self.assertEqual(os.environ.get("QUOTED_VAR"), "quoted value")
                
                # Check that comments were ignored
                self.assertNotIn("# This is a comment", os.environ)
        finally:
            # Clean up the temporary file
            os.unlink(temp_path)

    def test_load_env_files(self):
        """Test loading environment variables from multiple files with overrides."""
        # Create a temporary base .env file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as base_temp:
            base_temp.write("BASE_VAR=base_value\n")
            base_temp.write("OVERRIDE_VAR=original_value\n")
            base_path = base_temp.name

        # Create a temporary .env.local file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as local_temp:
            local_temp.write("LOCAL_VAR=local_value\n")
            local_temp.write("OVERRIDE_VAR=overridden_value\n")
            local_path = local_temp.name

        try:
            # Clear environment and load both files
            with patch.dict(os.environ, {}, clear=True):
                # Mock the file paths
                with patch('pathlib.Path.joinpath') as mock_joinpath:
                    # Configure the mock to return our temp files
                    mock_joinpath.side_effect = lambda path: MagicMock(
                        __str__=lambda self: base_path if path == '.env' else local_path
                    )
                    
                    # Call the function with our mocked paths
                    load_env_files()
                    
                    # Check that variables were loaded correctly
                    self.assertEqual(os.environ.get("BASE_VAR"), "base_value")
                    self.assertEqual(os.environ.get("LOCAL_VAR"), "local_value")
                    
                    # Check that local overrides base
                    self.assertEqual(os.environ.get("OVERRIDE_VAR"), "overridden_value")
        finally:
            # Clean up the temporary files
            os.unlink(base_path)
            os.unlink(local_path)

    def test_missing_env_file(self):
        """Test that missing .env files are handled gracefully."""
        with patch.dict(os.environ, {}, clear=True):
            # Use a non-existent file path
            non_existent_path = "/path/that/does/not/exist/.env"
            
            # This should not raise an exception
            load_env_file(non_existent_path)
            
            # Environment should remain unchanged
            self.assertEqual(len(os.environ), 0)


if __name__ == "__main__":
    unittest.main() 