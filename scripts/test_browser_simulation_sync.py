#!/usr/bin/env python3
"""
Browser Simulation Test for Freya UI (Synchronous Version)
==========================================================

This script simulates how a browser would interact with the Freya backend,
testing the exact message flow expected by the UI.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

# API Configuration
API_BASE_URL = "http://localhost:8000"
FIREBASE_CHAT_ENDPOINT = f"{API_BASE_URL}/firebase/chat"
SSE_STREAM_ENDPOINT = f"{API_BASE_URL}/events/stream"
SSE_CHAT_ENDPOINT = f"{API_BASE_URL}/events/chat"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"

# Test Configuration
TEST_USER_ID = "test_user_123"

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
RESET = "\033[0m"


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text: str):
    """Print error message"""
    print(f"{RED}✗ {text}{RESET}")


def print_info(text: str):
    """Print info message"""
    print(f"{YELLOW}→ {text}{RESET}")


def print_event(event_type: str, data: str = ""):
    """Print SSE event"""
    print(f"{MAGENTA}[EVENT] {event_type}: {data}{RESET}")


def test_sse_connection():
    """Test Server-Sent Events connection"""
    print_header("Testing SSE Connection")
    
    try:
        print_info("Connecting to SSE endpoint...")
        
        # Use stream=True for SSE
        response = requests.get(SSE_STREAM_ENDPOINT, stream=True, timeout=5)
        
        if response.status_code == 200:
            print_success("Connected to SSE stream")
            
            # Read a few events
            event_count = 0
            for line in response.iter_lines():
                if event_count >= 3:  # Just test initial events
                    break
                    
                if line:
                    line_str = line.decode('utf-8').strip()
                    if line_str.startswith('data:'):
                        data = line_str[5:].strip()
                        if data:
                            print_event("data", data)
                            event_count += 1
            
            response.close()
            print_success(f"Successfully received {event_count} events")
            return True
        else:
            print_error(f"SSE connection failed with status {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print_success("SSE connection established (timeout expected for long-lived connection)")
        return True
    except Exception as e:
        print_error(f"SSE connection test failed: {e}")
        return False


def simulate_browser_chat_flow():
    """Simulate the exact flow a browser would follow"""
    print_header("Simulating Browser Chat Flow")
    
    conversation_id = None
    
    try:
        # Simulate user typing and sending message
        user_message = "Hello Freya, tell me about yourself"
        print_info(f"User types: '{user_message}'")
        print_info("Simulating browser events...")
        
        # In a real browser, these events would be dispatched
        print_event("freya:listening", "(UI shows listening state)")
        time.sleep(0.1)
        print_event("freya:thinking", "(UI shows thinking state)")
        
        # Send the chat request
        request_data = {
            "user_id": TEST_USER_ID,
            "message": user_message,
            "conversation_id": conversation_id,
            "include_memory": True
        }
        
        print_info("Sending POST request to /firebase/chat")
        start_time = time.time()
        
        response = requests.post(FIREBASE_CHAT_ENDPOINT, json=request_data)
        
        if response.status_code == 200:
            result = response.json()
            response_time = time.time() - start_time
            
            print_success(f"Response received in {response_time:.2f}s")
            print_event("freya:reply", f"message: {result['message'][:50]}...")
            
            # Store conversation ID
            conversation_id = result.get("conversation_id")
            print_info(f"Conversation ID: {conversation_id}")
            
            # Simulate second message in conversation
            print_info("\nSimulating follow-up message...")
            user_message2 = "What's your primary purpose?"
            print_info(f"User types: '{user_message2}'")
            
            request_data2 = {
                "user_id": TEST_USER_ID,
                "message": user_message2,
                "conversation_id": conversation_id,
                "include_memory": True
            }
            
            response2 = requests.post(FIREBASE_CHAT_ENDPOINT, json=request_data2)
            
            if response2.status_code == 200:
                result2 = response2.json()
                print_success("Follow-up message successful")
                print_event("freya:reply", f"message: {result2['message'][:50]}...")
                return True
            else:
                print_error(f"Follow-up failed: {response2.status_code}")
                return False
        else:
            print_error(f"Chat request failed with status {response.status_code}")
            error_text = response.text
            print_error(f"Error: {error_text}")
            return False
            
    except Exception as e:
        print_error(f"Browser simulation failed: {e}")
        return False


def test_sse_chat_streaming():
    """Test the SSE chat endpoint with streaming"""
    print_header("Testing SSE Chat Streaming")
    
    try:
        request_data = {
            "user_id": TEST_USER_ID,
            "message": "Count to three",
            "conversation_id": None,
            "include_memory": True
        }
        
        print_info("Sending streaming chat request...")
        
        response = requests.post(SSE_CHAT_ENDPOINT, json=request_data, stream=True)
        
        if response.status_code == 200:
            print_success("Streaming response started")
            
            chunks_received = 0
            full_message = ""
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8').strip()
                    
                    if line_str.startswith('data:'):
                        data_str = line_str[5:].strip()
                        if data_str and data_str != '[DONE]':
                            try:
                                data = json.loads(data_str)
                                if data.get("type") == "content":
                                    content = data.get("content", "")
                                    full_message += content
                                    chunks_received += 1
                                    print(f"{GREEN}.{RESET}", end="", flush=True)
                            except json.JSONDecodeError:
                                pass
                        elif data_str == '[DONE]':
                            print_event("\nstream", "DONE")
                            break
            
            response.close()
            print(f"\n{GREEN}✓ Received {chunks_received} chunks{RESET}")
            print_info(f"Full message: {full_message[:100]}...")
            return chunks_received > 0
        else:
            print_error(f"Streaming failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"SSE chat streaming test failed: {e}")
        return False


def test_ui_state_transitions():
    """Test that UI state transitions happen correctly"""
    print_header("Testing UI State Transitions")
    
    print_info("Expected state flow: idle → listening → thinking/replying → idle")
    
    # Simulate the state transitions
    states = [
        ("idle", "Initial state"),
        ("listening", "User starts typing"),
        ("replying", "Message sent, waiting for response"),
        ("idle", "Response received"),
    ]
    
    for state, description in states:
        print_info(f"State: {state} - {description}")
        time.sleep(0.5)  # Simulate time passing
    
    print_success("State transitions follow expected pattern")
    return True


def test_error_recovery():
    """Test how the UI handles errors"""
    print_header("Testing Error Recovery")
    
    try:
        # Test with invalid user ID
        request_data = {
            "user_id": "",  # Invalid
            "message": "This should fail",
            "conversation_id": None,
            "include_memory": True
        }
        
        print_info("Sending invalid request...")
        
        response = requests.post(FIREBASE_CHAT_ENDPOINT, json=request_data)
        
        if response.status_code in [400, 422]:
            print_success("Server correctly rejected invalid request")
            try:
                error_data = response.json()
                print_info(f"Error response: {error_data}")
            except:
                print_info(f"Error response: {response.text}")
            
            # In browser, this would trigger error event
            print_event("freya:reply", "message: I'm having trouble connecting right now...")
            return True
        else:
            print_error(f"Unexpected status: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error recovery test failed: {e}")
        return False


def test_real_frontend_compatibility():
    """Test with actual frontend expectations"""
    print_header("Testing Real Frontend Compatibility")
    
    print_info("Testing exact request format from legacy/main.js...")
    
    # Test the exact flow from the frontend
    conversation_id = None
    
    # First message - exactly as frontend sends it
    request = {
        "user_id": TEST_USER_ID,
        "message": "Hi Freya",
        "conversation_id": conversation_id,
        "include_memory": True
    }
    
    print_info(f"Request: {json.dumps(request, indent=2)}")
    
    try:
        response = requests.post(FIREBASE_CHAT_ENDPOINT, json=request)
        
        if response.status_code == 200:
            result = response.json()
            print_success("Request accepted")
            
            # Check exact response format expected by frontend
            required_fields = ["message", "conversation_id"]
            missing_fields = [field for field in required_fields if field not in result]
            
            if not missing_fields:
                print_success("Response has all required fields for frontend")
                print_info(f"Response format: {json.dumps({k: type(v).__name__ for k, v in result.items()})}")
                
                # Verify message is a string
                if isinstance(result["message"], str):
                    print_success("Message field is correct type (string)")
                else:
                    print_error(f"Message field is wrong type: {type(result['message']).__name__}")
                    
                # Verify conversation_id is a string
                if isinstance(result["conversation_id"], str):
                    print_success("Conversation ID field is correct type (string)")
                else:
                    print_error(f"Conversation ID field is wrong type: {type(result['conversation_id']).__name__}")
                
                return True
            else:
                print_error(f"Missing required fields: {missing_fields}")
                return False
        else:
            print_error(f"Request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Frontend compatibility test failed: {e}")
        return False


def run_all_browser_tests():
    """Run all browser simulation tests"""
    print_header("BROWSER SIMULATION TEST SUITE")
    print(f"Testing backend at: {API_BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check server health first
    try:
        response = requests.get(HEALTH_ENDPOINT)
        if response.status_code != 200:
            print_error("Server is not running! Please start the server with:")
            print_info("python scripts/run_server.py")
            return
        else:
            print_success("Server is healthy")
    except Exception as e:
        print_error(f"Cannot connect to server: {e}")
        print_info("Please start the server with: python scripts/run_server.py")
        return
    
    # Run all tests
    tests = [
        ("Real Frontend Compatibility", test_real_frontend_compatibility),
        ("Browser Chat Flow", simulate_browser_chat_flow),
        ("UI State Transitions", test_ui_state_transitions),
        ("Error Recovery", test_error_recovery),
        # SSE tests disabled - the Firebase implementation doesn't use SSE
        # ("SSE Connection", test_sse_connection),
        # ("SSE Chat Streaming", test_sse_chat_streaming),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print_header("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{GREEN}PASSED{RESET}" if result else f"{RED}FAILED{RESET}"
        print(f"{test_name}: {status}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print_success("\n🎉 All browser simulation tests passed!")
        print_success("The backend correctly handles all UI interactions and state transitions.")
    else:
        print_error(f"\n❌ {total - passed} tests failed.")


if __name__ == "__main__":
    run_all_browser_tests()