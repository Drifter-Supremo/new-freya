"""
test_firebase_chat.py - Test script for simplified Firebase chat API

This script tests the simplified chat API that uses Firebase/Firestore
for data storage and retrieves memory context.
"""

import os
import sys
import json
import requests
import time
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Base URL for the API
BASE_URL = "http://localhost:8000/firebase"

# Use your actual user ID from Firestore
ACTUAL_USER_ID = "Sencere"

def test_chat_endpoint():
    """Test the /firebase/chat endpoint."""
    logger.info("Testing chat endpoint...")
    
    # Use your actual user ID
    user_id = ACTUAL_USER_ID
    
    # Test initial message
    message = "Hi, tell me about yourself. What do you remember about me?"
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": message,
            "user_id": user_id,
            "include_memory": True
        }
    )
    
    if response.status_code != 200:
        logger.error(f"Chat endpoint failed: {response.text}")
        return False
    
    result = response.json()
    conversation_id = result.get("conversation_id")
    logger.info(f"Conversation created: {conversation_id}")
    logger.info(f"Response: {result.get('message')}")
    
    # Test follow-up message with same conversation
    message = "What do you know about me?"
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": message,
            "user_id": user_id,
            "conversation_id": conversation_id,
            "include_memory": True
        }
    )
    
    if response.status_code != 200:
        logger.error(f"Follow-up message failed: {response.text}")
        return False
    
    result = response.json()
    logger.info(f"Response: {result.get('message')}")
    
    # Test memory-based question
    message = "Do you remember where I live?"
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": message,
            "user_id": user_id,
            "conversation_id": conversation_id,
            "include_memory": True
        }
    )
    
    if response.status_code != 200:
        logger.error(f"Memory question failed: {response.text}")
        return False
    
    result = response.json()
    logger.info(f"Response: {result.get('message')}")
    
    # Test getting conversations
    response = requests.get(f"{BASE_URL}/conversations/{user_id}")
    if response.status_code != 200:
        logger.error(f"Get conversations failed: {response.text}")
        return False
    
    conversations = response.json().get("conversations", [])
    logger.info(f"Found {len(conversations)} conversations")
    for conv in conversations[:2]:  # Show first 2 conversations
        logger.info(f"Conversation: {conv.get('id', 'N/A')} - Created: {conv.get('createdAt', 'N/A')}")
    
    # Test getting messages
    response = requests.get(f"{BASE_URL}/conversations/{conversation_id}/messages")
    if response.status_code != 200:
        logger.error(f"Get messages failed: {response.text}")
        return False
    
    messages = response.json().get("messages", [])
    logger.info(f"Found {len(messages)} messages")
    for msg in messages[:3]:  # Show first 3 messages
        logger.info(f"Message: {msg.get('user', 'N/A')[:50]}... - Time: {msg.get('timestamp', 'N/A')}")
    
    # Success
    logger.info("Chat endpoint tests passed!")
    return True

def test_user_facts():
    """Test the user facts endpoints."""
    logger.info("Testing user facts...")
    
    # Use your actual user ID
    user_id = ACTUAL_USER_ID
    
    logger.info(f"Testing user facts for user: {user_id}")
    
    # Get existing user facts from your Firestore
    response = requests.get(f"{BASE_URL}/facts/{user_id}")
    if response.status_code != 200:
        logger.error(f"Get facts failed: {response.text}")
        return False
    
    facts = response.json().get("facts", [])
    logger.info(f"Found {len(facts)} existing facts")
    for fact in facts[:5]:  # Show first 5 facts
        logger.info(f"Fact: {fact.get('type', 'N/A')} - {fact.get('value', 'N/A')} - Time: {fact.get('timestamp', 'N/A')}")
    
    # Test with a message that might generate facts (optional)
    message = "Just wanted to test if you can remember new information about me."
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": message,
            "user_id": user_id,
            "include_memory": True
        }
    )
    
    if response.status_code != 200:
        logger.error(f"Chat with facts failed: {response.text}")
        return False
    
    result = response.json()
    logger.info(f"Conversation created with facts")
    
    # Get user facts
    response = requests.get(f"{BASE_URL}/facts/{user_id}")
    if response.status_code != 200:
        logger.error(f"Get facts failed: {response.text}")
        return False
    
    facts = response.json().get("facts", [])
    logger.info(f"Found {len(facts)} facts")
    for fact in facts:
        logger.info(f"Fact: {fact.get('type')} - {fact.get('value')}")
    
    # Success
    logger.info("User facts tests passed!")
    return True

