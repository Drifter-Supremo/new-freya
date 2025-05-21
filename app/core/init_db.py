"""
init_db.py - Script to initialize database tables for Freya backend
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if we're using Firebase
USING_FIREBASE = os.getenv("USE_FIREBASE", "false").lower() in ("true", "1", "yes")

def init_db():
    if USING_FIREBASE:
        print("Using Firebase - no need to initialize PostgreSQL tables")
        return
    
    # Only import these for PostgreSQL mode
    from app.core.db import engine
    from app.models import Base
    
    print("Creating PostgreSQL tables...")
    Base.metadata.create_all(bind=engine)
    print("All tables created.")

if __name__ == "__main__":
    init_db()
