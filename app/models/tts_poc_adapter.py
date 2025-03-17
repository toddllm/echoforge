"""
TTS POC Adapter

This module provides an adapter to interface with the existing TTS POC implementation.
"""

import os
import sys
import logging
import subprocess
import tempfile
import json
import time
import shutil
import torch
import glob
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

from app.core import config

# Configure logging
logger = logging.getLogger("echoforge.tts_poc_adapter")

# Default paths for the original TTS_POC project
TTS_POC_PATH = "/home/tdeshane/tts_poc"
MOVIE_MAKER_PATH = "/home/tdeshane/movie_maker"
VOICE_POC_PATH = os.path.join(MOVIE_MAKER_PATH, "voice_poc")
VOICE_GENERATOR_SCRIPT = os.path.join(VOICE_POC_PATH, "run_voice_generator.sh")

# Standardized directory structure
ECHOFORGE_ROOT = "/tmp/echoforge"
VOICES_DIR = os.path.join(ECHOFORGE_ROOT, "voices")
GENERATED_DIR = os.path.join(VOICES_DIR, "generated")
TEMP_DIR = os.path.join(VOICES_DIR, "temp")
CACHE_DIR = os.path.join(VOICES_DIR, "cache")
LOGS_DIR = os.path.join(VOICES_DIR, "logs")

