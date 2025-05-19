"""
test_all.py - Run all tests for the chat endpoint
"""
import subprocess
import time
import sys
import os
import signal
import requests
from datetime import datetime
from uuid import uuid4

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.db import SessionLocal
from app.core.init_db import init_db
from app.models.user import User
from app.repository.user import UserRepository


def wait_for_server(url="http://localhost:8000/health", timeout=30):
    """Wait for the server to be ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    return False


def test_health_endpoint():
    """Test the health endpoint."""
    print("\n=== Testing Health Endpoint ===")
    response = requests.get("http://localhost:8000/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200


def test_create_user():
    """Test creating a user."""
    print("\n=== Testing User Creation ===")
    db = SessionLocal()
    user_repo = UserRepository(db)
    
    try:
        test_email = f"test_{uuid4().hex[:8]}@example.com"
        test_username = f"test_user_{uuid4().hex[:8]}"
        test_user_data = {
            "username": test_username,
            "email": test_email,
            "hashed_password": "test_password_hash"
        }
        
        user = user_repo.create(test_user_data)
        print(f"Created user: {user.id}")
        return user.id
    except Exception as e:
        print(f"Error: {str(e)}")
        return None
    finally:
        db.close()


def test_chat_endpoint(user_id):
    """Test the chat completions endpoint."""
    print("\n=== Testing Chat Completions Endpoint ===")
    
    request_data = {
        "messages": [
            {"role": "user", "content": "Hello Freya! How are you today?"}
        ],
        "user_id": user_id,
        "model": "ft:gpt-4.1-mini-2025-04-14:gorlea-industries:freya:BULkCmxj",
        "temperature": 1.0,
        "max_tokens": 800,
        "stream": False
    }
    
    print(f"Request: {request_data}")
    
    response = requests.post("http://localhost:8000/chat/completions", json=request_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        response_data = response.json()
        print(f"Response: {response_data}")
        
        if response_data.get("choices"):
            assistant_message = response_data["choices"][0]["message"]["content"]
            print(f"\nFreya says: {assistant_message}")
            return True
    else:
        print(f"Error: {response.text}")
        return False


def test_memory_query(user_id):
    """Test chat endpoint with memory query."""
    print("\n=== Testing Memory Query ===")
    
    # First message
    request1 = {
        "messages": [
            {"role": "user", "content": "My favorite programming language is Python"}
        ],
        "user_id": user_id,
        "model": "ft:gpt-4.1-mini-2025-04-14:gorlea-industries:freya:BULkCmxj",
        "temperature": 1.0,
        "max_tokens": 800,
        "stream": False
    }
    
    response1 = requests.post("http://localhost:8000/chat/completions", json=request1)
    
    if response1.status_code == 200:
        response1_data = response1.json()
        conversation_id = response1_data["id"]
        print(f"First message sent, conversation ID: {conversation_id}")
        
        # Second message asking about memory
        request2 = {
            "messages": [
                {"role": "user", "content": "My favorite programming language is Python"},
                {"role": "assistant", "content": response1_data["choices"][0]["message"]["content"]},
                {"role": "user", "content": "Do you remember what my favorite programming language is?"}
            ],
            "user_id": user_id,
            "conversation_id": conversation_id,
            "model": "ft:gpt-4.1-mini-2025-04-14:gorlea-industries:freya:BULkCmxj",
            "temperature": 1.0,
            "max_tokens": 800,
            "stream": False
        }
        
        response2 = requests.post("http://localhost:8000/chat/completions", json=request2)
        
        if response2.status_code == 200:
            response2_data = response2.json()
            assistant_message = response2_data["choices"][0]["message"]["content"]
            print(f"\nFreya says: {assistant_message}")
            return "Python" in assistant_message
        else:
            print(f"Error in second request: {response2.text}")
            return False
    else:
        print(f"Error in first request: {response1.text}")
        return False


def test_invalid_requests():
    """Test error handling with invalid requests."""
    print("\n=== Testing Error Handling ===")
    
    # Test with invalid user ID
    print("\n1. Testing invalid user ID:")
    request1 = {
        "messages": [
            {"role": "user", "content": "Hello"}
        ],
        "user_id": 99999999,  # Non-existent user ID
        "model": "ft:gpt-4.1-mini-2025-04-14:gorlea-industries:freya:BULkCmxj",
        "temperature": 1.0,
        "max_tokens": 800,
        "stream": False
    }
    
    response1 = requests.post("http://localhost:8000/chat/completions", json=request1)
    print(f"Status: {response1.status_code} (expected 404)")
    print(f"Response: {response1.json()}")
    
    # Test with empty messages
    print("\n2. Testing empty messages:")
    request2 = {
        "messages": [],
        "user_id": 1,  # Valid user ID format
        "model": "ft:gpt-4.1-mini-2025-04-14:gorlea-industries:freya:BULkCmxj",
        "temperature": 1.0,
        "max_tokens": 800,
        "stream": False
    }
    
    response2 = requests.post("http://localhost:8000/chat/completions", json=request2)
    print(f"Status: {response2.status_code} (expected 422)")
    
    # Test with invalid temperature
    print("\n3. Testing invalid temperature:")
    request3 = {
        "messages": [
            {"role": "user", "content": "Hello"}
        ],
        "user_id": 1,  # Valid user ID format
        "model": "ft:gpt-4.1-mini-2025-04-14:gorlea-industries:freya:BULkCmxj",
        "temperature": 3.0,
        "max_tokens": 800,
        "stream": False
    }
    
    response3 = requests.post("http://localhost:8000/chat/completions", json=request3)
    print(f"Status: {response3.status_code} (expected 422)")
    
    return (response1.status_code == 404 and 
            response2.status_code == 422 and 
            response3.status_code == 422)


def main():
    """Run all tests."""
    print("Starting Freya Backend Tests")
    print("============================")
    
    # Initialize database
    init_db()
    
    # Start the server in the background
    print("Starting server...")
    server_process = subprocess.Popen([
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000"
    ])
    
    try:
        # Wait for server to be ready
        print("Waiting for server to be ready...")
        if not wait_for_server():
            print("ERROR: Server failed to start")
            return
        
        print("Server is ready!")
        
        # Run tests
        results = []
        
        # Test 1: Health endpoint
        results.append(("Health Endpoint", test_health_endpoint()))
        
        # Test 2: Create user
        user_id = test_create_user()
        results.append(("User Creation", user_id is not None))
        
        if user_id:
            # Test 3: Basic chat
            results.append(("Basic Chat", test_chat_endpoint(user_id)))
            
            # Test 4: Memory query
            results.append(("Memory Query", test_memory_query(user_id)))
        
        # Test 5: Error handling
        results.append(("Error Handling", test_invalid_requests()))
        
        # Print results
        print("\n\nTest Results")
        print("============")
        for test_name, passed in results:
            status = "PASSED" if passed else "FAILED"
            print(f"{test_name}: {status}")
        
        total_passed = sum(1 for _, passed in results if passed)
        print(f"\nTotal: {total_passed}/{len(results)} tests passed")
        
    except Exception as e:
        print(f"Error during tests: {str(e)}")
    finally:
        # Stop the server
        print("\nStopping server...")
        server_process.terminate()
        server_process.wait()
        print("Server stopped.")


if __name__ == "__main__":
    main()