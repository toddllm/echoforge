"""
EchoForge - API Routes

This module defines the API routes for the EchoForge application.
"""

import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from typing import Dict, Any

from flask import Blueprint, jsonify, request, current_app, send_from_directory
from werkzeug.utils import secure_filename

# Set up logging
logger = logging.getLogger("echoforge.api")

# Create a thread pool for async tasks
executor = ThreadPoolExecutor(max_workers=2)
tasks = {}  # Store tasks by ID
task_lock = Lock()  # Lock for thread safety

# Create API blueprint
api_bp = Blueprint("api", __name__, url_prefix="/api")

def register_api_routes(app):
    """Register the API routes with the Flask application."""
    app.register_blueprint(api_bp)

# API Routes
@api_bp.route("/health", methods=["GET"])
def health_check():
    """Simple health check endpoint."""
    return jsonify({"status": "healthy", "version": "0.1.0"})

@api_bp.route("/voices", methods=["GET"])
def get_voices():
    """Return the list of available voices."""
    voice_dir = current_app.config["VOICE_DIR"]
    voices = []
    
    try:
        # Process all .wav files in the voice directory
        for filename in os.listdir(voice_dir):
            if filename.endswith(".wav"):
                # Extract metadata from filename (convention: speaker_id_temp_value_topk_value_style.wav)
                parts = filename.replace(".wav", "").split("_")
                
                if len(parts) >= 6:
                    voice_info = {
                        "filename": filename,
                        "filepath": os.path.join("voices", filename),
                        "speaker_id": int(parts[1]) if parts[1].isdigit() else 0,
                        "gender": "male" if int(parts[1]) % 2 == 1 else "female" if int(parts[1]) % 2 == 0 else "unknown",
                        "temperature": float(parts[3]) if parts[3].replace(".", "", 1).isdigit() else 0.5,
                        "topk": int(parts[5]) if parts[5].isdigit() else 50,
                        "style": " ".join(parts[6:]) if len(parts) > 6 else "default",
                        "character_name": None,
                        "character_role": None,
                        "character_description": None,
                    }
                    
                    # Check if there's a corresponding character JSON file
                    character_file = os.path.join(
                        current_app.config["CHARACTER_DIR"],
                        f"{filename.replace('.wav', '.json')}"
                    )
                    
                    if os.path.exists(character_file):
                        import json
                        try:
                            with open(character_file, "r") as f:
                                character_data = json.load(f)
                                voice_info.update(character_data)
                        except Exception as e:
                            logger.error(f"Error loading character data for {filename}: {e}")
                    
                    voices.append(voice_info)
                else:
                    # Handle simple filename format without detailed metadata
                    voices.append({
                        "filename": filename,
                        "filepath": os.path.join("voices", filename),
                        "speaker_id": 0,
                        "gender": "unknown",
                        "temperature": 0.5,
                        "topk": 50,
                        "style": "default",
                        "character_name": filename.replace(".wav", ""),
                        "character_role": None,
                        "character_description": None,
                    })
    except Exception as e:
        logger.error(f"Error loading voices: {e}")
        return jsonify({"error": str(e)}), 500
    
    return jsonify(voices)

@api_bp.route("/characters", methods=["GET"])
def get_characters():
    """Return the list of available character profiles."""
    character_dir = current_app.config["CHARACTER_DIR"]
    characters = []
    
    try:
        # Process all .json files in the character directory
        for filename in os.listdir(character_dir):
            if filename.endswith(".json"):
                character_file = os.path.join(character_dir, filename)
                
                import json
                try:
                    with open(character_file, "r") as f:
                        character_data = json.load(f)
                        character_data["filename"] = filename
                        characters.append(character_data)
                except Exception as e:
                    logger.error(f"Error loading character data for {filename}: {e}")
    except Exception as e:
        logger.error(f"Error loading characters: {e}")
        return jsonify({"error": str(e)}), 500
    
    return jsonify(characters)

