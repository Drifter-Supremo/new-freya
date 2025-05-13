"""
main.py - FastAPI entry point for Freya backend

- Loads environment variables (.env)
- Configures logging
- Sets up FastAPI app and endpoints
- Designed to be run with Uvicorn for local development
"""

from dotenv import load_dotenv
import os
import logging
from fastapi import FastAPI

# Load environment variables from .env file
env_loaded = load_dotenv()

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException

# Global error handler for HTTPException
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTPException: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )

# Global error handler for generic Exception
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )

# Optional: Validation error handler for request data
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"error": "Validation error", "details": exc.errors()},
    )

# CORS middleware: allow all origins, methods, headers (for local/dev only)
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint: used to verify the server is running
@app.get("/health")
def health_check():
    """
    Health check endpoint for monitoring and testing.
    Returns a simple status message if the server is up.
    """
    logger.info("Health check endpoint called.")
    return {"status": "ok"}

# Example: Accessing environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
POSTGRES_URL = os.getenv("POSTGRES_URL")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set in the environment. Please check your .env file.")
if not POSTGRES_URL:
    raise RuntimeError("POSTGRES_URL is not set in the environment. Please check your .env file.")

# Example usage:
# import openai
# openai.api_key = OPENAI_API_KEY
# ...

# Example usage for SQLModel/SQLAlchemy:
# from sqlmodel import create_engine
# engine = create_engine(POSTGRES_URL)
# ...
# Run the app locally with: python app/main.py or uvicorn app.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
