"""
test_chat_endpoint.py - Manual test script for the chat completions endpoint
"""
import requests
import json
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Example user and conversation IDs (replace with actual IDs from your database)
USER_ID = "11111111-1111-1111-1111-111111111111"  # Replace with actual user ID
CONVERSATION_ID = None  # Set to None for new conversation, or use existing ID

# API endpoint
API_URL = "http://localhost:8000/chat/completions"


def test_chat_completion():
    """Test the chat completions endpoint."""
    
    # Test data
    request_data = {
        "messages": [
            {"role": "user", "content": "Hello Freya! How are you doing today?"}
        ],
        "user_id": USER_ID,
        "model": "ft:gpt-4.1-mini-2025-04-14:gorlea-industries:freya:BULkCmxj",
        "temperature": 1.0,
        "max_tokens": 800,
        "stream": False
    }
    
    # Add conversation ID if provided
    if CONVERSATION_ID:
        request_data["conversation_id"] = CONVERSATION_ID
    
    print(f"Testing chat completion endpoint at {API_URL}")
    print(f"Request data: {json.dumps(request_data, indent=2)}")
    
    try:
        # Make request
        response = requests.post(API_URL, json=request_data)
        
        # Print response
        print(f"\nResponse status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"\nResponse data: {json.dumps(response_data, indent=2)}")
            
            # Extract and display the assistant's message
            if response_data.get("choices"):
                assistant_message = response_data["choices"][0]["message"]["content"]
                print(f"\nAssistant response: {assistant_message}")
        else:
            print(f"\nError response: {response.text}")
            
    except Exception as e:
        print(f"\nError making request: {str(e)}")


def test_memory_query():
    """Test the chat completions endpoint with a memory-related query."""
    
    # Test data with memory query
    request_data = {
        "messages": [
            {"role": "user", "content": "Do you remember what we talked about last time?"}
        ],
        "user_id": USER_ID,
        "model": "ft:gpt-4.1-mini-2025-04-14:gorlea-industries:freya:BULkCmxj",
        "temperature": 1.0,
        "max_tokens": 800,
        "stream": False
    }
    
    print(f"\nTesting memory query at {API_URL}")
    print(f"Request data: {json.dumps(request_data, indent=2)}")
    
    try:
        # Make request
        response = requests.post(API_URL, json=request_data)
        
        # Print response
        print(f"\nResponse status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"\nResponse data: {json.dumps(response_data, indent=2)}")
            
            # Extract and display the assistant's message
            if response_data.get("choices"):
                assistant_message = response_data["choices"][0]["message"]["content"]
                print(f"\nAssistant response: {assistant_message}")
        else:
            print(f"\nError response: {response.text}")
            
    except Exception as e:
        print(f"\nError making request: {str(e)}")


def test_conversation_continuation():
    """Test continuing an existing conversation."""
    
    # First message
    first_request = {
        "messages": [
            {"role": "user", "content": "Hi Freya! I want to talk about Python programming."}
        ],
        "user_id": USER_ID,
        "model": "ft:gpt-4.1-mini-2025-04-14:gorlea-industries:freya:BULkCmxj",
        "temperature": 1.0,
        "max_tokens": 800,
        "stream": False
    }
    
    print(f"\nTesting conversation continuation...")
    print(f"First request: {json.dumps(first_request, indent=2)}")
    
    try:
        # Make first request
        response1 = requests.post(API_URL, json=first_request)
        
        if response1.status_code == 200:
            response1_data = response1.json()
            conversation_id = response1_data["id"]
            assistant_response1 = response1_data["choices"][0]["message"]["content"]
            
            print(f"\nFirst response: {assistant_response1}")
            print(f"Conversation ID: {conversation_id}")
            
            # Second message in same conversation
            second_request = {
                "messages": [
                    {"role": "user", "content": "Hi Freya! I want to talk about Python programming."},
                    {"role": "assistant", "content": assistant_response1},
                    {"role": "user", "content": "What are the main advantages of using Python?"}
                ],
                "user_id": USER_ID,
                "conversation_id": conversation_id,
                "model": "ft:gpt-4.1-mini-2025-04-14:gorlea-industries:freya:BULkCmxj",
                "temperature": 1.0,
                "max_tokens": 800,
                "stream": False
            }
            
            print(f"\nSecond request: {json.dumps(second_request, indent=2)}")
            
            # Make second request
            response2 = requests.post(API_URL, json=second_request)
            
            if response2.status_code == 200:
                response2_data = response2.json()
                assistant_response2 = response2_data["choices"][0]["message"]["content"]
                print(f"\nSecond response: {assistant_response2}")
            else:
                print(f"\nError in second request: {response2.text}")
        else:
            print(f"\nError in first request: {response1.text}")
            
    except Exception as e:
        print(f"\nError: {str(e)}")


if __name__ == "__main__":
    print("Chat Completions Endpoint Test")
    print("==============================")
    
    # Test basic chat completion
    test_chat_completion()
    
    # Test memory query
    test_memory_query()
    
    # Test conversation continuation
    test_conversation_continuation()
    
    print("\nTest completed!")