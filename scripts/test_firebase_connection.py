"""
test_firebase_connection.py - Simple test to verify Firebase connectivity

This script tests basic Firebase connection and data retrieval using your actual Firestore data.
"""

import os
import sys
import logging

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.firebase_service import FirebaseService
from app.services.firebase_memory_service import FirebaseMemoryService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Your actual user ID
USER_ID = "Sencere"
# Your actual conversation ID
CONVERSATION_ID = "1QVkHoKe6QqLTlJQFAFE"

def test_firebase_connection():
    """Test basic Firebase connection"""
    logger.info("=== Testing Firebase Connection ===")
    
    try:
        firebase = FirebaseService()
        logger.info("✅ Firebase service initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize Firebase service: {str(e)}")
        return False

def test_user_facts_retrieval():
    """Test retrieval of user facts"""
    logger.info("=== Testing User Facts Retrieval ===")
    
    try:
        firebase = FirebaseService()
        
        # Get user facts
        facts = firebase.get_user_facts(USER_ID)
        logger.info(f"✅ Retrieved {len(facts)} user facts")
        
        # Show first few facts
        for i, fact in enumerate(facts[:5]):
            logger.info(f"  Fact {i+1}: {fact.get('type', 'N/A')} - {fact.get('value', 'N/A')}")
            logger.info(f"           Timestamp: {fact.get('timestamp', 'N/A')}")
            logger.info(f"           ID: {fact.get('id', 'N/A')}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to retrieve user facts: {str(e)}")
        return False

def test_conversations_retrieval():
    """Test retrieval of conversations"""
    logger.info("=== Testing Conversations Retrieval ===")
    
    try:
        firebase = FirebaseService()
        
        # Get conversations for user
        conversations = firebase.get_user_conversations(USER_ID, limit=5)
        logger.info(f"✅ Retrieved {len(conversations)} conversations")
        
        # Show conversation details
        for i, conv in enumerate(conversations[:3]):
            logger.info(f"  Conversation {i+1}: {conv.get('id', 'N/A')}")
            logger.info(f"                   Created: {conv.get('createdAt', 'N/A')}")
            logger.info(f"                   User ID: {conv.get('userId', 'N/A')}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to retrieve conversations: {str(e)}")
        return False

def test_messages_retrieval():
    """Test retrieval of messages"""
    logger.info("=== Testing Messages Retrieval ===")
    
    try:
        firebase = FirebaseService()
        
        # Get messages
        messages = firebase.get_conversation_messages(CONVERSATION_ID, limit=5)
        logger.info(f"✅ Retrieved {len(messages)} messages")
        
        # Show message details
        for i, msg in enumerate(messages[:3]):
            user_content = msg.get('user', 'N/A')
            # Truncate long messages for display
            if len(user_content) > 100:
                user_content = user_content[:100] + "..."
            logger.info(f"  Message {i+1}: {user_content}")
            logger.info(f"              Timestamp: {msg.get('timestamp', 'N/A')}")
            logger.info(f"              ID: {msg.get('id', 'N/A')}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to retrieve messages: {str(e)}")
        return False

def test_memory_service():
    """Test the Firebase memory service"""
    logger.info("=== Testing Firebase Memory Service ===")
    
    try:
        memory_service = FirebaseMemoryService()
        
        # Test memory context assembly
        test_queries = [
            "What do you remember about me?",
            "Tell me about my interests",
            "Do you know anything about my preferences?"
        ]
        
        for query in test_queries:
            logger.info(f"Testing query: '{query}'")
            
            # Check if it's detected as a memory query
            is_memory = memory_service.is_memory_query(query)
            logger.info(f"  Is memory query: {is_memory}")
            
            # Get user facts relevant to the query
            facts = memory_service.get_user_facts(USER_ID, query, limit=3)
            logger.info(f"  Relevant facts: {len(facts)}")
            
            for fact in facts[:2]:
                logger.info(f"    - {fact.get('type', 'N/A')}: {fact.get('value', 'N/A')}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to test memory service: {str(e)}")
        return False

def main():
    """Run all tests"""
    logger.info("Starting Firebase connection tests...")
    logger.info(f"Testing with User ID: {USER_ID}")
    logger.info(f"Testing with Conversation ID: {CONVERSATION_ID}")
    logger.info("=" * 60)
    
    tests = [
        test_firebase_connection,
        test_user_facts_retrieval,
        test_conversations_retrieval,
        test_messages_retrieval,
        test_memory_service
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
            logger.info("")  # Add spacing between tests
        except Exception as e:
            logger.error(f"Test {test.__name__} failed with exception: {str(e)}")
            results.append((test.__name__, False))
    
    # Report results
    logger.info("=" * 60)
    logger.info("=== TEST RESULTS ===")
    all_passed = True
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{name}: {status}")
        if not result:
            all_passed = False
    
    logger.info("=" * 60)
    logger.info(f"Overall result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Tests failed with exception: {str(e)}")
        sys.exit(1)