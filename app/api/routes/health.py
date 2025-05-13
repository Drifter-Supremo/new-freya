"""
health.py - Health check endpoint
"""
from fastapi import APIRouter
from app.core.config import logger

router = APIRouter()

@router.get("/health")
def health_check():
    """
    Health check endpoint for monitoring and testing.
    Returns a simple status message if the server is up.
    """
    logger.info("Health check endpoint called.")
    return {"status": "ok"}
