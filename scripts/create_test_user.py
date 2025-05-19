"""
create_test_user.py - Create a test user for testing the chat endpoint
"""
import sys
import os
from datetime import datetime
from uuid import uuid4

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.db import SessionLocal, init_db
from app.models.user import User
from app.repository.user import UserRepository


def create_test_user():
    """Create a test user for testing."""
    # Initialize database
    init_db()
    
    # Create session
    db = SessionLocal()
    user_repo = UserRepository(db)
    
    try:
        # Create test user
        test_user_data = {
            "id": uuid4(),
            "name": "Test User",
            "email": "test@example.com",
            "created_at": datetime.utcnow()
        }
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == test_user_data["email"]).first()
        if existing_user:
            print(f"User already exists with ID: {existing_user.id}")
            return existing_user.id
        
        # Create new user
        user = user_repo.create(test_user_data)
        print(f"Created test user with ID: {user.id}")
        print(f"User details: {user}")
        
        return user.id
        
    except Exception as e:
        print(f"Error creating test user: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    user_id = create_test_user()
    if user_id:
        print(f"\nYou can now use this user ID in test_chat_endpoint.py:")
        print(f'USER_ID = "{user_id}"')