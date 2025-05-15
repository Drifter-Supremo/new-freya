"""
test_memory_prioritization.py - Tests for memory prioritization logic
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.memory_context_service import MemoryContextBuilder


class TestMemoryPrioritization:
    """Test suite for memory prioritization functionality."""

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

    @pytest.fixture
    def sample_memory_context(self):
        """Create a sample memory context for testing."""
        return {
            "user_facts": [
                {"type": "job", "value": "Software Engineer at Google", "confidence": 80},
                {"type": "location", "value": "San Francisco", "confidence": 70},
                {"type": "family", "value": "Married with two kids", "confidence": 60},
                {"type": "hobby", "value": "Playing guitar and hiking", "confidence": 50},
                {"type": "education", "value": "Computer Science degree from Stanford", "confidence": 40}
            ],
            "recent_memories": [
                {"content": "I work as a Software Engineer at Google.", "user_id": 1, "timestamp": "2023-05-15T10:00:00Z"},
                {"content": "My family includes my spouse and two children.", "user_id": 1, "timestamp": "2023-05-14T10:00:00Z"},
                {"content": "I've been trying to improve my health by exercising more.", "user_id": 1, "timestamp": "2023-05-13T10:00:00Z"},
                {"content": "I enjoy playing guitar and hiking on weekends.", "user_id": 1, "timestamp": "2023-05-12T10:00:00Z"},
                {"content": "I studied Computer Science at Stanford University.", "user_id": 1, "timestamp": "2023-05-11T10:00:00Z"}
            ],
            "topic_memories": [
                {
                    "topic": {"id": 1, "name": "Work", "relevance_score": 0.8, "relevance": 80},
                    "message_count": 2,
                    "messages": [
                        {"content": "I work as a Software Engineer at Google.", "user_id": 1, "timestamp": "2023-05-15T10:00:00Z"},
                        {"content": "My team is working on a new project.", "user_id": 1, "timestamp": "2023-05-14T10:00:00Z"}
                    ]
                },
                {
                    "topic": {"id": 2, "name": "Family", "relevance_score": 0.7, "relevance": 70},
                    "message_count": 2,
                    "messages": [
                        {"content": "My family includes my spouse and two children.", "user_id": 1, "timestamp": "2023-05-14T10:00:00Z"},
                        {"content": "We're planning a family vacation next month.", "user_id": 1, "timestamp": "2023-05-13T10:00:00Z"}
                    ]
                },
                {
                    "topic": {"id": 3, "name": "Health", "relevance_score": 0.6, "relevance": 60},
                    "message_count": 1,
                    "messages": [
                        {"content": "I've been trying to improve my health by exercising more.", "user_id": 1, "timestamp": "2023-05-13T10:00:00Z"}
                    ]
                }
            ],
            "is_memory_query": True
        }

    def test_prioritize_facts_by_topics(self, memory_builder):
        """Test prioritization of user facts based on query topics."""
        # Sample facts and topics
        facts = [
            {"type": "job", "value": "Software Engineer at Google", "confidence": 80},
            {"type": "location", "value": "San Francisco", "confidence": 70},
            {"type": "family", "value": "Married with two kids", "confidence": 60}
        ]
        topics = ["work", "job", "career"]

        # Call the method
        prioritized_facts = memory_builder._prioritize_facts_by_topics(facts, topics)

        # Verify that job-related fact is prioritized
        assert prioritized_facts[0]["type"] == "job"
        assert prioritized_facts[0]["confidence"] > 80  # Should be boosted

        # Test with different topics
        topics = ["family", "children"]
        prioritized_facts = memory_builder._prioritize_facts_by_topics(facts, topics)

        # Verify that family-related fact is prioritized
        assert prioritized_facts[0]["type"] == "family"
        assert prioritized_facts[0]["confidence"] > 60  # Should be boosted

    def test_prioritize_recent_memories(self, memory_builder):
        """Test prioritization of recent memories based on query content."""
        # Sample memories
        memories = [
            {"content": "I work as a Software Engineer at Google.", "user_id": 1, "timestamp": "2023-05-15T10:00:00Z"},
            {"content": "My family includes my spouse and two children.", "user_id": 1, "timestamp": "2023-05-14T10:00:00Z"},
            {"content": "I've been trying to improve my health by exercising more.", "user_id": 1, "timestamp": "2023-05-13T10:00:00Z"}
        ]

        # Test with job-related query
        query = "Tell me about my job at Google."
        prioritized_memories = memory_builder._prioritize_recent_memories(memories, query)

        # Verify that job-related memory is prioritized
        assert "Software Engineer" in prioritized_memories[0]["content"]
        assert "relevance" in prioritized_memories[0]

        # Test with family-related query
        query = "What did I tell you about my family?"
        prioritized_memories = memory_builder._prioritize_recent_memories(memories, query)

        # Verify that family-related memory is prioritized
        assert "family" in prioritized_memories[0]["content"].lower()
        assert "relevance" in prioritized_memories[0]

    def test_prioritize_topic_memories(self, memory_builder):
        """Test prioritization of topic memories based on query topics."""
        # Sample topic memories
        topic_memories = [
            {
                "topic": {"id": 1, "name": "Work", "relevance_score": 0.8, "relevance": 80},
                "message_count": 2,
                "messages": [{"content": "I work as a Software Engineer at Google."}]
            },
            {
                "topic": {"id": 2, "name": "Family", "relevance_score": 0.7, "relevance": 70},
                "message_count": 2,
                "messages": [{"content": "My family includes my spouse and two children."}]
            }
        ]

        # Test with work-related topics
        query_topics = ["work", "job", "career"]
        prioritized_topic_memories = memory_builder._prioritize_topic_memories(topic_memories, query_topics)

        # Verify that work-related topic is prioritized
        assert prioritized_topic_memories[0]["topic"]["name"] == "Work"
        assert prioritized_topic_memories[0]["topic"]["relevance"] > 80  # Should be boosted

        # Test with family-related topics
        query_topics = ["family", "children"]
        prioritized_topic_memories = memory_builder._prioritize_topic_memories(topic_memories, query_topics)

        # Verify that family-related topic is prioritized
        assert prioritized_topic_memories[0]["topic"]["name"] == "Family"
        assert prioritized_topic_memories[0]["topic"]["relevance"] > 70  # Should be boosted

    def test_classify_memory_query_type(self, memory_builder):
        """Test classification of memory query types."""
        # Test different query types
        assert memory_builder._classify_memory_query_type("Do you remember what I told you about my job?") == "recall_verification"
        assert memory_builder._classify_memory_query_type("What did I say about my family?") == "content_recall"
        assert memory_builder._classify_memory_query_type("When did we discuss my health?") == "temporal_recall"
        assert memory_builder._classify_memory_query_type("Have we talked about my hobbies before?") == "existence_verification"
        assert memory_builder._classify_memory_query_type("What do you know about my education?") == "knowledge_query"
        assert memory_builder._classify_memory_query_type("Last time we talked about my vacation plans.") == "previous_conversation"
        assert memory_builder._classify_memory_query_type("Didn't I tell you about my new car?") == "fact_checking"
        assert memory_builder._classify_memory_query_type("Tell me what you remember about me.") == "general_memory_query"

    def test_prioritize_memories_for_memory_query(self, memory_builder, sample_memory_context):
        """Test the complete memory prioritization process."""
        # Create a fresh copy of the sample context for each test
        job_context = sample_memory_context.copy()
        job_context["user_facts"] = sample_memory_context["user_facts"].copy()
        job_context["recent_memories"] = sample_memory_context["recent_memories"].copy()
        job_context["topic_memories"] = sample_memory_context["topic_memories"].copy()

        # Mock extract_topics_from_query to return specific topics
        memory_builder.extract_topics_from_query = MagicMock(return_value=["work", "job"])

        # Test with job-related query
        query = "Do you remember what I told you about my job at Google?"
        prioritized_context = memory_builder._prioritize_memories_for_memory_query(job_context, query)

        # Verify that the context has been prioritized
        assert "memory_query_topics" in prioritized_context
        assert "memory_query_type" in prioritized_context
        assert prioritized_context["memory_query_type"] == "recall_verification"

        # Verify that job-related facts and memories are prioritized
        if prioritized_context["user_facts"]:
            assert prioritized_context["user_facts"][0]["type"] == "job"

        # Create a fresh copy of the sample context for the family test
        family_context = sample_memory_context.copy()
        family_context["user_facts"] = [
            {"type": "job", "value": "Software Engineer at Google", "confidence": 80},
            {"type": "location", "value": "San Francisco", "confidence": 70},
            {"type": "family", "value": "Married with two kids", "confidence": 60},
            {"type": "hobby", "value": "Playing guitar and hiking", "confidence": 50},
            {"type": "education", "value": "Computer Science degree from Stanford", "confidence": 40}
        ]
        family_context["recent_memories"] = sample_memory_context["recent_memories"].copy()
        family_context["topic_memories"] = sample_memory_context["topic_memories"].copy()

        # Test with family-related query
        memory_builder.extract_topics_from_query = MagicMock(return_value=["family", "children"])
        query = "What did I tell you about my family?"
        prioritized_context = memory_builder._prioritize_memories_for_memory_query(family_context, query)

        # Verify that family-related facts and memories are prioritized
        if prioritized_context["user_facts"]:
            assert prioritized_context["user_facts"][0]["type"] == "family"
        assert prioritized_context["memory_query_type"] == "content_recall"
