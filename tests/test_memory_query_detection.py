"""
test_memory_query_detection.py - Tests for memory query detection functionality
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.memory_context_service import MemoryContextBuilder


class TestMemoryQueryDetection:
    """Test suite for memory query detection functionality."""

    @pytest.fixture
    def memory_builder(self):
        """Create a MemoryContextBuilder with mocked dependencies."""
        # Create mock session
        mock_db = MagicMock()
        
        # Create the builder with mocked session
        builder = MemoryContextBuilder(mock_db)
        
        # Mock the dependencies to avoid DB calls
        builder.memory_repo = MagicMock()
        builder.conversation_history_service = MagicMock()
        builder.topic_memory_service = MagicMock()
        builder.topic_extractor = MagicMock()
        
        return builder

    def test_direct_memory_questions(self, memory_builder):
        """Test detection of direct memory questions."""
        # Test various direct memory questions
        memory_queries = [
            "Do you remember what I told you about my job?",
            "Do you remember when we talked about my family?",
            "What did I tell you about my hobby?",
            "What did we discuss yesterday?",
            "When did I mention my sister?",
            "Have we talked about my new project?",
            "Tell me what I said about my vacation plans.",
            "Remind me what we discussed about my health."
        ]
        
        for query in memory_queries:
            assert memory_builder.is_memory_query(query), f"Failed to detect memory query: '{query}'"

    def test_recall_requests(self, memory_builder):
        """Test detection of recall requests."""
        # Test various recall requests
        recall_queries = [
            "Remember our conversation about movies?",
            "Recall what I told you about my job interview.",
            "Can you recollect when I mentioned my dog?",
            "Bring up what we discussed about my vacation.",
            "Reference our previous chat about my health."
        ]
        
        for query in recall_queries:
            assert memory_builder.is_memory_query(query), f"Failed to detect recall query: '{query}'"

    def test_topic_specific_recall(self, memory_builder):
        """Test detection of topic-specific recall."""
        # Test various topic-specific recall queries
        topic_queries = [
            "What do you know about my family?",
            "What did you know about my job?",
            "What have I told you about my hobbies?",
            "What did I mention about my house?",
            "What have we said about my health issues?"
        ]
        
        for query in topic_queries:
            assert memory_builder.is_memory_query(query), f"Failed to detect topic query: '{query}'"

    def test_previous_conversation_references(self, memory_builder):
        """Test detection of previous conversation references."""
        # Test various previous conversation references
        prev_queries = [
            "Last time we talked about my project.",
            "Previously you mentioned something about my diet.",
            "Earlier I told you about my new car.",
            "In our previous conversation about my job.",
            "During our last chat we discussed my vacation plans."
        ]
        
        for query in prev_queries:
            assert memory_builder.is_memory_query(query), f"Failed to detect previous conversation query: '{query}'"

    def test_fact_checking(self, memory_builder):
        """Test detection of fact checking queries."""
        # Test various fact checking queries
        fact_queries = [
            "Didn't I tell you about my promotion?",
            "Did we talk about my sister's wedding?",
            "Am I right that you know about my dog?",
            "Am I correct when I say we discussed my health issues?"
        ]
        
        for query in fact_queries:
            assert memory_builder.is_memory_query(query), f"Failed to detect fact checking query: '{query}'"

    def test_memory_keywords(self, memory_builder):
        """Test detection of memory keywords."""
        # Test various queries with memory keywords
        keyword_queries = [
            "I remember telling you about my job.",
            "Can you recall my favorite color?",
            "I might have forgotten what I told you.",
            "Check your memory about my family.",
            "You mentioned my project yesterday.",
            "I told you about my vacation plans.",
            "We said we would discuss this later.",
            "We talked about this last week.",
            "Our conversation about movies was interesting."
        ]
        
        for query in keyword_queries:
            assert memory_builder.is_memory_query(query), f"Failed to detect keyword query: '{query}'"

    def test_non_memory_queries(self, memory_builder):
        """Test that non-memory queries are correctly identified."""
        # Test various non-memory queries
        non_memory_queries = [
            "What's the weather like today?",
            "Tell me a joke.",
            "How are you doing?",
            "What's your name?",
            "Can you help me with my homework?",
            "What time is it?",
            "I'm feeling sad today.",
            "Do you like pizza?",
            "What's the capital of France?"
        ]
        
        for query in non_memory_queries:
            assert not memory_builder.is_memory_query(query), f"Incorrectly detected as memory query: '{query}'"

    def test_topic_extraction_from_query(self, memory_builder):
        """Test extraction of topics from queries."""
        # Mock the topic_extractor.extract_topics method
        memory_builder.topic_extractor.extract_topics.return_value = []
        
        # Test topic extraction with direct keyword matching
        query = "Tell me what you know about my family and my job."
        
        # Call the method
        topics = memory_builder.extract_topics_from_query(query)
        
        # Since we mocked extract_topics to return empty list, it should fall back to keyword matching
        assert "family" in topics, "Failed to extract 'family' topic"
        assert "work" in topics, "Failed to extract 'work' topic"
        
        # Test with TopicExtractor returning topics
        memory_builder.topic_extractor.extract_topics.return_value = ["family", "career"]
        
        # Call the method again
        topics = memory_builder.extract_topics_from_query(query)
        
        # Should use the topics from TopicExtractor
        assert topics == ["family", "career"], "Failed to use topics from TopicExtractor"