def test_topics():
    """Test the topics endpoints."""
    logger.info("Testing topics...")
    
    # Create a test user ID
    user_id = f"test_user_{int(time.time())}"
    
    # First, send messages to create topics
    messages = [
        "I love hiking in the mountains every weekend.",
        "My favorite programming language is Python.",
        "I've been thinking about buying a new car."
    ]
    
    conversation_id = None
    for message in messages:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={
                "message": message,
                "user_id": user_id,
                "conversation_id": conversation_id,
                "include_memory": True
            }
        )
        
        if response.status_code != 200:
            logger.error(f"Chat for topics failed: {response.text}")
            return False
        
        result = response.json()
        if not conversation_id:
            conversation_id = result.get("conversation_id")
    
    logger.info(f"Conversation created with topics")
    
    # Get topics
    response = requests.get(f"{BASE_URL}/topics/{user_id}")
    if response.status_code != 200:
        logger.error(f"Get topics failed: {response.text}")
        return False
    
    topics = response.json().get("topics", [])
    logger.info(f"Found {len(topics)} topics")
    for topic in topics:
        logger.info(f"Topic: {topic.get('name')}")
    
    # Test memory recall with topics
    memory_message = "Do you remember what I said about hiking?"
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": memory_message,
            "user_id": user_id,
            "conversation_id": conversation_id,
            "include_memory": True
        }
    )
    
    if response.status_code != 200:
        logger.error(f"Topic recall failed: {response.text}")
        return False
    
    result = response.json()
    logger.info(f"Topic recall response: {result.get('message')}")
    
    # Success
    logger.info("Topics tests passed!")
    return True

def test_delete_conversation():
    """Test deleting a conversation."""
    logger.info("Testing conversation deletion...")
    
    # Create a test user ID
    user_id = f"test_user_{int(time.time())}"
    
    # Create a conversation
    message = "This is a test conversation that will be deleted."
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": message,
            "user_id": user_id,
            "include_memory": True
        }
    )
    
    if response.status_code != 200:
        logger.error(f"Create conversation failed: {response.text}")
        return False
    
    result = response.json()
    conversation_id = result.get("conversation_id")
    logger.info(f"Conversation created: {conversation_id}")
    
    # Delete the conversation
    response = requests.delete(f"{BASE_URL}/conversations/{conversation_id}")
    if response.status_code != 200:
        logger.error(f"Delete conversation failed: {response.text}")
        return False
    
    logger.info(f"Conversation deleted: {conversation_id}")
    
    # Try to get messages from deleted conversation
    response = requests.get(f"{BASE_URL}/conversations/{conversation_id}/messages")
    if response.status_code == 404:
        logger.info("Correctly got 404 for deleted conversation")
    else:
        logger.error(f"Expected 404, got {response.status_code}: {response.text}")
        return False
    
    # Success
    logger.info("Conversation deletion test passed!")
    return True

def run_all_tests():
    """Run all tests and report results."""
    logger.info("Starting Firebase chat API tests...")
    
    tests = [
        test_chat_endpoint,
        test_user_facts,
        test_topics,
        test_delete_conversation
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            logger.error(f"Test {test.__name__} failed with exception: {str(e)}")
            results.append((test.__name__, False))
    
    # Report results
    logger.info("\n===== TEST RESULTS =====")
    all_passed = True
    for name, result in results:
        status = "PASSED" if result else "FAILED"
        logger.info(f"{name}: {status}")
        if not result:
            all_passed = False
    
    logger.info(f"\nOverall test result: {'PASSED' if all_passed else 'FAILED'}")
    return all_passed

if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Tests failed with exception: {str(e)}")
        sys.exit(1)