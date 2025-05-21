"""
db.py - SQLAlchemy engine and session with connection pooling for Freya backend
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

load_dotenv()

# Check if we're using Firebase (simplified approach)
USING_FIREBASE = os.getenv("USE_FIREBASE", "false").lower() in ("true", "1", "yes")

# Only set up SQLAlchemy if not using Firebase
if not USING_FIREBASE:
    DATABASE_URL = os.getenv("POSTGRES_URL")
    
    # Connection pool configuration
    POOL_SIZE = 5         # Number of connections to keep in the pool
    MAX_OVERFLOW = 10     # Extra connections allowed above pool_size
    POOL_TIMEOUT = 30     # Seconds to wait before giving up on getting a connection
    
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=POOL_SIZE,
        max_overflow=MAX_OVERFLOW,
        pool_timeout=POOL_TIMEOUT,
        echo=False,  # Set to True for SQL debugging
    )
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    # Dummy engine and session for Firebase mode
    import logging
    logger = logging.getLogger("freya")
    logger.info("Using Firebase mode - PostgreSQL database not initialized")
    
    # Create dummy objects that won't be used
    engine = None
    SessionLocal = None

def get_db():
    if USING_FIREBASE:
        # When using Firebase, return None
        # This should never be called in Firebase mode
        import logging
        logger = logging.getLogger("freya")
        logger.warning("get_db() called in Firebase mode - this should not happen")
        yield None
    else:
        # Normal PostgreSQL session handling
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
