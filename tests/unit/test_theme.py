"""
Unit tests for the theme functionality.
"""

import os
import unittest
from unittest.mock import patch

from app.core import config


class ThemeConfigTest(unittest.TestCase):
    """Test the theme configuration functionality."""

    def test_default_theme(self):
        """Test that the default theme is 'light'."""
        # Reset the environment variable to ensure we get the default
        with patch.dict(os.environ, {}, clear=True):
            # Reload the config module to get fresh values
            import importlib
            importlib.reload(config)
            self.assertEqual(config.DEFAULT_THEME, "light")

    def test_custom_theme(self):
        """Test that the theme can be customized via environment variables."""
        # Set the environment variable to 'dark'
        with patch.dict(os.environ, {"DEFAULT_THEME": "dark"}, clear=True):
            # Reload the config module to get fresh values
            import importlib
            importlib.reload(config)
            self.assertEqual(config.DEFAULT_THEME, "dark")

    def test_invalid_theme(self):
        """Test that invalid themes are accepted but should be handled by the UI."""
        # Set the environment variable to an invalid value
        with patch.dict(os.environ, {"DEFAULT_THEME": "invalid_theme"}, clear=True):
            # Reload the config module to get fresh values
            import importlib
            importlib.reload(config)
            # The config should accept any string value, UI will handle validation
            self.assertEqual(config.DEFAULT_THEME, "invalid_theme")


if __name__ == "__main__":
    unittest.main() 