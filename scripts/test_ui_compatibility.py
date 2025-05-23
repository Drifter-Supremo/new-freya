#!/usr/bin/env python3
"""
Test UI Compatibility with Backend API
=====================================

This script tests the backend API to ensure full compatibility with the existing React UI.
It simulates real user interactions and verifies all expected behaviors.
"""

import asyncio
import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

# API Configuration
API_BASE_URL = "http://localhost:8000"
FIREBASE_CHAT_ENDPOINT = f"{API_BASE_URL}/firebase/chat"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"

# Test Configuration
TEST_USER_ID = "test_user_123"

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
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


def check_health():
    """Check if the server is healthy"""
    try:
        response = requests.get(HEALTH_ENDPOINT)
        if response.status_code == 200:
            print_success("Server is healthy")
            return True
        else:
            print_error(f"Server health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Cannot connect to server: {e}")
        return False


def test_chat_request_format(conversation_id: Optional[str] = None) -> Dict[str, Any]:
    """Test that the API accepts the exact format expected by the UI"""
    print_header("Testing Chat Request Format")
    
    # Exact format from legacy/main.js
    request_data = {
        "user_id": TEST_USER_ID,
        "message": "Hello Freya, how are you today?",
        "conversation_id": conversation_id,
        "include_memory": True
    }
    
    print_info(f"Sending request: {json.dumps(request_data, indent=2)}")
    
    try:
        response = requests.post(FIREBASE_CHAT_ENDPOINT, json=request_data)
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Request accepted with status {response.status_code}")
            print_info(f"Response: {json.dumps(result, indent=2)}")
            
            # Verify response format matches UI expectations
            if "message" in result and "conversation_id" in result:
                print_success("Response format matches UI expectations")
                return result
            else:
                print_error("Response missing required fields for UI")
                return {}
        else:
            print_error(f"Request failed with status {response.status_code}")
            print_error(f"Response: {response.text}")
            return {}
            
    except Exception as e:
        print_error(f"Request failed: {e}")
        return {}


def test_conversation_continuity():
    """Test that conversation IDs are maintained across messages"""
    print_header("Testing Conversation Continuity")
    
    # First message - no conversation ID
    print_info("Sending first message (new conversation)")
    result1 = test_chat_request_format(conversation_id=None)
    
    if not result1 or "conversation_id" not in result1:
        print_error("Failed to get conversation ID from first message")
        return False
    
    conversation_id = result1["conversation_id"]
    print_success(f"Got conversation ID: {conversation_id}")
    
    # Second message - with conversation ID
    print_info("Sending second message (continuing conversation)")
    request_data = {
        "user_id": TEST_USER_ID,
        "message": "Do you remember what I just said?",
        "conversation_id": conversation_id,
        "include_memory": True
    }
    
    try:
        response = requests.post(FIREBASE_CHAT_ENDPOINT, json=request_data)
        result2 = response.json()
        
        if result2.get("conversation_id") == conversation_id:
            print_success("Conversation ID maintained across messages")
            print_info(f"Freya's response: {result2.get('message', '')[:100]}...")
            return True
        else:
            print_error("Conversation ID changed unexpectedly")
            return False
            
    except Exception as e:
        print_error(f"Second message failed: {e}")
        return False


def test_memory_inclusion():
    """Test that memory context is included when requested"""
    print_header("Testing Memory Inclusion")
    
    # Test with memory included
    print_info("Testing with include_memory=True")
    request_data = {
        "user_id": TEST_USER_ID,
        "message": "What do you remember about me?",
        "conversation_id": None,
        "include_memory": True
    }
    
    try:
        response = requests.post(FIREBASE_CHAT_ENDPOINT, json=request_data)
        result = response.json()
        
        if response.status_code == 200:
            print_success("Memory request processed successfully")
            print_info(f"Response: {result.get('message', '')[:150]}...")
            
            # Test without memory
            print_info("\nTesting with include_memory=False")
            request_data["include_memory"] = False
            response2 = requests.post(FIREBASE_CHAT_ENDPOINT, json=request_data)
            result2 = response2.json()
            
            if response2.status_code == 200:
                print_success("Non-memory request processed successfully")
                print_info(f"Response: {result2.get('message', '')[:150]}...")
                return True
                
        return False
        
    except Exception as e:
        print_error(f"Memory test failed: {e}")
        return False


