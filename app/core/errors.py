"""
errors.py - Global error handlers for FastAPI
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from app.core.config import logger


def add_error_handlers(app):
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.error(f"HTTPException: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled Exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = []
        for error in exc.errors():
            # Convert error dict to make it JSON serializable
            err_dict = {
                "loc": error.get("loc"),
                "msg": error.get("msg"),
                "type": error.get("type")
            }
            errors.append(err_dict)
        
        logger.error(f"Validation error: {errors}")
        return JSONResponse(
            status_code=422,
            content={"error": "Validation error", "details": errors},
        )
