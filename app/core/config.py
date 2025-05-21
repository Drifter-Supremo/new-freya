"""
config.py - Centralized configuration for environment, logging, and CORS
"""
import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("freya")

# CORS configuration
CORS_CONFIG = {
    'allow_origins': ["*"],
    'allow_credentials': True,
    'allow_methods': ["*"],
    'allow_headers': ["*"],
}

# Check if we're using Firebase (simplified approach)
USING_FIREBASE = os.getenv("USE_FIREBASE", "false").lower() in ("true", "1", "yes")

# Environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
POSTGRES_URL = os.getenv("POSTGRES_URL")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set in the environment. Please check your .env file.")

# Only require PostgreSQL if not using Firebase
if not USING_FIREBASE and not POSTGRES_URL:
    raise RuntimeError("POSTGRES_URL is not set in the environment. Please check your .env file.")

# If using Firebase, log info message
if USING_FIREBASE:
    logger.info("Using Firebase backend (simplified approach)")
    if not POSTGRES_URL:
        logger.info("PostgreSQL URL not set, which is fine when using Firebase")
