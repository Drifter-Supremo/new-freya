"""
init_db.py - Script to initialize database tables for Freya backend
"""
from app.core.db import engine
from app.models import Base

def init_db():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("All tables created.")

if __name__ == "__main__":
    init_db()
