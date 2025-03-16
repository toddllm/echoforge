#!/usr/bin/env python3
"""
Admin Voice Generation Test Script

This script tests the voice generation functionality that will be used in the admin interface.
It directly uses the same components that the admin endpoints would use.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_admin_voice")

def test_voice_generation(text, speaker_id=1, temperature=0.7, top_k=50, output_path=None):
    """Test voice generation using the API voice generator."""
    try:
        from app.api.voice_generator import voice_generator
        from app.core.task_manager import TaskManager
        from app.core import config
        
        if voice_generator is None:
            logger.error("Voice generator not initialized")
            return False
            
        # Create output directory if needed
        if output_path:
            output_file = Path(output_path)
            os.makedirs(output_file.parent, exist_ok=True)
        else:
            # Use the same output directory as the voice generator
            output_dir = Path(config.OUTPUT_DIR)
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"admin_test_{speaker_id}_{timestamp}.wav"
        
        logger.info(f"Will save output to: {output_file}")
        
        # Initialize task manager for testing
        task_manager = TaskManager()
        task_id = task_manager.register_task("voice_generation")
        logger.info(f"Registered task with ID: {task_id}")
        
        # Update task status
        task_manager.update_task(task_id, status="processing")
        
        # Generate the voice
        logger.info(f"Generating voice for text: '{text}'")
        try:
            file_path, file_url = voice_generator.generate(
                text=text,
                speaker_id=speaker_id,
                temperature=temperature,
                top_k=top_k,
                style="natural"
            )
            
            if file_path:
                # Voice generation successful
                logger.info(f"Voice generated at: {file_path}")
                
                # If the generated file is different from our target file, copy it
                if str(file_path) != str(output_file):
                    import shutil
                    shutil.copy2(file_path, output_file)
                    logger.info(f"Copied audio file to: {output_file}")
                
                # Update task with success
                task_manager.update_task(
                    task_id, 
                    status="completed",
                    result={
                        "file_path": str(output_file),
                        "file_url": file_url or f"/voices/{output_file.name}"
                    }
                )
                return True
            else:
                logger.error("Voice generation failed - no file path returned")
                task_manager.update_task(
                    task_id, 
                    status="failed",
                    error="Voice generation failed - no file path returned"
                )
        except Exception as e:
            logger.exception(f"Error during voice generation: {e}")
            task_manager.update_task(
                task_id, 
                status="failed",
                error=str(e)
            )
            return False
    
    except ImportError as e:
        logger.error(f"Error importing required modules: {e}")
        return False
    
    return False

def main():
    """Main function for the test script."""
    parser = argparse.ArgumentParser(description="Test admin voice generation")
    parser.add_argument("--text", default="Hello, this is a test of the admin voice generation system.", 
                        help="Text to convert to speech")
    parser.add_argument("--output", default=None, help="Output file path (default: auto-generated)")
    parser.add_argument("--speaker-id", type=int, default=1, help="Speaker ID to use (default: 1)")
    parser.add_argument("--temperature", type=float, default=0.7, 
                        help="Temperature for sampling (default: 0.7)")
    parser.add_argument("--top-k", type=int, default=50, 
                        help="Top-k tokens to consider (default: 50)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    
    # Run the test
    success = test_voice_generation(
        text=args.text,
        speaker_id=args.speaker_id,
        temperature=args.temperature,
        top_k=args.top_k,
        output_path=args.output
    )
    
    if success:
        logger.info("Voice generation test completed successfully")
        return 0
    else:
        logger.error("Voice generation test failed")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 