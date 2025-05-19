"""
test_conversation_endpoints.py - Test all conversation management endpoints
"""
import sys
import os
import requests
import json
from datetime import datetime
from uuid import uuid4

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.db import SessionLocal
from app.core.init_db import init_db
from app.models.user import User
from app.repository.user import UserRepository

# Test configuration
BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}


def test_create_conversation(user_id):
    """Test POST /conversations/ endpoint"""
    print("\n1. Testing POST /conversations/ - Create new conversation")
    response = requests.post(
        f"{BASE_URL}/conversations/?user_id={user_id}",
        headers=HEADERS
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        conversation = response.json()
        print(f"✅ Created conversation {conversation['id']}")
        return conversation['id']
    else:
        print("❌ Failed to create conversation")
        return None


def test_get_recent_conversations(user_id):
    """Test GET /conversations/{user_id}/recent endpoint"""
    print(f"\n2. Testing GET /conversations/{user_id}/recent - Get recent conversations")
    response = requests.get(f"{BASE_URL}/conversations/{user_id}/recent?limit=5")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        conversations = response.json()
        print(f"✅ Found {len(conversations)} recent conversations")
    else:
        print("❌ Failed to get recent conversations")


def test_get_conversation_messages(conversation_id):
    """Test GET /conversations/{conversation_id}/messages endpoint"""
    print(f"\n3. Testing GET /conversations/{conversation_id}/messages - Get messages")
    response = requests.get(
        f"{BASE_URL}/conversations/{conversation_id}/messages?limit=10"
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        messages = response.json()
        print(f"✅ Found {len(messages)} messages")
    else:
        print("❌ Failed to get messages")


def test_search_conversations(user_id):
    """Test GET /conversations/{user_id}/search endpoint"""
    print(f"\n4. Testing GET /conversations/{user_id}/search - Search conversations")
    
    # First, create a test message to search for
    create_test_message(user_id)
    
    # Now search for it
    response = requests.get(
        f"{BASE_URL}/conversations/{user_id}/search?query=test&limit=5"
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        messages = response.json()
        print(f"✅ Found {len(messages)} matching messages")
    else:
        print("❌ Failed to search conversations")


def create_test_message(user_id):
    """Helper to create a test message for search testing"""
    # First create a conversation
    conv_response = requests.post(
        f"{BASE_URL}/conversations/?user_id={user_id}",
        headers=HEADERS
    )
    
    if conv_response.status_code == 200:
        conversation_id = conv_response.json()['id']
        
        # Now create a chat completion with a test message
        chat_data = {
            "messages": [
                {"role": "user", "content": "This is a test message for search functionality"}
            ],
            "user_id": user_id,
            "conversation_id": conversation_id,
            "stream": False
        }
        
        requests.post(f"{BASE_URL}/chat/completions", json=chat_data)


def test_delete_conversation(conversation_id, user_id):
    """Test DELETE /conversations/{conversation_id} endpoint"""
    print(f"\n5. Testing DELETE /conversations/{conversation_id} - Delete conversation")
    response = requests.delete(
        f"{BASE_URL}/conversations/{conversation_id}?user_id={user_id}"
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("✅ Successfully deleted conversation")
    else:
        print("❌ Failed to delete conversation")


def test_conversation_context(conversation_id):
    """Test GET /conversations/{conversation_id}/context endpoint"""
    print(f"\n6. Testing GET /conversations/{conversation_id}/context - Get context")
    response = requests.get(
        f"{BASE_URL}/conversations/{conversation_id}/context?message_limit=5"
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("✅ Successfully retrieved conversation context")
    else:
        print("❌ Failed to get conversation context")


def main():
    """Run all conversation endpoint tests"""
    # Initialize database
    init_db()
    
    # Create session
    db = SessionLocal()
    user_repo = UserRepository(db)
    
    try:
        # Create test user
        test_email = f"test_{uuid4().hex[:8]}@example.com"
        test_user_data = {
            "id": uuid4(),
            "name": f"Test User {uuid4().hex[:8]}",
            "email": test_email,
            "created_at": datetime.utcnow()
        }
        
        # Create new user
        user = user_repo.create(test_user_data)
        user_id = user.id
        print(f"Created test user: {user_id}")
        
        # Run tests
        print("\n=== Testing Conversation Management Endpoints ===\n")
        
        # Test 1: Create conversation
        conversation_id = test_create_conversation(user_id)
        
        # Test 2: Get recent conversations
        test_get_recent_conversations(user_id)
        
        # Test 3: Get conversation messages (if we created one)
        if conversation_id:
            test_get_conversation_messages(conversation_id)
            
            # Test 6: Get conversation context
            test_conversation_context(conversation_id)
        
        # Test 4: Search conversations
        test_search_conversations(user_id)
        
        # Test 5: Delete conversation (if we created one)
        if conversation_id:
            test_delete_conversation(conversation_id, user_id)
        
        print("\n=== All tests completed ===\n")
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("NOTE: Make sure the FastAPI server is running!")
    print("Run in another terminal: uvicorn app.main:app --reload")
    print()
    
    try:
        # Test if server is running
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            main()
        else:
            print("ERROR: Server is not responding properly")
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to the server. Make sure it's running!")
        print("Run: uvicorn app.main:app --reload")