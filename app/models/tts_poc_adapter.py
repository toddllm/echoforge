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
        
        # Use a scene ID based on timestamp and random values to avoid collisions
        import random
        scene_id = int((time.time() * 10000) % 1000000) + random.randint(1, 1000)
        
        # Create a JSON prompts file in the expected format
        prompts_file = None
        try:
            # Create a temporary file for the prompts
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp:
                # Format as JSON with scene_id as key and text as value
                json.dump({str(scene_id): text}, temp)
                prompts_file = temp.name
            
            logger.debug(f"Created prompts file: {prompts_file}")
            
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
            
            # Build the command - Use EchoForge temp directory for output
            cmd = [
                VOICE_GENERATOR_SCRIPT,
                "--scene", str(scene_id),
                "--device", device,
                "--output", self.temp_output_dir,
                "--prompts", prompts_file
            ]
            
            logger.info(f"Running voice generation with device: {device}, command: {' '.join(cmd)}")
            
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
                logger.error(f"Voice generation failed with return code: {process.returncode}")
                logger.error(f"STDOUT: {stdout}")
                logger.error(f"STDERR: {stderr}")
                
                # Check for typical errors
                if "CUDA out of memory" in stderr:
                    logger.warning("CUDA out of memory error detected")
                    if device == "cuda":
                        logger.info("CUDA failed, falling back to CPU")
                        # Recursive call with CPU device
                        return self._generate_with_voice_script(text, speaker_id, temperature, top_k, "cpu")
                
                return None, 0
            
            logger.info(f"Voice generation command succeeded")
            
            # Log the complete output for debugging
            logger.info(f"STDOUT: {stdout}")
            if stderr:
                logger.info(f"STDERR: {stderr}")
            
            # Wait a moment to ensure file system operations complete
            time.sleep(2)
            
            # Parse the output to find any clues about file location
            potential_output_path = None
            
            # Try to find mentions of file paths or creation in the stdout
            for line in stdout.splitlines():
                # Search for common output patterns
                for pattern in ["saved to", "output", "generated", "file", "wav", "audio", "created", "wrote"]:
                    if pattern in line.lower():
                        logger.info(f"Possible output path hint: {line}")
                
                # Look for paths
                if "/" in line and (".wav" in line.lower() or ".mp3" in line.lower() or ".ogg" in line.lower()):
                    # Extract potential path - look for patterns like /path/to/file.wav
                    path_candidates = []
                    for word in line.split():
                        if "/" in word and ("." in word or word.endswith("/")):
                            path_candidates.append(word)
                    
                    for path in path_candidates:
                        # Clean up the path (remove quotes, commas, etc.)
                        clean_path = path.strip("'\",.;:()[]{}").strip()
                        if os.path.exists(clean_path):
                            potential_output_path = clean_path
                            logger.info(f"Found potential output path in stdout: {potential_output_path}")
                            break
                
                # Look for specific output patterns in the stdout to find the file path
                if any(phrase in line for phrase in ["Output file:", "Generated file:", "Saved to:", "Writing to", "Audio file"]):
                    parts = line.split(":", 1) if ":" in line else line.split("to ", 1) if "to " in line else (line, "")
                    if len(parts) == 2:
                        possible_path = parts[1].strip().strip("'\",.;:()[]{}").strip()
                        # Check if this looks like a file path
                        if "/" in possible_path and os.path.exists(possible_path) and possible_path.endswith(('.wav', '.mp3', '.ogg')):
                            potential_output_path = possible_path
                            logger.info(f"Found output path from stdout pattern match: {potential_output_path}")
                            break
            
            # Look for the output file
            output_path = potential_output_path
            
            # Debug: List all WAV files in the temp directory
            logger.info(f"Checking for WAV files in temp directory: {self.temp_output_dir}")
            temp_wav_files = glob.glob(os.path.join(self.temp_output_dir, "*.wav"))
            for wav_file in temp_wav_files:
                logger.info(f"Found WAV file in temp dir: {wav_file}")
            
            # Debug: List all WAV files in the voice_poc directory
            logger.info(f"Checking for WAV files in voice_poc directory: {VOICE_POC_PATH}")
            voice_poc_wav_files = glob.glob(os.path.join(VOICE_POC_PATH, "*.wav"))
            for wav_file in voice_poc_wav_files:
                logger.info(f"Found WAV file in voice_poc dir: {wav_file}")
            
            # If we didn't find it in stdout, check various locations
            if not output_path or not os.path.exists(output_path):
                # Look for files that might contain the scene_id in the name
                scene_patterns = [
                    # Different possible prefixes
                    f"*{scene_id}*.wav",
                    f"*scene*{scene_id}*.wav",
                    f"*voice*{scene_id}*.wav",
                    f"*output*{scene_id}*.wav",
                    f"*audio*{scene_id}*.wav",
                    
                    # Specific scene id patterns
                    f"*scene_{scene_id}*.wav",
                    f"*scene-{scene_id}*.wav",
                    f"*scene{scene_id}*.wav",
                ]
                
                # Directories to search for scene ID-based files
                scene_search_dirs = [
                    self.temp_output_dir,
                    VOICE_POC_PATH,
                    os.path.join(MOVIE_MAKER_PATH, "hdmy5movie_voices", "scenes"),
                    MOVIE_MAKER_PATH,
                    os.path.dirname(VOICE_POC_PATH),
                    os.getcwd()
                ]
                
                for search_dir in scene_search_dirs:
                    if os.path.exists(search_dir):
                        for pattern in scene_patterns:
                            matching_files = glob.glob(os.path.join(search_dir, pattern))
                            if matching_files:
                                output_path = matching_files[0]
                                logger.info(f"Found file matching scene ID pattern {pattern} in {search_dir}: {output_path}")
                                break
                        
                        # Break the outer loop if file found
                        if output_path and os.path.exists(output_path):
                            break
                
                # If still not found, try standard patterns in our temp directory
                if not output_path or not os.path.exists(output_path):
                    potential_paths = [
                        os.path.join(self.temp_output_dir, f"scene_{scene_id}.wav"),
                        os.path.join(self.temp_output_dir, f"scene{scene_id}.wav"),
                        os.path.join(self.temp_output_dir, f"{scene_id}.wav"),
                        os.path.join(VOICE_POC_PATH, f"output_{scene_id}.wav"),
                        os.path.join(VOICE_POC_PATH, f"scene_{scene_id}.wav"),
                        os.path.join(VOICE_POC_PATH, f"scene_{scene_id}_*.wav"),  # Using glob pattern
                        os.path.join(self.temp_output_dir, f"voice_{scene_id}.wav")
                    ]
                    
                    # Also check the original movie_maker paths as fallback
                    movie_maker_paths = [
                        os.path.join(MOVIE_MAKER_PATH, "hdmy5movie_voices", "scenes", f"scene_{scene_id}.wav"),
                        os.path.join(MOVIE_MAKER_PATH, "hdmy5movie_voices", "scenes", f"scene{scene_id}.wav"),
                        os.path.join(MOVIE_MAKER_PATH, "hdmy5movie_voices", "scenes", f"{scene_id}.wav")
                    ]
                    
                    # Combine both lists
                    potential_paths.extend(movie_maker_paths)
                    
                    # Check for newest .wav files in all potential directories
                    current_time = time.time()
                    directories_to_check = [
                        self.temp_output_dir,
                        VOICE_POC_PATH,
                        os.path.join(MOVIE_MAKER_PATH, "hdmy5movie_voices", "scenes"),
                        MOVIE_MAKER_PATH,
                        os.path.dirname(VOICE_POC_PATH),
                        os.getcwd()
                    ]
                    
                    newest_file = None
                    newest_time = 0
                    
                    for directory in directories_to_check:
                        if os.path.exists(directory):
                            logger.info(f"Checking directory for WAV files: {directory}")
                            for filename in os.listdir(directory):
                                if filename.endswith('.wav'):
                                    file_path = os.path.join(directory, filename)
                                    file_mtime = os.path.getmtime(file_path)
                                    time_diff = current_time - file_mtime
                                    logger.info(f"Found WAV file: {file_path}, modified {time_diff:.1f} seconds ago")
                                    if time_diff < 120 and file_mtime > newest_time:  # Expanded search to 2 minutes
                                        newest_time = file_mtime
                                        newest_file = file_path
                    
                    # First check the exact patterns
                    for path in potential_paths:
                        # Handle glob patterns
                        if '*' in path:
                            matching_files = glob.glob(path)
                            if matching_files:
                                output_path = matching_files[0]
                                logger.debug(f"Found output using glob pattern {path}: {output_path}")
                                break
                        elif os.path.exists(path):
                            output_path = path
                            logger.debug(f"Found output using pattern matching: {output_path}")
                            break
                    
                    # If not found, use the newest file
                    if (not output_path or not os.path.exists(output_path)) and newest_file:
                        output_path = newest_file
                        logger.info(f"Found newest wav file: {output_path}, modified {current_time - newest_time:.1f} seconds ago")
            
            # If still not found, try desperate measures: find any WAV file modified in the last 2 minutes
            if not output_path or not os.path.exists(output_path):
                logger.warning(f"No output file found using standard methods. Trying filesystem search...")
                
                # Run the find command to locate recently modified wav files
                find_cmd = [
                    "find", 
                    "/tmp", "/home/tdeshane",  # Directories to search
                    "-name", "*.wav",
                    "-mmin", "-2",  # Modified in the last 2 minutes
                    "-type", "f"    # Regular files only
                ]
                
                try:
                    # Run find command
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
                            # Find the most recently modified file
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
                # Log the stdout again for reference
                logger.error(f"Output file not found after exhaustive search for scene_id: {scene_id}")
                logger.error(f"STDOUT content for reference: {stdout}")
                return None, 0
            
            logger.info(f"Found generated speech at: {output_path}")
            
            # Load the audio file
            try:
                import torchaudio
                audio, sample_rate = torchaudio.load(output_path)
                
                # Copy to our output directory with a unique name
                timestamp = int(time.time())
                unique_id = str(scene_id)[-8:]  # Use last 8 digits of scene_id
                output_filename = f"voice_{timestamp}_{unique_id}.wav"
                final_output = os.path.join(self.echoforge_output_dir, output_filename)
                
                # Save a copy to our output directory
                torchaudio.save(final_output, audio, sample_rate)
                logger.info(f"Saved copy to: {final_output}")
                
                # Return the audio tensor and sample rate
                return audio.squeeze(), sample_rate
                
            except Exception as e:
                logger.error(f"Error loading audio file {output_path}: {e}")
                return None, 0
            
        except Exception as e:
            logger.exception(f"Error generating speech: {e}")
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