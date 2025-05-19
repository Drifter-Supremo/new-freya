"""
create_test_user.py - Creates a test user for SSE testing
"""
import sys
from sqlalchemy.orm import Session
import uuid

# Add the parent directory to the path for imports
sys.path.append(".")

from app.core.db import SessionLocal
from app.models.user import User
from app.repository.user import UserRepository


def create_user(db: Session):
    """Create a test user with ID 1"""
    
    # Check if user with ID 1 already exists
    user_repo = UserRepository(db)
    existing_user = user_repo.get(1)
    if existing_user:
        print(f"User with ID 1 already exists: {existing_user.username}")
        return existing_user
    
    # Generate a unique username
    unique_id = uuid.uuid4().hex[:8]
    username = f"testuser_{unique_id}"
    email = f"test_{unique_id}@example.com"
    
    # Create user data
    user_data = {
        "id": 1,  # Force ID to be 1
        "username": username,
        "email": email,
        "hashed_password": "dummy_password_hash"
    }
    
    # Create the user
    try:
        user = user_repo.create(user_data)
        db.commit()
        print(f"Created user with ID: {user.id}, username: {user.username}")
        return user
    except Exception as e:
        db.rollback()
        print(f"Error creating user: {str(e)}")
        raise


if __name__ == "__main__":
    db = SessionLocal()
    try:
        user = create_user(db)
        print(f"User ID: {user.id}")
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
    finally:
        db.close()
