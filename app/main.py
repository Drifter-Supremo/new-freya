"""
main.py - FastAPI entry point for Freya backend

- Loads environment variables (.env)
- Configures logging
- Sets up FastAPI app and endpoints
- Designed to be run with Uvicorn for local development
"""

"""
main.py - FastAPI entry point for Freya backend (modular version)

- Loads config, logging, and error handlers from core modules
- Registers API routers from api/routes
- Designed to be run with Uvicorn for local development
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import centralized config and logger
from app.core.config import CORS_CONFIG, logger
# Import and register error handlers
from app.core.errors import add_error_handlers
# Import API routes
from app.api.routes.health import router as health_router
from app.api.routes.db_health import router as db_health_router
from app.api.routes.conversation import router as conversation_router
from app.api.routes.user_fact import router as user_fact_router
from app.api.routes.topic import router as topic_router
from app.api.routes.memory import router as memory_router
from app.api.routes.chat import router as chat_router
from app.api.routes.events import router as events_router

# Create FastAPI app
app = FastAPI()

# Set up CORS middleware (dev: allow all)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_CONFIG['allow_origins'],
    allow_credentials=CORS_CONFIG['allow_credentials'],
    allow_methods=CORS_CONFIG['allow_methods'],
    allow_headers=CORS_CONFIG['allow_headers'],
)

# Register error handlers
add_error_handlers(app)

# Register API routers
app.include_router(health_router)
app.include_router(db_health_router)
app.include_router(conversation_router)
app.include_router(user_fact_router)
app.include_router(topic_router)
app.include_router(memory_router)
app.include_router(chat_router)
app.include_router(events_router)

# Run the app locally
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
