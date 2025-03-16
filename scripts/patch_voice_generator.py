#!/usr/bin/env python3
"""
Script to patch the run_voice_generator.sh in the voice_poc directory
to add support for direct text generation without scenes.
"""

import os
import sys
import subprocess
import logging
import shutil
import tempfile
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("patch_script")

VOICE_POC_PATH = "/home/tdeshane/movie_maker/voice_poc"
VOICE_GENERATOR_SCRIPT = os.path.join(VOICE_POC_PATH, "run_voice_generator.sh")

def patch_script():
    """Patch the run_voice_generator.sh script to support direct text input."""
    # Check if the script exists
    if not os.path.exists(VOICE_GENERATOR_SCRIPT):
        logger.error(f"Voice generator script not found at: {VOICE_GENERATOR_SCRIPT}")
        return False
    
    # Backup the original script
    backup_path = f"{VOICE_GENERATOR_SCRIPT}.bak"
    if not os.path.exists(backup_path):
        logger.info(f"Creating backup of script at: {backup_path}")
        shutil.copy2(VOICE_GENERATOR_SCRIPT, backup_path)
    
    # Read the original script
    with open(VOICE_GENERATOR_SCRIPT, "r") as f:
        script_content = f.read()
    
    # Check if already patched
    if "--text" in script_content and "--direct" in script_content:
        logger.info("Script already patched, skipping")
        return True
    
    # Create a patched version of the script
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
        # Add the direct text option to the script
        script_lines = script_content.splitlines()
        modified_lines = []
        
        # Add new variables for direct text input
        help_added = False
        direct_added = False
        text_added = False
        options_modified = False
        generator_modified = False
        
        for line in script_lines:
            # Add the direct flag
            if "DEVICE=" in line and not direct_added:
                modified_lines.append(line)
                modified_lines.append("# Direct text input instead of scenes")
                modified_lines.append("DIRECT=false")
                modified_lines.append("TEXT=\"\"")
                direct_added = True
                continue
            
            # Add help info
            if "--help" in line and "Show this help message" in line and not help_added:
                modified_lines.append(line)
                modified_lines.append("  --text TEXT        Direct text to synthesize (requires --direct)")
                modified_lines.append("  --direct           Use direct text input instead of scene IDs")
                help_added = True
                continue
            
            # Add option parsing
            if "case $key in" in line and not options_modified:
                modified_lines.append(line)
                modified_lines.append("    --text)")
                modified_lines.append("        TEXT=\"$2\"")
                modified_lines.append("        shift # past argument")
                modified_lines.append("        shift # past value")
                modified_lines.append("        ;;")
                modified_lines.append("    --direct)")
                modified_lines.append("        DIRECT=true")
                modified_lines.append("        shift # past argument")
                modified_lines.append("        ;;")
                options_modified = True
                continue
            
            # Modify the generator call to support direct text input
            if "python -m csm.generator" in line and not generator_modified:
                # Save the original line
                original_generator_line = line
                
                # Add the direct mode logic
                modified_lines.append("# Direct text mode implementation")
                modified_lines.append("if [[ \"$DIRECT\" == true ]]; then")
                modified_lines.append("  echo \"Running in direct text mode with: '$TEXT'\"")
                modified_lines.append("  # Create a temporary prompts file with the direct text")
                modified_lines.append("  TEMP_FILE=$(mktemp)")
                modified_lines.append("  echo \"{\\\"1\\\": \\\"$TEXT\\\"}\" > \"$TEMP_FILE\"")
                modified_lines.append("  # Run the generator with scene 1")
                modified_lines.append("  python -m csm.generator --device $DEVICE --output \"$OUTPUT\" --prompts \"$TEMP_FILE\" --scene 1")
                modified_lines.append("  RESULT=$?")
                modified_lines.append("  # Clean up temp file")
                modified_lines.append("  rm -f \"$TEMP_FILE\"")
                modified_lines.append("  exit $RESULT")
                modified_lines.append("else")
                modified_lines.append("  # Original scene-based mode")
                modified_lines.append("  " + original_generator_line)
                modified_lines.append("fi")
                generator_modified = True
                continue
            
            modified_lines.append(line)
        
        # Write the modified script
        tmp.write("\n".join(modified_lines))
        tmp_path = tmp.name
    
    # Replace the original script with our patched version
    try:
        shutil.move(tmp_path, VOICE_GENERATOR_SCRIPT)
        os.chmod(VOICE_GENERATOR_SCRIPT, 0o755)  # Make it executable
        logger.info(f"Successfully patched {VOICE_GENERATOR_SCRIPT}")
        return True
    except Exception as e:
        logger.error(f"Error replacing script: {e}")
        return False

if __name__ == "__main__":
    try:
        if patch_script():
            print("Voice generator script successfully patched to support direct text input.")
        else:
            print("Failed to patch voice generator script.")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 