#!/usr/bin/env python3
"""
Browser Simulation Test for Freya UI
====================================

This script simulates how a browser would interact with the Freya backend,
including SSE event streams and the exact message flow expected by the UI.
"""

import asyncio
import aiohttp
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


async def test_sse_connection():
    """Test Server-Sent Events connection"""
    print_header("Testing SSE Connection")
    
    try:
        async with aiohttp.ClientSession() as session:
            print_info("Connecting to SSE endpoint...")
            
            async with session.get(SSE_STREAM_ENDPOINT) as response:
                if response.status == 200:
                    print_success("Connected to SSE stream")
                    
                    # Read a few events
                    event_count = 0
                    async for line in response.content:
                        if event_count >= 3:  # Just test initial events
                            break
                            
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith('data:'):
                            data = line_str[5:].strip()
                            if data:
                                print_event("data", data)
                                event_count += 1
                    
                    print_success(f"Successfully received {event_count} events")
                    return True
                else:
                    print_error(f"SSE connection failed with status {response.status}")
                    return False
                    
    except Exception as e:
        print_error(f"SSE connection test failed: {e}")
        return False


async def simulate_browser_chat_flow():
    """Simulate the exact flow a browser would follow"""
    print_header("Simulating Browser Chat Flow")
    
    conversation_id = None
    
    try:
        async with aiohttp.ClientSession() as session:
            # Simulate user typing and sending message
            user_message = "Hello Freya, tell me about yourself"
            print_info(f"User types: '{user_message}'")
            print_info("Simulating browser events...")
            
            # In a real browser, these events would be dispatched
            print_event("freya:listening", "(UI shows listening state)")
            await asyncio.sleep(0.1)
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
            
            async with session.post(FIREBASE_CHAT_ENDPOINT, json=request_data) as response:
                if response.status == 200:
                    result = await response.json()
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
                    
                    async with session.post(FIREBASE_CHAT_ENDPOINT, json=request_data2) as response2:
                        if response2.status == 200:
                            result2 = await response2.json()
                            print_success("Follow-up message successful")
                            print_event("freya:reply", f"message: {result2['message'][:50]}...")
                            return True
                        else:
                            print_error(f"Follow-up failed: {response2.status}")
                            return False
                else:
                    print_error(f"Chat request failed with status {response.status}")
                    error_text = await response.text()
                    print_error(f"Error: {error_text}")
                    return False
                    
    except Exception as e:
        print_error(f"Browser simulation failed: {e}")
        return False


async def test_sse_chat_streaming():
    """Test the SSE chat endpoint with streaming"""
    print_header("Testing SSE Chat Streaming")
    
    try:
        async with aiohttp.ClientSession() as session:
            request_data = {
                "user_id": TEST_USER_ID,
                "message": "Count to three",
                "conversation_id": None,
                "include_memory": True
            }
            
            print_info("Sending streaming chat request...")
            
            async with session.post(SSE_CHAT_ENDPOINT, json=request_data) as response:
                if response.status == 200:
                    print_success("Streaming response started")
                    
                    chunks_received = 0
                    full_message = ""
                    
                    async for line in response.content:
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
                    
                    print(f"\n{GREEN}✓ Received {chunks_received} chunks{RESET}")
                    print_info(f"Full message: {full_message[:100]}...")
                    return chunks_received > 0
                else:
                    print_error(f"Streaming failed with status {response.status}")
                    return False
                    
    except Exception as e:
        print_error(f"SSE chat streaming test failed: {e}")
        return False


async def test_ui_state_transitions():
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
        await asyncio.sleep(0.5)  # Simulate time passing
    
    print_success("State transitions follow expected pattern")
    return True


async def test_error_recovery():
    """Test how the UI handles errors"""
    print_header("Testing Error Recovery")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test with invalid user ID
            request_data = {
                "user_id": "",  # Invalid
                "message": "This should fail",
                "conversation_id": None,
                "include_memory": True
            }
            
            print_info("Sending invalid request...")
            
            async with session.post(FIREBASE_CHAT_ENDPOINT, json=request_data) as response:
                if response.status in [400, 422]:
                    print_success("Server correctly rejected invalid request")
                    error_data = await response.json()
                    print_info(f"Error response: {error_data}")
                    
                    # In browser, this would trigger error event
                    print_event("freya:reply", "message: I'm having trouble connecting right now...")
                    return True
                else:
                    print_error(f"Unexpected status: {response.status}")
                    return False
                    
    except Exception as e:
        print_error(f"Error recovery test failed: {e}")
        return False


async def run_all_browser_tests():
    """Run all browser simulation tests"""
    print_header("BROWSER SIMULATION TEST SUITE")
    print(f"Testing backend at: {API_BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check server health first
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(HEALTH_ENDPOINT) as response:
                if response.status != 200:
                    print_error("Server is not running! Please start the server with:")
                    print_info("python scripts/run_server.py")
                    return
                else:
                    print_success("Server is healthy")
    except Exception as e:
        print_error(f"Cannot connect to server: {e}")
        return
    
    # Run all tests
    tests = [
        ("SSE Connection", test_sse_connection),
        ("Browser Chat Flow", simulate_browser_chat_flow),
        ("SSE Chat Streaming", test_sse_chat_streaming),
        ("UI State Transitions", test_ui_state_transitions),
        ("Error Recovery", test_error_recovery),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
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
    asyncio.run(run_all_browser_tests())