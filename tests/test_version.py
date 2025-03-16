"""
Test the version information in the app package.
"""

import app


def test_version():
    """Test that the version is a string."""
    assert isinstance(app.__version__, str)
    assert app.__version__ == "0.1.0" 