class TTSPOCAdapter:
    """
    Adapter for the TTS POC implementation.
    This provides access to the more sophisticated voice generation capabilities in the existing codebase.
    """
    
    def __init__(self, output_dir: str = "/tmp/echoforge/voices"):
        """
        Initialize the TTS POC adapter.
        
        Args:
            output_dir: Directory to store generated voice files
        """
        self.output_dir = output_dir
        self.available = False
        
        # Create EchoForge-specific paths
        self.echoforge_output_dir = os.path.join(output_dir, "generated")
        self.temp_output_dir = os.path.join(output_dir, "temp")
        self.cache_dir = os.path.join(output_dir, "cache")
        self.logs_dir = os.path.join(output_dir, "logs")
        
        # Ensure all output directories exist
        for directory in [self.output_dir, self.echoforge_output_dir, self.temp_output_dir, 
                          self.cache_dir, self.logs_dir]:
            try:
                os.makedirs(directory, exist_ok=True)
                if not os.path.exists(directory):
                    logger.error(f"Failed to create directory {directory}")
                elif not os.access(directory, os.W_OK):
                    logger.error(f"Directory {directory} is not writable")
                else:
                    logger.info(f"Directory verified: {directory}")
            except Exception as e:
                logger.error(f"Error creating directory {directory}: {e}")
        
        # Create symlinks for compatibility with other systems
        try:
            # Create symlink from TTS POC expected output to our temp directory
            tts_poc_output = os.path.join(VOICE_POC_PATH, "output")
            if not os.path.exists(tts_poc_output):
                os.makedirs(os.path.dirname(tts_poc_output), exist_ok=True)
                os.symlink(self.temp_output_dir, tts_poc_output)
                logger.info(f"Created symlink from {tts_poc_output} to {self.temp_output_dir}")
        except Exception as e:
            logger.warning(f"Could not create symlink: {e}")
        
        # Try to validate the adapter setup
        if os.path.exists(TTS_POC_PATH):
            logger.info(f"TTS POC path found: {TTS_POC_PATH}")
            
            # Also check for movie_maker if we're using the CSM adapter
            if os.path.exists(VOICE_GENERATOR_SCRIPT):
                logger.info(f"Voice generator script found: {VOICE_GENERATOR_SCRIPT}")
                self.available = True
            else:
                logger.warning(f"Voice generator script not found: {VOICE_GENERATOR_SCRIPT}")
                # Try to use the direct TTS POC web_api.py
                if os.path.exists(os.path.join(TTS_POC_PATH, "web_api.py")):
                    logger.info("Found TTS POC web_api.py, will use direct generation method")
                    self.available = True
        else:
            logger.warning(f"TTS POC path not found: {TTS_POC_PATH}")
        
        if self.available:
            logger.info("TTS POC adapter initialized and available")
        else:
            logger.warning("TTS POC adapter initialized but not available")
    
    def generate_speech(self, text: str, speaker_id: int = 1, temperature: float = 0.7, 
                        top_k: int = 50, device: str = "auto") -> Tuple[Optional[torch.Tensor], int]:
        """
        Generate speech using the TTS POC implementation.
        
        Args:
            text: Text to convert to speech
            speaker_id: ID of the speaker to use
            temperature: Temperature for generation
            top_k: Top-k value for generation
            device: Device to use (auto, cpu, cuda)
            
        Returns:
            Tuple containing the audio tensor and sample rate, or (None, 0) if failed
        """
        if not self.available:
            logger.error("TTS POC adapter not available")
            return None, 0
        
        # Validate device parameter - convert 'auto' to 'cuda' if available
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Auto device selection chose: {device}")
        
        # Choose the appropriate generation method
        if os.path.exists(VOICE_GENERATOR_SCRIPT):
            return self._generate_with_voice_script(text, speaker_id, temperature, top_k, device)
        elif os.path.exists(os.path.join(TTS_POC_PATH, "web_api.py")):
            return self._generate_with_web_api(text, speaker_id, temperature, top_k, device)
        else:
            logger.error("No valid generation method available")
            return None, 0
    
    def _generate_with_voice_script(self, text: str, speaker_id: int, temperature: float, 
                                  top_k: int, device: str) -> Tuple[Optional[torch.Tensor], int]:
        """
        Generate speech using the voice_poc script from movie_maker.
        This is a simplified version that uses a single prompt directly.
        
        Args:
            text: Text to convert to speech
            speaker_id: ID of the speaker to use
            temperature: Temperature for generation
            top_k: Top-k value for generation
            device: Device to use (auto, cpu, cuda)
            
        Returns:
            Tuple containing the audio tensor and sample rate, or (None, 0) if failed
        """
        logger.info(f"Generating speech for text: '{text}' using device: {device}")
        
        # Validate device parameter
        if device not in ["cuda", "cpu"]:
            logger.warning(f"Invalid device '{device}', falling back to CPU")
            device = "cpu"
        
        # Check CUDA availability if requested
        if device == "cuda" and not torch.cuda.is_available():
            logger.warning("CUDA requested but not available, falling back to CPU")
            device = "cpu"
        
        # Create a unique identifier for this request
        timestamp = int(time.time())
        import random
        unique_id = f"{timestamp}_{random.randint(10000, 99999)}"
        expected_output = os.path.join(self.temp_output_dir, f"echoforge_voice_{unique_id}.wav")
        
        # Ensure the temp directory exists and is writable
        if not os.path.exists(self.temp_output_dir):
            try:
                os.makedirs(self.temp_output_dir, exist_ok=True)
                logger.info(f"Created temp directory: {self.temp_output_dir}")
            except Exception as e:
                logger.error(f"Failed to create temp directory: {e}")
                return None, 0
        
        # Use tempfile to create a temporary direct script that we control
        temp_script = None
        try:
            # Create a temporary Python script file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                script_content = f'''
import os
import sys
import torch
import logging
import json
import tempfile
import subprocess
import glob
import shutil
import time
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("echoforge_direct_tts")

# Define paths
VOICE_GENERATOR = "{VOICE_GENERATOR_SCRIPT}"
OUTPUT_DIR = "{self.temp_output_dir}"
OUTPUT_FILE = "{expected_output}"

# Check CUDA availability if requested
if "{device}" == "cuda":
    if not torch.cuda.is_available():
        logger.error("CUDA requested but not available")
        sys.exit(1)
    else:
        # Print CUDA device info
        device_name = torch.cuda.get_device_name(0)
        device_cap = torch.cuda.get_device_capability(0)
        logger.info(f"Using CUDA device: {{device_name}} with capability {{device_cap}}")
        
        # Check CUDA memory
        total_mem = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        free_mem = torch.cuda.memory_reserved(0) / (1024**3)
        logger.info(f"CUDA memory: {{total_mem:.2f}} GB total, {{free_mem:.2f}} GB reserved")

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)
if not os.path.exists(OUTPUT_DIR):
    logger.error(f"Failed to create output directory: {{OUTPUT_DIR}}")
    sys.exit(1)

