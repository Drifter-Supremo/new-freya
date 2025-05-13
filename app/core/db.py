"""
db.py - SQLAlchemy engine and session with connection pooling for Freya backend
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

load_dotenv()

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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
