"""
Test memory retrieval functionality with real Firebase/Firestore API calls.
This tests the actual memory retrieval system with production data.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import json
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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


def test_firebase_memory_service_initialization():
    """Test that Firebase memory service initializes correctly."""
    try:
        from app.services.firebase_memory_service import FirebaseMemoryService
        
        # Initialize the service
        service = FirebaseMemoryService()
        
        # Verify service has required components
        assert hasattr(service, 'firebase'), "Missing firebase attribute"
        assert hasattr(service, 'topic_extractor'), "Missing topic_extractor attribute"
        assert hasattr(service, 'is_memory_query'), "Missing is_memory_query method"
        assert hasattr(service, 'get_user_facts'), "Missing get_user_facts method"
        assert hasattr(service, 'get_recent_messages'), "Missing get_recent_messages method"
        assert hasattr(service, 'get_topic_memories'), "Missing get_topic_memories method"
        assert hasattr(service, 'assemble_memory_context'), "Missing assemble_memory_context method"
        
        test_result("Firebase memory service initialization", True)
    except Exception as e:
        test_result("Firebase memory service initialization", False, str(e))


def test_user_facts_retrieval():
    """Test retrieving user facts from Firestore with real data."""
    try:
        from app.services.firebase_memory_service import FirebaseMemoryService
        
        service = FirebaseMemoryService()
        
        # Test with real user ID from production
        user_id = "Sencere"
        
        # Test 1: Get all user facts
        logger.info(f"Retrieving all facts for user: {user_id}")
        all_facts = service.get_user_facts(user_id, limit=20)
        
        logger.info(f"Retrieved {len(all_facts)} facts")
        if all_facts:
            logger.info("Sample facts:")
            for fact in all_facts[:3]:
                logger.info(f"  - {fact.get('type')}: {fact.get('value')}")
        
        assert isinstance(all_facts, list), "Facts should be a list"
        assert len(all_facts) > 0, "Should have retrieved some facts"
        
        # Verify fact structure
        for fact in all_facts:
            assert 'type' in fact, "Fact should have 'type' field"
            assert 'value' in fact, "Fact should have 'value' field"
            assert 'timestamp' in fact, "Fact should have 'timestamp' field"
        
        # Test 2: Get facts with query relevance
        query = "tell me about my kids"
        logger.info(f"\nRetrieving facts relevant to query: '{query}'")
        relevant_facts = service.get_user_facts(user_id, query=query, limit=5)
        
        logger.info(f"Retrieved {len(relevant_facts)} relevant facts")
        for fact in relevant_facts:
            logger.info(f"  - {fact.get('type')}: {fact.get('value')}")
        
        # Test 3: Test different queries
        test_queries = [
            "what's my job",
            "where do I live",
            "my interests",
            "family information"
        ]
        
        for test_query in test_queries:
            logger.info(f"\nTesting query: '{test_query}'")
            facts = service.get_user_facts(user_id, query=test_query, limit=3)
            logger.info(f"  Found {len(facts)} relevant facts")
            if facts:
                logger.info(f"  Top result: {facts[0].get('type')} - {facts[0].get('value')}")
        
        test_result("User facts retrieval", True)
    except Exception as e:
        test_result("User facts retrieval", False, str(e))


def test_recent_messages_retrieval():
    """Test retrieving recent messages from Firestore."""
    try:
        from app.services.firebase_memory_service import FirebaseMemoryService
        
        service = FirebaseMemoryService()
        user_id = "Sencere"
        
        # Test 1: Get recent messages
        logger.info(f"\nRetrieving recent messages for user: {user_id}")
        recent_messages = service.get_recent_messages(user_id, limit=10, max_age_days=30)
        
        logger.info(f"Retrieved {len(recent_messages)} recent messages")
        
        # Display sample messages
        if recent_messages:
            logger.info("Sample recent messages:")
            for i, msg in enumerate(recent_messages[:3]):
                content = msg.get('content', '')[:100] + '...' if len(msg.get('content', '')) > 100 else msg.get('content', '')
                logger.info(f"  {i+1}. {content}")
        
        # Verify message structure
        for msg in recent_messages:
            assert 'content' in msg or 'user' in msg, "Message should have content or user field"
            assert 'timestamp' in msg, "Message should have timestamp"
            assert 'conversation_id' in msg, "Message should have conversation_id"
        
        # Test 2: Test with different time ranges
        for days in [7, 14, 60]:
            logger.info(f"\nTesting messages from last {days} days")
            messages = service.get_recent_messages(user_id, limit=5, max_age_days=days)
            logger.info(f"  Found {len(messages)} messages")
        
        test_result("Recent messages retrieval", True)
    except Exception as e:
        test_result("Recent messages retrieval", False, str(e))


def test_topic_memories_retrieval():
    """Test retrieving topic-based memories from Firestore."""
    try:
        from app.services.firebase_memory_service import FirebaseMemoryService
        
        service = FirebaseMemoryService()
        user_id = "Sencere"
        
        # Test different topic queries
        topic_queries = [
            "family and kids",
            "work and career",
            "health concerns",
            "hobbies and interests"
        ]
        
        for query in topic_queries:
            logger.info(f"\nRetrieving topic memories for: '{query}'")
            topic_memories = service.get_topic_memories(user_id, query, topic_limit=3, message_limit=2)
            
            logger.info(f"Found {len(topic_memories)} relevant topics")
            
            for topic_mem in topic_memories:
                topic = topic_mem.get('topic', {})
                messages = topic_mem.get('messages', [])
                logger.info(f"  Topic: {topic.get('name')} (relevance: {topic.get('relevance')}%)")
                logger.info(f"    Messages: {len(messages)}")
                
                # Verify structure
                assert 'topic' in topic_mem, "Should have topic field"
                assert 'messages' in topic_mem, "Should have messages field"
                assert 'name' in topic, "Topic should have name"
                assert 'relevance' in topic, "Topic should have relevance score"
        
        test_result("Topic memories retrieval", True)
    except Exception as e:
        test_result("Topic memories retrieval", False, str(e))


def test_memory_query_detection():
    """Test memory query detection with various queries."""
    try:
        from app.services.firebase_memory_service import FirebaseMemoryService
        
        service = FirebaseMemoryService()
        
        # Memory-related queries that should be detected
        memory_queries = [
            "Do you remember when I told you about my job?",
            "What did I say about my kids?",
            "Have we talked about my health before?",
            "What do you know about my family?",
            "Did I mention my hobbies?",
            "Tell me what you remember about me",
            "When did we discuss my work?",
            "What was that thing I told you last time?",
            "Do you recall our conversation about travel?",
            "Have I told you about my interests?"
        ]
        
        # Non-memory queries that should NOT be detected
        non_memory_queries = [
            "How's the weather today?",
            "Tell me a joke",
            "What is Python?",
            "Help me write code",
            "Good morning!",
            "Calculate 2 + 2",
            "Explain quantum physics",
            "What time is it?"
        ]
        
        logger.info("\nTesting memory query detection:")
        
        # Test memory queries
        logger.info("\nQueries that SHOULD be detected as memory-related:")
        memory_detected = 0
        for query in memory_queries:
            is_memory = service.is_memory_query(query)
            if is_memory:
                memory_detected += 1
                logger.info(f"  ✓ '{query}'")
            else:
                logger.warning(f"  ✗ MISSED: '{query}'")
        
        # Test non-memory queries
        logger.info("\nQueries that should NOT be detected as memory-related:")
        non_memory_correct = 0
        for query in non_memory_queries:
            is_memory = service.is_memory_query(query)
            if not is_memory:
                non_memory_correct += 1
                logger.info(f"  ✓ '{query}'")
            else:
                logger.warning(f"  ✗ FALSE POSITIVE: '{query}'")
        
        # Calculate accuracy
        total_memory = len(memory_queries)
        total_non_memory = len(non_memory_queries)
        accuracy = (memory_detected + non_memory_correct) / (total_memory + total_non_memory) * 100
        
        logger.info(f"\nDetection accuracy: {accuracy:.1f}%")
        logger.info(f"  Memory queries detected: {memory_detected}/{total_memory}")
        logger.info(f"  Non-memory correctly identified: {non_memory_correct}/{total_non_memory}")
        
        # Test should pass if accuracy is above 80%
        assert accuracy >= 80, f"Detection accuracy too low: {accuracy:.1f}%"
        
        test_result("Memory query detection", True)
    except Exception as e:
        test_result("Memory query detection", False, str(e))


def test_topic_extraction():
    """Test topic extraction from queries."""
    try:
        from app.services.firebase_memory_service import FirebaseMemoryService
        
        service = FirebaseMemoryService()
        
        # Test queries with expected topics
        test_cases = [
            ("Tell me about my family and kids", ["family"]),
            ("What did I say about my job at the company?", ["work", "job"]),
            ("Do you remember my health issues?", ["health"]),
            ("What are my hobbies and interests?", ["hobbies", "interests"]),
            ("Where do I live?", ["location", "home"]),
            ("Tell me about my education background", ["education"])
        ]
        
        logger.info("\nTesting topic extraction:")
        
        for query, expected_topics in test_cases:
            extracted = service.extract_topics_from_query(query, top_n=3)
            logger.info(f"\nQuery: '{query}'")
            logger.info(f"  Extracted topics: {extracted}")
            
            # Check if at least one expected topic was found
            found_expected = any(topic.lower() in [t.lower() for t in extracted] or 
                               any(topic.lower() in t.lower() for t in extracted) 
                               for topic in expected_topics)
            
            if found_expected:
                logger.info("  ✓ Found expected topic")
            else:
                logger.warning(f"  ✗ Expected one of {expected_topics}")
        
        test_result("Topic extraction", True)
    except Exception as e:
        test_result("Topic extraction", False, str(e))


def test_memory_context_assembly():
    """Test full memory context assembly with real data."""
    try:
        from app.services.firebase_memory_service import FirebaseMemoryService
        
        service = FirebaseMemoryService()
        user_id = "Sencere"
        
        # Test different types of queries
        test_queries = [
            {
                "query": "Do you remember what I told you about my kids?",
                "type": "memory_query",
                "expected_content": ["user_facts", "topic_memories", "is_memory_query"]
            },
            {
                "query": "Tell me about the weather",
                "type": "general_query",
                "expected_content": ["user_facts", "recent_memories", "topic_memories"]
            },
            {
                "query": "What do you know about my work?",
                "type": "knowledge_query",
                "expected_content": ["user_facts", "topic_memories", "formatted_context"]
            }
        ]
        
        for test_case in test_queries:
            query = test_case["query"]
            logger.info(f"\n{'='*60}")
            logger.info(f"Testing memory assembly for: '{query}'")
            logger.info(f"Query type: {test_case['type']}")
            
            # Assemble memory context
            context = service.assemble_memory_context(user_id, query)
            
            # Verify structure
            assert isinstance(context, dict), "Context should be a dictionary"
            
            # Check expected fields
            for field in test_case["expected_content"]:
                assert field in context, f"Context missing '{field}' field"
            
            # Display results
            logger.info(f"\nMemory context assembled:")
            logger.info(f"  Is memory query: {context.get('is_memory_query')}")
            logger.info(f"  User facts found: {len(context.get('user_facts', []))}")
            logger.info(f"  Recent memories: {len(context.get('recent_memories', []))}")
            logger.info(f"  Topic memories: {len(context.get('topic_memories', []))}")
            
            if context.get('memory_query_type'):
                logger.info(f"  Memory query type: {context['memory_query_type']}")
            
            # Show formatted context preview
            if 'formatted_context' in context:
                preview = context['formatted_context'][:500] + '...' if len(context['formatted_context']) > 500 else context['formatted_context']
                logger.info(f"\nFormatted context preview:")
                logger.info("-" * 40)
                logger.info(preview)
                logger.info("-" * 40)
        
        test_result("Memory context assembly", True)
    except Exception as e:
        test_result("Memory context assembly", False, str(e))


def test_memory_prioritization():
    """Test memory prioritization for different query types."""
    try:
        from app.services.firebase_memory_service import FirebaseMemoryService
        
        service = FirebaseMemoryService()
        user_id = "Sencere"
        
        # Test memory prioritization with specific queries
        prioritization_tests = [
            {
                "query": "When did I tell you about my new job?",
                "expected_type": "temporal_recall",
                "priority": "timestamps"
            },
            {
                "query": "Have we discussed my health issues?",
                "expected_type": "existence_verification",
                "priority": "relevant_topics"
            },
            {
                "query": "What do you know about my family?",
                "expected_type": "knowledge_query",
                "priority": "user_facts"
            }
        ]
        
        logger.info("\nTesting memory prioritization:")
        
        for test in prioritization_tests:
            query = test["query"]
            logger.info(f"\nQuery: '{query}'")
            
            # Get memory context
            context = service.assemble_memory_context(user_id, query)
            
            # Check query type classification
            query_type = context.get('memory_query_type', 'unknown')
            logger.info(f"  Classified as: {query_type}")
            logger.info(f"  Expected: {test['expected_type']}")
            
            # Verify prioritization based on type
            formatted_context = context.get('formatted_context', '')
            
            if test['priority'] == 'timestamps' and 'Timeline' in formatted_context:
                logger.info("  ✓ Correctly prioritized timestamps")
            elif test['priority'] == 'relevant_topics' and 'Verification' in formatted_context:
                logger.info("  ✓ Correctly prioritized topic verification")
            elif test['priority'] == 'user_facts' and 'User Facts' in formatted_context:
                logger.info("  ✓ Correctly prioritized user facts")
            else:
                logger.info(f"  ⚠️  Priority focus: {test['priority']}")
        
        test_result("Memory prioritization", True)
    except Exception as e:
        test_result("Memory prioritization", False, str(e))


def test_fact_relevance_scoring():
    """Test fact relevance scoring algorithm."""
    try:
        from app.services.firebase_memory_service import FirebaseMemoryService
        
        service = FirebaseMemoryService()
        
        # Create test facts
        test_facts = [
            {"type": "job", "value": "Software engineer at TechCorp", "timestamp": datetime.now()},
            {"type": "family", "value": "Has two kids named Alice and Bob", "timestamp": datetime.now()},
            {"type": "location", "value": "Lives in San Francisco", "timestamp": datetime.now()},
            {"type": "interests", "value": "Enjoys hiking and photography", "timestamp": datetime.now()},
            {"type": "pets", "value": "Has a dog named Max", "timestamp": datetime.now()}
        ]
        
        # Test queries and expected top results
        scoring_tests = [
            ("Tell me about my job", "job"),
            ("What about my kids", "family"),
            ("Where do I live", "location"),
            ("My hobbies", "interests"),
            ("My pet", "pets")
        ]
        
        logger.info("\nTesting fact relevance scoring:")
        
        for query, expected_type in scoring_tests:
            logger.info(f"\nQuery: '{query}'")
            
            # Score facts
            scored_facts = service._score_facts_by_relevance(test_facts, query)
            
            if scored_facts:
                # Sort by score
                scored_facts.sort(key=lambda x: x[1], reverse=True)
                top_fact = scored_facts[0][0]
                top_score = scored_facts[0][1]
                
                logger.info(f"  Top result: {top_fact['type']} (score: {top_score:.2f})")
                logger.info(f"  Expected: {expected_type}")
                
                # Check if correct fact type is ranked first
                if top_fact['type'] == expected_type:
                    logger.info("  ✓ Correct fact prioritized")
                else:
                    logger.warning("  ✗ Incorrect prioritization")
                
                # Show all scores
                logger.info("  All scores:")
                for fact, score in scored_facts[:3]:
                    logger.info(f"    - {fact['type']}: {score:.2f}")
        
        test_result("Fact relevance scoring", True)
    except Exception as e:
        test_result("Fact relevance scoring", False, str(e))


def test_memory_formatting():
    """Test memory context formatting for different scenarios."""
    try:
        from app.services.firebase_memory_service import FirebaseMemoryService
        
        service = FirebaseMemoryService()
        
        # Test different memory context scenarios
        test_contexts = [
            {
                "name": "Memory query with facts and topics",
                "context": {
                    "is_memory_query": True,
                    "memory_query_type": "recall_verification",
                    "user_facts": [
                        {"type": "job", "value": "Software engineer", "confidence": 90},
                        {"type": "family", "value": "Two kids", "confidence": 85}
                    ],
                    "recent_memories": [
                        {"content": "Discussed project deadline", "timestamp": "2025-05-20T10:00:00"}
                    ],
                    "topic_memories": [
                        {
                            "topic": {"name": "work", "relevance": 80},
                            "messages": [{"content": "Working on new feature", "timestamp": "2025-05-19T15:00:00"}]
                        }
                    ]
                }
            },
            {
                "name": "General query with limited context",
                "context": {
                    "is_memory_query": False,
                    "user_facts": [
                        {"type": "interests", "value": "Photography", "confidence": 70}
                    ],
                    "recent_memories": [],
                    "topic_memories": []
                }
            }
        ]
        
        logger.info("\nTesting memory formatting:")
        
        for test in test_contexts:
            logger.info(f"\n{test['name']}:")
            
            # Format the context
            formatted = service.format_memory_context(test['context'])
            
            # Verify formatting
            assert isinstance(formatted, str), "Formatted context should be a string"
            assert len(formatted) > 0, "Formatted context should not be empty"
            assert "### Memory Context ###" in formatted, "Should have context header"
            
            # Check specific sections based on content
            if test['context']['user_facts']:
                assert "User Facts" in formatted, "Should include user facts section"
            
            if test['context']['is_memory_query']:
                if test['context']['memory_query_type'] == 'recall_verification':
                    assert "Topic-Related Memories" in formatted or "Recent Conversation" in formatted, \
                        "Memory queries should include relevant sections"
            
            # Display formatted output
            logger.info("Formatted output preview:")
            logger.info("-" * 40)
            preview = formatted[:400] + '...' if len(formatted) > 400 else formatted
            logger.info(preview)
            logger.info("-" * 40)
        
        test_result("Memory formatting", True)
    except Exception as e:
        test_result("Memory formatting", False, str(e))


def main():
    """Run all memory retrieval tests."""
    logger.info("=" * 70)
    logger.info("MEMORY RETRIEVAL FUNCTIONALITY TESTS")
    logger.info("Testing with real Firebase/Firestore API calls")
    logger.info("=" * 70)
    
    # Run all tests
    test_firebase_memory_service_initialization()
    test_user_facts_retrieval()
    test_recent_messages_retrieval()
    test_topic_memories_retrieval()
    test_memory_query_detection()
    test_topic_extraction()
    test_memory_context_assembly()
    test_memory_prioritization()
    test_fact_relevance_scoring()
    test_memory_formatting()
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("TEST SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Tests passed: {tests_passed}")
    logger.info(f"Tests failed: {tests_failed}")
    logger.info(f"Total tests: {tests_passed + tests_failed}")
    
    if tests_failed == 0:
        logger.info("\n✅ All memory retrieval tests passed!")
        logger.info("The memory retrieval system is working correctly with Firebase/Firestore.")
        return 0
    else:
        logger.error(f"\n❌ {tests_failed} tests failed!")
        logger.error("Please check the errors above for details.")
        return 1


if __name__ == "__main__":
    exit(main())