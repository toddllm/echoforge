"""
Voice Browser API

This module provides endpoints for browsing and serving voice files.
"""

import os
import glob
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse

from app.core import config

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["voices"])

@router.get("/voice-browser", response_class=HTMLResponse)
async def browse_voices(request: Request):
    """
    Display a web page with all generated voice files for verification.
    """
    # Get all voice files from the configured output directory
    voice_dir = os.path.join(config.OUTPUT_DIR, "generated")
    voice_files = []
    
    if os.path.exists(voice_dir):
        voice_files.extend(glob.glob(os.path.join(voice_dir, "*.wav")))
    
    # Also check the echoforge/generated directory
    alt_voice_dir = "echoforge/generated"
    if os.path.exists(alt_voice_dir):
        voice_files.extend(glob.glob(os.path.join(alt_voice_dir, "*.wav")))
    
    # Log what we found
    logger.info(f"Found {len(voice_files)} voice files")
    for file in voice_files[:5]:  # Log first 5 files
        logger.info(f"Voice file: {file}")
    
    # Sort by modification time (newest first)
    voice_files.sort(key=os.path.getmtime, reverse=True)
    
    # Create a list of file info
    files = []
    for file_path in voice_files:
        filename = os.path.basename(file_path)
        mtime = os.path.getmtime(file_path)
        size = os.path.getsize(file_path) / 1024  # Size in KB
        files.append({
            "filename": filename,
            "path": f"/api/voices/{filename}",
            "mtime": mtime,
            "size": f"{size:.1f} KB"
        })
    
    # Create a simple HTML page
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>EchoForge Voice Files</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #333; }}
            .file-list {{ margin-top: 20px; }}
            .file-item {{ 
                border: 1px solid #ddd; 
                padding: 10px; 
                margin-bottom: 10px; 
                border-radius: 5px;
                background-color: #f9f9f9;
            }}
            .file-info {{ margin-bottom: 5px; color: #666; }}
            audio {{ width: 100%; }}
        </style>
    </head>
    <body>
        <h1>EchoForge Generated Voice Files</h1>
        <p>Total files: {len(files)}</p>
        <div class="file-list">
    """
    
    # Add each file
    for file in files:
        html += f"""
        <div class="file-item">
            <div class="file-info">Filename: {file['filename']}</div>
            <div class="file-info">Size: {file['size']}</div>
            <audio controls>
                <source src="{file['path']}" type="audio/wav">
                Your browser does not support the audio element.
            </audio>
        </div>
        """
    
    html += """
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)

@router.get("/voices/{filename}")
async def get_voice_file(filename: str):
    """
    Serve a voice file from the generated directory.
    """
    # Construct the file path
    voice_dir = os.path.join(config.OUTPUT_DIR, "generated")
    file_path = os.path.join(voice_dir, filename)
    
    # Check if the file exists
    if not os.path.exists(file_path):
        # Try looking in the root generated directory
        alt_file_path = os.path.join("echoforge/generated", filename)
        if os.path.exists(alt_file_path):
            return FileResponse(alt_file_path, media_type="audio/wav")
        
        # If still not found, raise 404
        raise HTTPException(status_code=404, detail=f"Voice file {filename} not found")
    
    # Return the file
    return FileResponse(file_path, media_type="audio/wav") 