# Create a simple JSON file with our text
temp_json = None
try:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({{"1": "{text}"}}, f)
        temp_json = f.name
    
    # Run the voice generator script with a single scene
    cmd = [
        VOICE_GENERATOR,
        "--device", "{device}",
        "--output", OUTPUT_DIR,
        "--prompts", temp_json,
        "--scene", "1"
    ]
    
    logger.info(f"Running command: {{' '.join(cmd)}}")
    
    # Execute the command
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for the process to complete
    stdout, stderr = process.communicate()
    
    if process.returncode != 0:
        logger.error(f"Command failed with code {{process.returncode}}")
        logger.error(f"STDOUT: {{stdout}}")
        logger.error(f"STDERR: {{stderr}}")
        
        # Check for CUDA out of memory error
        if "CUDA out of memory" in stderr:
            logger.error("CUDA out of memory error detected")
            print("CUDA_OOM_ERROR")
        
        sys.exit(1)
    
    # Look for the output file - scenes are usually named scene_1.wav
    scene_file = os.path.join(OUTPUT_DIR, "scene_1.wav")
    if os.path.exists(scene_file):
        # Copy to our expected output path
        shutil.copy2(scene_file, OUTPUT_FILE)
        logger.info(f"Copied scene file to: {{OUTPUT_FILE}}")
        print(f"OUTPUT_FILE: {{OUTPUT_FILE}}")
        sys.exit(0)
    else:
        # Check for other possible filenames
        possible_files = glob.glob(os.path.join(OUTPUT_DIR, "*.wav"))
        
        # If no files found in output dir, check the voice_poc directory
        if not possible_files:
            voice_poc_output = os.path.join("{VOICE_POC_PATH}", "output")
            possible_files = glob.glob(os.path.join(voice_poc_output, "*.wav"))
            logger.info(f"Checking voice_poc output directory: {{voice_poc_output}}")
        
        # If still no files, check the current directory
        if not possible_files:
            possible_files = glob.glob("*.wav")
            logger.info("Checking current directory for WAV files")
        
        # If we found any files, use the most recent one
        if possible_files:
            # Sort by modification time (newest first)
            possible_files.sort(key=os.path.getmtime, reverse=True)
            newest_file = possible_files[0]
            logger.info(f"Found newest WAV file: {{newest_file}}")
            
            # Copy to our expected output
            shutil.copy2(newest_file, OUTPUT_FILE)
            logger.info(f"Copied newest file to: {{OUTPUT_FILE}}")
            print(f"OUTPUT_FILE: {{OUTPUT_FILE}}")
            sys.exit(0)
        
        logger.error("Could not find generated file")
        
        # List all directories to help debug
        logger.error(f"Contents of OUTPUT_DIR: {{os.listdir(OUTPUT_DIR) if os.path.exists(OUTPUT_DIR) else 'directory not found'}}")
        voice_poc_output = os.path.join("{VOICE_POC_PATH}", "output")
        logger.error(f"Contents of voice_poc output: {{os.listdir(voice_poc_output) if os.path.exists(voice_poc_output) else 'directory not found'}}")
        logger.error(f"Contents of current dir: {{os.listdir('.')}}")
        
        sys.exit(1)
except Exception as e:
    logger.error(f"Unhandled exception: {{e}}")
    logger.error(traceback.format_exc())
    sys.exit(1)
finally:
    # Clean up
    if temp_json and os.path.exists(temp_json):
        os.unlink(temp_json)
