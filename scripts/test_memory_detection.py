"""
test_memory_detection.py - Simple test script for memory query detection

This script tests the memory query detection functionality without requiring database access.
"""

import sys
from pathlib import Path
import os

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.memory_context_service import MemoryContextBuilder
from app.services.topic_extraction import TopicExtractor

# Test queries for memory detection
MEMORY_QUERIES = [
    "Do you remember what I told you about my job?",
    "What did I say about my family?",
    "Have we talked about my health before?",
    "Recall our conversation about movies.",
    "What do you know about my hobbies?",
    "Last time we discussed my vacation plans.",
    "Didn't I tell you about my new car?",
    "Am I right that we talked about my sister?"
]

# Non-memory queries
NON_MEMORY_QUERIES = [
    "What's the weather like today?",
    "Tell me a joke.",
    "How are you doing?",
    "What's your name?",
    "Can you help me with my homework?",
    "What time is it?",
    "I'm feeling sad today.",
    "Do you like pizza?"
]

# Topic-specific queries
TOPIC_QUERIES = [
    "Tell me about my family and my job.",
    "What do you know about my health and exercise routine?",
    "I'm interested in movies, books, and music.",
    "My education at university was challenging.",
    "I live in a house in the city with my family."
]


class MockSession:
    """Mock database session for testing without database access."""
    def __init__(self):
        pass
    
    def query(self, *args, **kwargs):
        return self
    
    def filter(self, *args, **kwargs):
        return self
    
    def all(self):
        return []
    
    def first(self):
        return None


def test_memory_query_detection():
    """Test memory query detection."""
    print("\n=== Testing Memory Query Detection ===")
    
    # Create a builder with a mock session
    builder = MemoryContextBuilder(MockSession())
    
    # Mock the dependencies to avoid DB calls
    builder.memory_repo = None
    builder.conversation_history_service = None
    builder.topic_memory_service = None
    
    # Keep the topic extractor for topic extraction testing
    builder.topic_extractor = TopicExtractor()
    
    print("\nMemory Queries:")
    for query in MEMORY_QUERIES:
        result = builder.is_memory_query(query)
        print(f"  '{query}' -> {'✓' if result else '✗'}")
        assert result, f"Failed to detect memory query: '{query}'"
    
    print("\nNon-Memory Queries:")
    for query in NON_MEMORY_QUERIES:
        result = builder.is_memory_query(query)
        print(f"  '{query}' -> {'✗' if not result else '✓'}")
        assert not result, f"Incorrectly detected as memory query: '{query}'"
    
    print("\nMemory query detection test passed.")


def test_topic_extraction():
    """Test topic extraction from queries."""
    print("\n=== Testing Topic Extraction ===")
    
    # Create a builder with a mock session
    builder = MemoryContextBuilder(MockSession())
    
    # Mock the dependencies to avoid DB calls
    builder.memory_repo = None
    builder.conversation_history_service = None
    builder.topic_memory_service = None
    
    # Keep the topic extractor for topic extraction testing
    builder.topic_extractor = TopicExtractor()
    
    for query in TOPIC_QUERIES:
        topics = builder.extract_topics_from_query(query, top_n=5)
        print(f"\nQuery: '{query}'")
        print(f"Extracted topics: {topics}")
        assert topics, f"No topics extracted from query: '{query}'"
    
    print("\nTopic extraction test passed.")


def main():
    """Main function to run the test script."""
    print("=== Memory Context Builder Tests (No Database) ===")
    
    # Run tests
    test_memory_query_detection()
    test_topic_extraction()
    
    print("\nAll tests passed!")


if __name__ == "__main__":
    main()
