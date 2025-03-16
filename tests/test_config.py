"""
Test the configuration module.
"""

import os
from unittest.mock import patch

from app.core import config


def test_default_theme():
    """Test that the default theme is 'light'."""
    with patch.dict(os.environ, {}, clear=True):
        assert config.DEFAULT_THEME == "light"


def test_custom_theme():
    """Test that the theme can be customized via environment variables."""
    with patch.dict(os.environ, {"DEFAULT_THEME": "dark"}, clear=True):
        # Reload the config module to get fresh values
        import importlib
        importlib.reload(config)
        assert config.DEFAULT_THEME == "dark" 