'''
                f.write(script_content)
                temp_script = f.name
            
            # Set up command to run our helper script
            cmd = [sys.executable, temp_script]
            logger.info(f"Running voice generation with command: {' '.join(cmd)}")
            
            # Run the command
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for the process to complete
            stdout, stderr = process.communicate()
            
            # Check for CUDA OOM error
            if "CUDA_OOM_ERROR" in stdout:
                logger.warning("CUDA out of memory error detected, falling back to CPU")
                if device == "cuda":
                    logger.info("Retrying with CPU")
                    return self._generate_with_voice_script(text, speaker_id, temperature, top_k, "cpu")
            
            # Check the return code
            if process.returncode != 0:
                logger.error(f"Voice generation failed with return code: {process.returncode}")
                logger.error(f"STDOUT: {stdout}")
                logger.error(f"STDERR: {stderr}")
                
                # Fall back to CPU if we got CUDA out of memory error
                if device == "cuda" and ("CUDA out of memory" in stderr or "CUDA error" in stderr):
                    logger.warning("CUDA error detected, falling back to CPU")
                    return self._generate_with_voice_script(text, speaker_id, temperature, top_k, "cpu")
                
                return None, 0
            
            logger.info(f"Voice generation completed successfully")
            
            # Look for the OUTPUT_FILE marker in stdout
            output_path = None
            for line in stdout.splitlines():
                if "OUTPUT_FILE:" in line:
                    parts = line.split("OUTPUT_FILE:", 1)
                    if len(parts) == 2:
                        potential_path = parts[1].strip()
                        if os.path.exists(potential_path):
                            output_path = potential_path
                            logger.info(f"Found output file from marker: {output_path}")
                            break
            
            # If we couldn't find the marker, check if the expected output exists
            if not output_path and os.path.exists(expected_output):
                output_path = expected_output
                logger.info(f"Found expected output file: {output_path}")
            
            # If still not found, look for any WAV files created in the last 30 seconds
            if not output_path:
                current_time = time.time()
                newest_file = None
                newest_time = 0
                
                # Search in multiple directories
                search_dirs = [
                    self.temp_output_dir,
                    self.echoforge_output_dir,
                    VOICE_POC_PATH,
                    os.path.join(VOICE_POC_PATH, "output"),
                    os.getcwd()
                ]
                
                for directory in search_dirs:
                    if os.path.exists(directory):
                        logger.info(f"Searching for WAV files in: {directory}")
                        for filename in os.listdir(directory):
                            if filename.endswith('.wav'):
                                file_path = os.path.join(directory, filename)
                                file_mtime = os.path.getmtime(file_path)
                                time_diff = current_time - file_mtime
                                if time_diff < 60 and file_mtime > newest_time:  # Increased to 60 seconds
                                    newest_time = file_mtime
                                    newest_file = file_path
                
                if newest_file:
                    output_path = newest_file
                    logger.info(f"Using newest WAV file: {output_path}, modified {current_time - newest_time:.1f} seconds ago")
            
            if not output_path or not os.path.exists(output_path):
                logger.error("Output file not found after generation")
                
                # List contents of directories to help debug
                for directory in [self.temp_output_dir, self.echoforge_output_dir, 
                                 os.path.join(VOICE_POC_PATH, "output")]:
                    if os.path.exists(directory):
                        logger.error(f"Contents of {directory}: {os.listdir(directory)}")
                
                return None, 0
            
            # Load the audio file
            try:
                import torchaudio
                audio, sample_rate = torchaudio.load(output_path)
                
                # Save a copy to our output directory with a unique name
                final_output = os.path.join(self.echoforge_output_dir, f"voice_{unique_id}.wav")
                torchaudio.save(final_output, audio, sample_rate)
                logger.info(f"Saved final output to: {final_output}")
                
                # Create a symlink in the cache directory
                cache_link = os.path.join(self.cache_dir, f"latest_{unique_id}.wav")
                try:
                    if os.path.exists(cache_link):
                        os.remove(cache_link)
                    os.symlink(final_output, cache_link)
                    logger.info(f"Created symlink at {cache_link}")
                except Exception as e:
                    logger.warning(f"Could not create symlink: {e}")
                
                return audio, sample_rate
            except Exception as e:
                logger.error(f"Error loading audio file: {e}")
                return None, 0
        
        except Exception as e:
            logger.error(f"Error in voice generation: {e}")
            return None, 0
        
        finally:
            # Clean up the temporary script
            if temp_script and os.path.exists(temp_script):
                try:
                    os.unlink(temp_script)
                except:
                    pass
    
    def _generate_with_web_api(self, text: str, speaker_id: int, temperature: float, 
                             top_k: int, device: str) -> Tuple[Optional[torch.Tensor], int]:
        """
        Generate speech using the TTS POC web_api.py method.
        
        Args:
            text: Text to convert to speech
            speaker_id: ID of the speaker to use
            temperature: Temperature for generation
            top_k: Top-k value for generation
            device: Device to use (auto, cpu, cuda)
            
        Returns:
            Tuple containing the audio tensor and sample rate, or (None, 0) if failed
        """
        logger.info(f"Generating speech with tts_poc web_api: '{text}'")
        
        # This approach would involve either:
        # 1. Making an HTTP request to a running TTS POC server
        # 2. Importing and using the TTS POC modules directly
        # 3. Running the TTS POC generation script
        
        # For now, let's implement option 3 as it's most reliable
        timestamp = int(time.time())
        unique_id = os.urandom(4).hex()  # 8 character random hex
        output_filename = f"voice_{timestamp}_{unique_id}.wav"
        final_output = os.path.join(self.echoforge_output_dir, output_filename)
        
        try:
            # Create a temporary JSON file with the generation parameters
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp:
                params = {
                    "text": text,
                    "speaker_id": speaker_id,
                    "temperature": temperature,
                    "top_k": top_k,
                    "device": device,
                    "output_path": final_output
                }
                json.dump(params, temp)
                params_file = temp.name
            
            # Run the script to generate the audio
            cmd = [
                sys.executable,
                os.path.join(TTS_POC_PATH, "test_generation.py"),
                "--params", params_file
            ]
            
            logger.info(f"Running TTS POC generation with command: {' '.join(cmd)}")
            
            # Run the command
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=TTS_POC_PATH
            )
            
            # Wait for the process to complete
            stdout, stderr = process.communicate()
            
            # Check the return code
            if process.returncode != 0:
                logger.error(f"TTS POC generation failed with return code: {process.returncode}")
                logger.error(f"STDOUT: {stdout}")
                logger.error(f"STDERR: {stderr}")
                
                # Check for typical errors
                if "CUDA out of memory" in stderr:
                    logger.warning("CUDA out of memory error detected")
                    if device == "cuda":
                        logger.info("CUDA failed, falling back to CPU")
                        # Recursive call with CPU device
                        return self._generate_with_web_api(text, speaker_id, temperature, top_k, "cpu")
                
                return None, 0
            
            logger.info(f"TTS POC generation command succeeded")
            
            # Wait a moment to ensure file system operations complete
            time.sleep(1)
            
            # Check if the output file exists
            if not os.path.exists(final_output):
                # Look for alternative paths mentioned in stdout
                for line in stdout.splitlines():
                    if "Generated file:" in line or "Output saved to:" in line:
                        parts = line.split(":", 1)
                        if len(parts) == 2:
                            possible_path = parts[1].strip()
                            if os.path.exists(possible_path) and possible_path.endswith('.wav'):
                                # Copy the file to our output location
                                shutil.copy2(possible_path, final_output)
                                logger.info(f"Copied output from {possible_path} to {final_output}")
                                break
            
            if not os.path.exists(final_output):
                logger.error(f"Output file not found: {final_output}")
                return None, 0
            
            # Load the audio file
            try:
                import torchaudio
                audio, sample_rate = torchaudio.load(final_output)
                logger.info(f"Loaded audio from {final_output}: {audio.shape}, {sample_rate}Hz")
                
                # Return the audio tensor and sample rate
                return audio.squeeze(), sample_rate
                
            except Exception as e:
                logger.error(f"Error loading audio file: {e}")
                return None, 0
            
        except Exception as e:
            logger.exception(f"Error generating speech: {e}")
            return None, 0
        
        finally:
            # Clean up temporary params file
            if 'params_file' in locals() and os.path.exists(params_file):
                try:
                    os.unlink(params_file)
                except Exception as e:
                    logger.warning(f"Error removing temporary params file: {e}")
    
    def get_voice_file_url(self, file_path: str) -> str:
        """
        Get a URL for accessing the voice file.
        
        Args:
            file_path: Path to the voice file
            
        Returns:
            URL for accessing the voice file
        """
        # Extract just the filename from the path
        filename = os.path.basename(file_path)
        
        # Return the relative URL
        return f"/api/admin/voices/{filename}" 