"""
test_chat_simple.py - Simple test for the chat endpoint
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


def test_chat_endpoint():
    """Simple test of the chat endpoint."""
    # Initialize database
    init_db()
    
    # Create session
    db = SessionLocal()
    user_repo = UserRepository(db)
    
    try:
        # Create or get test user
        test_email = f"test_{uuid4().hex[:8]}@example.com"
        test_user_data = {
            "id": uuid4(),
            "name": f"Test User {uuid4().hex[:8]}",
            "email": test_email,
            "created_at": datetime.utcnow()
        }
        
        # Create new user
        user = user_repo.create(test_user_data)
        print(f"Created test user: {user.id}")
        
        # Test data
        request_data = {
            "messages": [
                {"role": "user", "content": "Hello Freya! How are you doing today?"}
            ],
            "user_id": str(user.id),
            "model": "ft:gpt-4.1-mini-2025-04-14:gorlea-industries:freya:BULkCmxj",
            "temperature": 1.0,
            "max_tokens": 800,
            "stream": False
        }
        
        print(f"Request data: {request_data}")
        
        # Run the server command in another terminal:
        print("\nNOTE: Make sure the FastAPI server is running!")
        print("Run in another terminal: uvicorn app.main:app --reload")
        
        import requests
        
        try:
            response = requests.post("http://localhost:8000/chat/completions", json=request_data)
            print(f"\nResponse status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"Response: {response_data}")
                
                if response_data.get("choices"):
                    assistant_message = response_data["choices"][0]["message"]["content"]
                    print(f"\nFreya says: {assistant_message}")
            else:
                print(f"Error: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("\nERROR: Cannot connect to the server. Make sure it's running!")
            print("Run: uvicorn app.main:app --reload")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    test_chat_endpoint()