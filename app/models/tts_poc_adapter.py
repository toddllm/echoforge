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
        
        # Ensure output directories exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.echoforge_output_dir, exist_ok=True)
        os.makedirs(self.temp_output_dir, exist_ok=True)
        
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
        
        Args:
            text: Text to convert to speech
            speaker_id: ID of the speaker to use
            temperature: Temperature for generation
            top_k: Top-k value for generation
            device: Device to use (auto, cpu, cuda)
            
        Returns:
            Tuple containing the audio tensor and sample rate, or (None, 0) if failed
        """
        logger.info(f"Generating speech with voice_poc script: '{text}'")
        
        # Create a unique identifier for this request
        timestamp = int(time.time())
        import random
        unique_id = f"{timestamp}_{random.randint(10000, 99999)}"
        output_filename = f"echoforge_voice_{unique_id}.wav"
        
        # Create our expected output path
        expected_output_path = os.path.join(self.temp_output_dir, output_filename)
        logger.info(f"Expected output will be at: {expected_output_path}")
        
        # Create a custom Python script for direct generation (no scenes)
        temp_script = None
        prompts_file = None
        try:
            # Create a temporary file for the direct generation script
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as script_file:
                script_content = f"""
# Temporary direct voice generation script for EchoForge
import os
import sys
import torch
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("direct_voice_generator")

# Add the voice_poc path to sys.path
voice_poc_path = "{VOICE_POC_PATH}"
sys.path.insert(0, voice_poc_path)

# First try to import from voice_poc
try:
    from csm.generator import Generator
    logger.info("Successfully imported CSM modules from voice_poc")
    
    # Initialize the generator
    generator = Generator(device="{device}")
    
    # Generate the audio for our single text prompt
    logger.info("Generating speech for text: '{text}'")
    
    # Generate and save audio to our specific output path
    audio = generator.generate_audio_for_text(
        "{text}", 
        temperature={temperature}, 
        top_k={top_k}
    )
    
    # Ensure the output directory exists
    os.makedirs(os.path.dirname("{expected_output_path}"), exist_ok=True)
    
    # Save to our expected output path
    generator.save_audio(audio, "{expected_output_path}")
    logger.info(f"Saved audio to {expected_output_path}")
    
    # Also save to a backup location in case the original one isn't found
    backup_path = os.path.join(os.getcwd(), "{output_filename}")
    generator.save_audio(audio, backup_path)
    logger.info(f"Saved backup to {backup_path}")
    
    print(f"ECHOFORGE_OUTPUT_PATH: {expected_output_path}")
    sys.exit(0)
except Exception as e:
    logger.error(f"Error generating with CSM Generator: {{e}}")
    print(f"ERROR: {{e}}")
    sys.exit(1)