@api_bp.route("/characters", methods=["POST"])
def create_character():
    """Create a new character profile."""
    try:
        character_data = request.json
        
        if not character_data:
            return jsonify({"error": "No character data provided"}), 400
        
        if "character_name" not in character_data:
            return jsonify({"error": "Character name is required"}), 400
        
        # Generate filename from character name
        filename = secure_filename(
            f"{character_data['character_name'].lower().replace(' ', '_')}.json"
        )
        
        character_file = os.path.join(current_app.config["CHARACTER_DIR"], filename)
        
        import json
        with open(character_file, "w") as f:
            json.dump(character_data, f, indent=2)
        
        return jsonify({"status": "success", "filename": filename}), 201
    
    except Exception as e:
        logger.error(f"Error creating character: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route("/generate", methods=["POST"])
def generate_speech():
    """Generate speech from text using a voice profile."""
    text = request.json.get("text", "")
    voice_path = request.json.get("voice", "")
    device = request.json.get("device", "auto")
    
    if not text:
        return jsonify({"error": "Text is required"}), 400
    
    if not voice_path:
        return jsonify({"error": "Voice path is required"}), 400
    
    try:
        # Create a unique task ID
        task_id = str(int(time.time() * 1000))
        
        with task_lock:
            tasks[task_id] = {
                "status": "pending",
                "progress": 0,
                "error": None,
                "output": None,
                "text_length": len(text),
                "start_time": time.time()
            }
        
        # Submit the generation task to run in the background
        executor.submit(
            perform_generation, 
            task_id=task_id,
            text=text,
            voice_path=voice_path,
            device=device,
        )
        
        return jsonify({"task_id": task_id})
    
    except Exception as e:
        logger.exception(f"Error submitting generation task: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route("/status/<task_id>", methods=["GET"])
def get_task_status(task_id):
    """Get the status of a generation task."""
    with task_lock:
        if task_id not in tasks:
            return jsonify({"error": "Task not found"}), 404
        
        return jsonify(tasks[task_id])

@api_bp.route("/output/<path:filename>", methods=["GET"])
def serve_output(filename):
    """Serve generated output files."""
    return send_from_directory(current_app.config["OUTPUT_DIR"], filename)

@api_bp.route("/voices/<path:filename>", methods=["GET"])
def serve_voice(filename):
    """Serve voice sample files."""
    return send_from_directory(current_app.config["VOICE_DIR"], filename)

@api_bp.route("/diagnostics", methods=["GET"])
def diagnostics():
    """Run a diagnostic check on the system."""
    import platform
    import psutil
    
    try:
        # System info
        system_info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(logical=False),
            "logical_cpu_count": psutil.cpu_count(logical=True),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2)
        }
        
        # PyTorch and CUDA info
        torch_info = {}
        try:
            import torch
            torch_info = {
                "torch_version": torch.__version__,
                "cuda_available": torch.cuda.is_available(),
                "cuda_device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
            }
            
            # Add CUDA device info if available
            if torch.cuda.is_available():
                device = torch.cuda.current_device()
                free_memory = torch.cuda.get_device_properties(device).total_memory - torch.cuda.memory_allocated(device)
                free_memory_mb = free_memory / (1024 * 1024)
                torch_info["cuda_device_name"] = torch.cuda.get_device_name(device)
                torch_info["cuda_device_capability"] = torch.cuda.get_device_capability(device)
                torch_info["cuda_free_memory_mb"] = round(free_memory_mb, 2)
        except ImportError:
            torch_info["error"] = "PyTorch not installed"
        
        # Directory info
        directory_info = {
            "data_dir": os.path.exists(current_app.config["DATA_DIR"]),
            "voice_dir": os.path.exists(current_app.config["VOICE_DIR"]),
            "character_dir": os.path.exists(current_app.config["CHARACTER_DIR"]),
            "output_dir": os.path.exists(current_app.config["OUTPUT_DIR"]),
            "voice_count": len([f for f in os.listdir(current_app.config["VOICE_DIR"]) 
                               if f.endswith(".wav")]) if os.path.exists(current_app.config["VOICE_DIR"]) else 0,
            "character_count": len([f for f in os.listdir(current_app.config["CHARACTER_DIR"]) 
                                  if f.endswith(".json")]) if os.path.exists(current_app.config["CHARACTER_DIR"]) else 0,
            "output_count": len([f for f in os.listdir(current_app.config["OUTPUT_DIR"]) 
                               if f.endswith(".wav")]) if os.path.exists(current_app.config["OUTPUT_DIR"]) else 0,
        }
        
        return jsonify({
            "system": system_info,
            "torch": torch_info,
            "directories": directory_info,
            "status": "healthy"
        })
    
    except Exception as e:
        logger.exception(f"Error running diagnostics: {e}")
        return jsonify({"error": str(e), "status": "error"}), 500

def perform_generation(task_id, text, voice_path, device):
    """Perform speech generation in a background thread."""
    try:
        with task_lock:
            if task_id not in tasks:
                return
            
            tasks[task_id]["status"] = "running"
            tasks[task_id]["progress"] = 10
        
        logger.info(f"Starting generation for task {task_id}: '{text}'")
        
        # Import the voice generator here to avoid circular imports
        from app.core.voice_generator import generate_speech
        
        # Update progress
        with task_lock:
            tasks[task_id]["progress"] = 30
        
        # Generate a unique output filename
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"generated_{timestamp}.wav"
        output_path = os.path.join(current_app.config["OUTPUT_DIR"], output_filename)
        
        # Generate speech
        start_time = time.time()
        success = generate_speech(
            text=text,
            voice_path=voice_path,
            output_path=output_path,
            device=device
        )
        generation_time = time.time() - start_time
        
        # Update task status based on generation result
        with task_lock:
            tasks[task_id]["progress"] = 90
            
            if success and os.path.exists(output_path):
                tasks[task_id]["status"] = "complete"
                tasks[task_id]["progress"] = 100
                tasks[task_id]["output"] = f"output/{output_filename}"
                tasks[task_id]["generation_time"] = generation_time
                logger.info(f"Generation complete for task {task_id}. Audio saved to: {output_path}")
            else:
                tasks[task_id]["status"] = "error"
                tasks[task_id]["progress"] = 100
                tasks[task_id]["error"] = "Failed to generate speech output"
                logger.error(f"Generation failed for task {task_id}")
    
    except Exception as e:
        logger.exception(f"Error during speech generation: {e}")
        with task_lock:
            if task_id in tasks:
                tasks[task_id]["status"] = "error"
                tasks[task_id]["progress"] = 100
                tasks[task_id]["error"] = str(e) 