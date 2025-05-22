"""
Simple unit tests for Firebase integration.
Run without pytest dependency.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test results tracking
tests_passed = 0
tests_failed = 0


def test_result(test_name, passed, error=None):
    """Track test results."""
    global tests_passed, tests_failed
    if passed:
        tests_passed += 1
        logger.info(f"✅ {test_name}: PASSED")
    else:
        tests_failed += 1
        logger.error(f"❌ {test_name}: FAILED - {error}")


def test_firebase_service_initialization():
    """Test Firebase service initialization."""
    try:
        from app.services.firebase_service import FirebaseService
        
        # Test that service can be instantiated
        service = FirebaseService()
        assert service is not None, "Service is None"
        
        # Check each attribute individually
        if not hasattr(service, 'db'):
            raise AssertionError("Service missing 'db' attribute")
        if not hasattr(service, 'get_user_facts'):
            raise AssertionError("Service missing 'get_user_facts' method")
        if not hasattr(service, 'add_message'):
            raise AssertionError("Service missing 'add_message' method")
        if not hasattr(service, 'add_document'):
            raise AssertionError("Service missing 'add_document' method")
        
        test_result("Firebase service initialization", True)
    except AssertionError as e:
        test_result("Firebase service initialization", False, f"Assertion failed: {str(e)}")
    except Exception as e:
        test_result("Firebase service initialization", False, f"Exception: {type(e).__name__}: {str(e)}")


def test_memory_query_detection():
    """Test memory query detection logic."""
    try:
        from app.services.firebase_memory_service import FirebaseMemoryService
        
        service = FirebaseMemoryService()
        
        # Test memory queries
        memory_queries = [
            "Do you remember my name?",
            "What did I tell you about my job?",
            "Have we talked about this before?",
            "What did we discuss last time?"
        ]
        
        non_memory_queries = [
            "Hello, how are you?",
            "What's the weather like?",
            "Tell me a joke",
            "How does Python work?"
        ]
        
        # Test memory queries
        for query in memory_queries:
            result = service.is_memory_query(query)
            assert result == True, f"Failed to detect memory query: {query}"
        
        # Test non-memory queries  
        for query in non_memory_queries:
            result = service.is_memory_query(query)
            assert result == False, f"Incorrectly detected as memory query: {query}"
            
        test_result("Memory query detection", True)
    except Exception as e:
        test_result("Memory query detection", False, str(e))


async def test_chat_request_validation():
    """Test chat request model validation."""
    try:
        from app.api.routes.firebase_chat import ChatMessageRequest
        
        # Valid request
        valid_request = ChatMessageRequest(
            message="Hello",
            user_id="test_user",
            include_memory=True
        )
        assert valid_request.message == "Hello"
        assert valid_request.user_id == "test_user"
        assert valid_request.include_memory == True
        
        # Request with defaults
        default_request = ChatMessageRequest(
            message="Hi",
            user_id="user123"
        )
        assert default_request.include_memory == True  # Should default to True
        assert default_request.conversation_id is None  # Should default to None
        
        test_result("Chat request validation", True)
    except Exception as e:
        test_result("Chat request validation", False, str(e))


async def test_chat_response_structure():
    """Test chat response model structure."""
    try:
        from app.api.routes.firebase_chat import ChatMessageResponse
        
        response = ChatMessageResponse(
            message="Hello there!",
            conversation_id="conv123",
            message_id="msg123",
            timestamp="2025-05-22T10:00:00"
        )
        
        # Check response structure
        assert response.message == "Hello there!"
        assert response.conversation_id == "conv123"
        assert response.message_id == "msg123"
        assert response.timestamp == "2025-05-22T10:00:00"
        
        # Check default state flags
        assert response.state_flags["listening"] == False
        assert response.state_flags["thinking"] == False
        assert response.state_flags["reply"] == True
        
        test_result("Chat response structure", True)
    except Exception as e:
        test_result("Chat response structure", False, str(e))


def main():
    """Run all tests."""
    logger.info("Starting Firebase unit tests...")
    
    # Run sync tests
    test_firebase_service_initialization()
    test_memory_query_detection()
    
    # Run async tests
    asyncio.run(test_chat_request_validation())
    asyncio.run(test_chat_response_structure())
    
    # Summary
    logger.info("\n===== TEST SUMMARY =====")
    logger.info(f"Tests passed: {tests_passed}")
    logger.info(f"Tests failed: {tests_failed}")
    logger.info(f"Total tests: {tests_passed + tests_failed}")
    
    if tests_failed == 0:
        logger.info("\n✅ All tests passed!")
        return 0
    else:
        logger.error(f"\n❌ {tests_failed} tests failed!")
        return 1


if __name__ == "__main__":
    exit(main())