def test_error_handling():
    """Test that errors are handled gracefully"""
    print_header("Testing Error Handling")
    
    # Test missing required fields
    test_cases = [
        {"name": "Missing user_id", "data": {"message": "Hello", "include_memory": True}},
        {"name": "Missing message", "data": {"user_id": TEST_USER_ID, "include_memory": True}},
        {"name": "Empty message", "data": {"user_id": TEST_USER_ID, "message": "", "include_memory": True}},
    ]
    
    all_passed = True
    
    for test in test_cases:
        print_info(f"Testing: {test['name']}")
        try:
            response = requests.post(FIREBASE_CHAT_ENDPOINT, json=test["data"])
            if response.status_code in [400, 422]:
                print_success(f"Correctly rejected invalid request with status {response.status_code}")
            else:
                print_error(f"Unexpected status code: {response.status_code}")
                all_passed = False
        except Exception as e:
            print_error(f"Test failed: {e}")
            all_passed = False
    
    return all_passed


def test_response_timing():
    """Test response timing to ensure UI state transitions work correctly"""
    print_header("Testing Response Timing")
    
    request_data = {
        "user_id": TEST_USER_ID,
        "message": "Count to three slowly",
        "conversation_id": None,
        "include_memory": True
    }
    
    print_info("Measuring response time...")
    start_time = time.time()
    
    try:
        response = requests.post(FIREBASE_CHAT_ENDPOINT, json=request_data)
        end_time = time.time()
        response_time = end_time - start_time
        
        if response.status_code == 200:
            print_success(f"Response received in {response_time:.2f} seconds")
            
            # UI expects reasonable response times
            if response_time < 30:  # 30 seconds is reasonable for OpenAI
                print_success("Response time is within acceptable range for UI")
                return True
            else:
                print_error("Response time too slow for good UI experience")
                return False
        else:
            print_error(f"Request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Timing test failed: {e}")
        return False


def test_freya_personality():
    """Test that Freya's personality comes through in responses"""
    print_header("Testing Freya's Personality")
    
    personality_prompts = [
        "Tell me a joke",
        "How do you feel about being an AI?",
        "What happened on Saturn?",
    ]
    
    all_passed = True
    
    for prompt in personality_prompts:
        print_info(f"Testing prompt: '{prompt}'")
        request_data = {
            "user_id": TEST_USER_ID,
            "message": prompt,
            "conversation_id": None,
            "include_memory": True
        }
        
        try:
            response = requests.post(FIREBASE_CHAT_ENDPOINT, json=request_data)
            if response.status_code == 200:
                result = response.json()
                message = result.get("message", "")
                print_success(f"Got response: {message[:100]}...")
                
                # Check for Freya's personality markers
                # She should be brief, warm, and avoid quotes/asterisks
                if '"' in message or '*' in message:
                    print_error("Response contains quotes or asterisks (against Freya's rules)")
                    all_passed = False
                elif len(message) > 500:
                    print_error("Response too verbose (Freya should be brief)")
                    all_passed = False
                else:
                    print_success("Response follows Freya's personality guidelines")
            else:
                print_error(f"Request failed with status {response.status_code}")
                all_passed = False
                
        except Exception as e:
            print_error(f"Personality test failed: {e}")
            all_passed = False
    
    return all_passed


def run_all_tests():
    """Run all UI compatibility tests"""
    print_header("UI COMPATIBILITY TEST SUITE")
    print(f"Testing backend at: {API_BASE_URL}")
    print(f"User ID: {TEST_USER_ID}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check server health first
    if not check_health():
        print_error("\nServer is not running! Please start the server with:")
        print_info("python scripts/run_server.py")
        return
    
    # Run all tests
    tests = [
        ("Chat Request Format", lambda: bool(test_chat_request_format())),
        ("Conversation Continuity", test_conversation_continuity),
        ("Memory Inclusion", test_memory_inclusion),
        ("Error Handling", test_error_handling),
        ("Response Timing", test_response_timing),
        ("Freya Personality", test_freya_personality),
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
        print_success("\n🎉 All UI compatibility tests passed! The backend is fully compatible with the frontend.")
    else:
        print_error(f"\n❌ {total - passed} tests failed. Please fix the issues before deployment.")


if __name__ == "__main__":
    run_all_tests()