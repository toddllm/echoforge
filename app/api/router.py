"""
Main API Router

This module configures the main API router and includes all sub-routers.
"""

import logging
from fastapi import APIRouter, Depends, Request, HTTPException

from app.api.voice_routes import router as voice_router
from app.api.debug_routes import router as debug_router
from app.api.status import router as status_router
from app.api.character_showcase_routes import router as character_showcase_router
from app.api.v1 import router as v1_router  # Import v1 compatibility router

from app.core import config

logger = logging.getLogger("echoforge.api.router")

# Create API router with global prefix
router = APIRouter(prefix="/api")

# Include voice generator router
router.include_router(voice_router)

# Include debug router only in debug mode
if config.DEBUG:
    router.include_router(debug_router)

# Include system status router
router.include_router(status_router)

# Include character showcase router if available
if character_showcase_router:
    logger.info("Including character showcase router in main API router")
    router.include_router(character_showcase_router)
    
# Include voice cloning router if available
try:
    from app.api.voice_cloning_routes import router as voice_cloning_router
    if voice_cloning_router:
        logger.info("Including voice cloning router in main API router")
        router.include_router(voice_cloning_router)
except ImportError as e:
    logger.warning(f"Could not import voice cloning router: {e}")
except Exception as e:
    logger.error(f"Error including voice cloning router: {e}")

# Include v1 compatibility router
router.include_router(v1_router)  # Add v1 compatibility router

# Common router dependencies
def get_common_dependencies():
    """Return common dependencies for API routes."""
    return {} 