"""
                script_file.write(script_content)
                temp_script = script_file.name
            
            logger.debug(f"Created direct generation script: {temp_script}")
            
            # Determine device to use
            if device == "auto":
                # Check if CUDA is available
                if torch.cuda.is_available():
                    try:
                        # Check available GPU memory
                        device_id = torch.cuda.current_device()
                        free_memory = torch.cuda.get_device_properties(device_id).total_memory - torch.cuda.memory_allocated(device_id)
                        free_memory_mb = free_memory / (1024 * 1024)
                        
                        if free_memory_mb > 2000:  # Need at least 2GB
                            device = "cuda"
                            logger.info(f"Auto-selecting CUDA device with {free_memory_mb:.2f} MB free")
                        else:
                            device = "cpu"
                            logger.info(f"Auto-selecting CPU due to limited GPU memory ({free_memory_mb:.2f} MB free)")
                    except Exception as e:
                        logger.warning(f"Error checking GPU memory: {e}, falling back to CPU")
                        device = "cpu"
                else:
                    device = "cpu"
                    logger.info("Auto-selecting CPU as CUDA is not available")
            
            # Build the command to run our direct script
            cmd = [
                sys.executable,  # Use the same Python interpreter
                temp_script
            ]
            
            logger.info(f"Running direct voice generation with device: {device}, command: {' '.join(cmd)}")
            
            # Run the command
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=VOICE_POC_PATH
            )
            
            # Wait for the process to complete
            stdout, stderr = process.communicate()
            
            # Check the return code
            if process.returncode != 0:
                logger.error(f"Direct voice generation failed with return code: {process.returncode}")
                logger.error(f"STDOUT: {stdout}")
                logger.error(f"STDERR: {stderr}")
                
                # Check for typical errors
                if "CUDA out of memory" in stderr:
                    logger.warning("CUDA out of memory error detected")
                    if device == "cuda":
                        logger.info("CUDA failed, falling back to CPU")
                        # Recursive call with CPU device
                        return self._generate_with_voice_script(text, speaker_id, temperature, top_k, "cpu")
                
                # If the direct approach fails, fall back to the original script
                logger.warning("Direct generation failed, falling back to original voice generator script")
                return self._generate_with_original_script(text, speaker_id, temperature, top_k, device)
            
            logger.info(f"Direct voice generation command succeeded")
            
            # Log the complete output for debugging
            logger.info(f"STDOUT: {stdout}")
            if stderr:
                logger.info(f"STDERR: {stderr}")
            
            # Wait a moment to ensure file system operations complete
            time.sleep(2)
            
            # Look for the output file marker in stdout
            output_path = None
            for line in stdout.splitlines():
                if "ECHOFORGE_OUTPUT_PATH:" in line:
                    parts = line.split("ECHOFORGE_OUTPUT_PATH:", 1)
                    if len(parts) == 2:
                        potential_path = parts[1].strip()
                        if os.path.exists(potential_path):
                            output_path = potential_path
                            logger.info(f"Found output path from marker: {output_path}")
                            break
            
            # If not found with marker, look for expected output path
            if not output_path and os.path.exists(expected_output_path):
                output_path = expected_output_path
                logger.info(f"Found output at expected path: {output_path}")
            
            # Search for recently modified files
            if not output_path:
                # Check for the output filename in temp directory or current directory
                for check_dir in [self.temp_output_dir, VOICE_POC_PATH, os.getcwd()]:
                    potential_path = os.path.join(check_dir, output_filename)
                    if os.path.exists(potential_path):
                        output_path = potential_path
                        logger.info(f"Found output file in directory {check_dir}: {output_path}")
                        break
                
                # If still not found, look for any recent WAV file
                if not output_path:
                    current_time = time.time()
                    newest_file = None
                    newest_time = 0
                    
                    for directory in [self.temp_output_dir, VOICE_POC_PATH, os.getcwd()]:
                        if os.path.exists(directory):
                            logger.info(f"Checking directory for recent WAV files: {directory}")
                            for filename in os.listdir(directory):
                                if filename.endswith('.wav'):
                                    file_path = os.path.join(directory, filename)
                                    file_mtime = os.path.getmtime(file_path)
                                    time_diff = current_time - file_mtime
                                    logger.info(f"Found WAV file: {file_path}, modified {time_diff:.1f} seconds ago")
                                    if time_diff < 30 and file_mtime > newest_time:  # Look for files modified in the last 30 seconds
                                        newest_time = file_mtime
                                        newest_file = file_path
                    
                    if newest_file:
                        output_path = newest_file
                        logger.info(f"Found newest wav file: {output_path}, modified {current_time - newest_time:.1f} seconds ago")
            
            # If output still not found, try desperate measures
            if not output_path:
                logger.warning(f"No output file found using standard methods. Trying filesystem search...")
                
                # Run the find command to locate recently modified wav files
                find_cmd = [
                    "find", 
                    "/tmp", VOICE_POC_PATH, os.getcwd(),
                    "-name", "*.wav",
                    "-mmin", "-1",  # Modified in the last 1 minute
                    "-type", "f"    # Regular files only
                ]
                
                try:
                    find_process = subprocess.Popen(
                        find_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    find_stdout, find_stderr = find_process.communicate()
                    
                    if find_process.returncode == 0 and find_stdout:
                        recent_wav_files = find_stdout.strip().split("\n")
                        if recent_wav_files:
                            most_recent = None
                            most_recent_time = 0
                            
                            for file_path in recent_wav_files:
                                if os.path.exists(file_path):
                                    logger.info(f"Found recent WAV file: {file_path}")
                                    file_mtime = os.path.getmtime(file_path)
                                    if file_mtime > most_recent_time:
                                        most_recent_time = file_mtime
                                        most_recent = file_path
                            
                            if most_recent:
                                output_path = most_recent
                                logger.info(f"Using most recently modified WAV file: {output_path}")
                    else:
                        logger.warning(f"Find command failed or found no files: {find_stderr}")
                
                except Exception as e:
                    logger.warning(f"Error running find command: {e}")
            
            if not output_path or not os.path.exists(output_path):
                logger.error(f"Output file not found after direct generation attempt")
                logger.error(f"STDOUT content for reference: {stdout}")
                
                # Fall back to the original script as a last resort
                logger.warning("Direct generation failed to produce a file, falling back to original voice generator script")
                return self._generate_with_original_script(text, speaker_id, temperature, top_k, device)
            
            logger.info(f"Found generated speech at: {output_path}")
            
            # Load the audio file
            try:
                import torchaudio
                audio, sample_rate = torchaudio.load(output_path)
                
                # Copy to our output directory with a unique name
                timestamp = int(time.time())
                final_output = os.path.join(self.echoforge_output_dir, f"voice_{timestamp}_{unique_id}.wav")
                
                # Save a copy to our output directory
                torchaudio.save(final_output, audio, sample_rate)
                logger.info(f"Saved copy to: {final_output}")
                
                # Return the audio tensor and sample rate
                return audio.squeeze(), sample_rate
                
            except Exception as e:
                logger.error(f"Error loading audio file {output_path}: {e}")
                return None, 0
            
        except Exception as e:
            logger.exception(f"Error in direct speech generation: {e}")
            return None, 0
        
        finally:
            # Clean up temporary files
            if temp_script and os.path.exists(temp_script):
                try:
                    os.unlink(temp_script)
                except Exception as e:
                    logger.warning(f"Error removing temporary script file: {e}")
            
            if prompts_file and os.path.exists(prompts_file):
                try:
                    os.unlink(prompts_file)
                except Exception as e:
                    logger.warning(f"Error removing temporary prompts file: {e}")
    
    def _generate_with_original_script(self, text: str, speaker_id: int, temperature: float, 
                                     top_k: int, device: str) -> Tuple[Optional[torch.Tensor], int]:
        """
        Fallback method that uses the original voice_poc script.
        This is kept as a fallback in case the direct method fails.
        
        Args:
            text: Text to convert to speech
            speaker_id: ID of the speaker to use
            temperature: Temperature for generation
            top_k: Top-k value for generation
            device: Device to use (auto, cpu, cuda)
            
        Returns:
            Tuple containing the audio tensor and sample rate, or (None, 0) if failed
        """
        logger.info(f"Falling back to original script for: '{text}'")
        
        # Create a unique identifier for this request
        timestamp = int(time.time())
        import random
        unique_id = f"{timestamp}_{random.randint(10000, 99999)}"
        
        # Create a temporary prompts file with a single prompt (no scene ID)
        prompts_file = None
        try:
            # Create a temporary file for the prompts with a direct prompt
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp:
                # Just write the text directly - no JSON or scene IDs
                temp.write(text)
                prompts_file = temp.name
            
            logger.debug(f"Created direct prompts file: {prompts_file}")
            
            # Build the command - simplified with no scene ID
            cmd = [
                VOICE_GENERATOR_SCRIPT,
                "--device", device,
                "--output", self.temp_output_dir,
                "--text", text,  # Pass text directly
                "--direct"  # Add a flag to indicate direct text input
            ]
            
            logger.info(f"Running original voice generation with direct text: {' '.join(cmd)}")
            
            # Run the command
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=VOICE_POC_PATH
            )
            
            # Wait for the process to complete
            stdout, stderr = process.communicate()
            
            # Check the return code
            if process.returncode != 0:
                logger.error(f"Original voice generation failed with return code: {process.returncode}")
                logger.error(f"STDOUT: {stdout}")
                logger.error(f"STDERR: {stderr}")
                return None, 0
            
            logger.info(f"Original voice generation command succeeded")
            
            # Log the complete output for debugging
            logger.info(f"STDOUT: {stdout}")
            if stderr:
                logger.info(f"STDERR: {stderr}")
            
            # Wait a moment to ensure file system operations complete
            time.sleep(2)
            
            # Search for the output file - simplify the search to focus on recent files
            current_time = time.time()
            newest_file = None
            newest_time = 0
            
            for directory in [self.temp_output_dir, VOICE_POC_PATH]:
                if os.path.exists(directory):
                    for filename in os.listdir(directory):
                        if filename.endswith('.wav'):
                            file_path = os.path.join(directory, filename)
                            file_mtime = os.path.getmtime(file_path)
                            time_diff = current_time - file_mtime
                            if time_diff < 60 and file_mtime > newest_time:
                                newest_time = file_mtime
                                newest_file = file_path
            
            if not newest_file:
                logger.error(f"No output file found after original script generation")
                return None, 0
            
            logger.info(f"Found generated speech from original script at: {newest_file}")
            
            # Load the audio file
            try:
                import torchaudio
                audio, sample_rate = torchaudio.load(newest_file)
                
                # Copy to our output directory with a unique name
                final_output = os.path.join(self.echoforge_output_dir, f"voice_{timestamp}_{unique_id}.wav")
                
                # Save a copy to our output directory
                torchaudio.save(final_output, audio, sample_rate)
                logger.info(f"Saved copy to: {final_output}")
                
                # Return the audio tensor and sample rate
                return audio.squeeze(), sample_rate
                
            except Exception as e:
                logger.error(f"Error loading audio file: {e}")
                return None, 0
            
        except Exception as e:
            logger.exception(f"Error in original script generation: {e}")
            return None, 0
        
        finally:
            # Clean up temporary prompts file
            if prompts_file and os.path.exists(prompts_file):
                try:
                    os.unlink(prompts_file)
                except Exception as e:
                    logger.warning(f"Error removing temporary prompts file: {e}")
    
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