"""
Environment loader for EchoForge.

This module loads environment variables from .env files.
"""

import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def load_env_file(file_path):
    """
    Load environment variables from a file.
    
    Args:
        file_path: Path to the .env file
    """
    if not os.path.exists(file_path):
        logger.debug(f"Environment file not found: {file_path}")
        return
    
    logger.info(f"Loading environment from: {file_path}")
    
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
                
            # Parse key-value pairs
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if value and value[0] == value[-1] and value[0] in ('"', "'"):
                    value = value[1:-1]
                
                # Set environment variable
                os.environ[key] = value
                logger.debug(f"Set environment variable: {key}")

def load_env_files():
    """
    Load environment variables from .env files.
    
    Loads variables in the following order (later files override earlier ones):
    1. .env (base environment)
    2. .env.local (local environment)
    """
    # Get project root directory
    root_dir = Path(__file__).parent.parent.parent
    
    # Load base environment
    base_env = root_dir / '.env'
    load_env_file(base_env)
    
    # Load local environment (overrides base)
    local_env = root_dir / '.env.local'
    load_env_file(local_env)

# Load environment variables when the module is imported
load_env_files() 