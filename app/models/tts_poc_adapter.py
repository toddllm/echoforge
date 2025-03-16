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
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

# Configure logging
logger = logging.getLogger("echoforge.tts_poc_adapter")

# Default paths
TTS_POC_PATH = "/home/tdeshane/tts_poc"
MOVIE_MAKER_PATH = "/home/tdeshane/movie_maker"
VOICE_POC_PATH = os.path.join(MOVIE_MAKER_PATH, "voice_poc")
VOICE_GENERATOR_SCRIPT = os.path.join(VOICE_POC_PATH, "run_voice_generator.sh")
SCENES_OUTPUT_DIR = os.path.join(MOVIE_MAKER_PATH, "hdmy5movie_voices", "scenes")

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
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
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
            
            # Build the command
            cmd = [
                VOICE_GENERATOR_SCRIPT,
                "--scene", str(scene_id),
                "--device", device,
                "--output", SCENES_OUTPUT_DIR,
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
            
            # Look for the output file
            output_path = None
            
            # Look for specific output patterns in the stdout to find the file path
            for line in stdout.splitlines():
                if "Output file:" in line or "Generated file:" in line or "Saved to:" in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        possible_path = parts[1].strip()
                        if os.path.exists(possible_path) and possible_path.endswith('.wav'):
                            output_path = possible_path
                            logger.debug(f"Found output path from stdout: {output_path}")
                            break
            
            # If we didn't find it in stdout, check various locations
            if not output_path or not os.path.exists(output_path):
                # Try standard patterns
                potential_paths = [
                    os.path.join(SCENES_OUTPUT_DIR, f"scene_{scene_id}.wav"),
                    os.path.join(SCENES_OUTPUT_DIR, f"scene{scene_id}.wav"),
                    os.path.join(SCENES_OUTPUT_DIR, f"{scene_id}.wav"),
                    os.path.join(VOICE_POC_PATH, f"output_{scene_id}.wav"),
                    os.path.join(VOICE_POC_PATH, f"scene_{scene_id}.wav")
                ]
                
                for path in potential_paths:
                    if os.path.exists(path):
                        output_path = path
                        logger.debug(f"Found output using pattern matching: {output_path}")
                        break
            
            if not output_path or not os.path.exists(output_path):
                logger.error(f"Output file not found after exhaustive search")
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
                final_output = os.path.join(self.output_dir, output_filename)
                
                # Save a copy to our output directory
                torchaudio.save(final_output, audio, sample_rate)
                logger.info(f"Saved copy to: {final_output}")
                
                # Return the audio tensor and sample rate
                return audio.squeeze(), sample_rate
                
            except Exception as e:
                logger.error(f"Error loading audio file: {e}")
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
        final_output = os.path.join(self.output_dir, output_filename)
        
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