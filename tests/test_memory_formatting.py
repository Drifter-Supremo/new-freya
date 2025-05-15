"""
test_memory_formatting.py - Tests for memory context formatting
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.memory_context_service import MemoryContextBuilder


class TestMemoryFormatting:
    """Test suite for memory context formatting functionality."""

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
            "is_memory_query": True,
            "memory_query_topics": ["work", "job"],
            "memory_query_type": "recall_verification"
        }

    def test_format_user_facts(self, memory_builder):
        """Test formatting of user facts."""
        facts = [
            {"type": "job", "value": "Software Engineer at Google", "confidence": 80},
            {"type": "location", "value": "San Francisco", "confidence": 70}
        ]
        
        formatted_facts = memory_builder._format_user_facts(facts)
        
        # Check that the formatting includes the expected content
        assert "## User Facts" in formatted_facts
        assert "Job: Software Engineer at Google" in formatted_facts
        assert "Location: San Francisco" in formatted_facts
        assert "★★★★★" in formatted_facts  # Check for confidence indicators
        
        # Test with empty facts
        assert memory_builder._format_user_facts([]) == ""

    def test_format_topic_memories_for_recall(self, memory_builder):
        """Test formatting of topic memories for recall queries."""
        topic_memories = [
            {
                "topic": {"id": 1, "name": "Work", "relevance": 80},
                "messages": [
                    {"content": "I work as a Software Engineer at Google."},
                    {"content": "My team is working on a new project."}
                ]
            }
        ]
        
        formatted_memories = memory_builder._format_topic_memories_for_recall(topic_memories)
        
        # Check that the formatting includes the expected content
        assert "## Topic-Related Memories" in formatted_memories
        assert "### Work" in formatted_memories
        assert "I work as a Software Engineer at Google." in formatted_memories
        assert "My team is working on a new project." in formatted_memories
        
        # Test with empty topic memories
        assert memory_builder._format_topic_memories_for_recall([]) == ""
        
        # Test with low relevance topic (should be filtered out)
        low_relevance_topic = [
            {
                "topic": {"id": 1, "name": "Work", "relevance": 20},
                "messages": [
                    {"content": "I work as a Software Engineer at Google."}
                ]
            }
        ]
        formatted_low_relevance = memory_builder._format_topic_memories_for_recall(low_relevance_topic)
        assert "### Work" not in formatted_low_relevance

    def test_format_recent_memories_for_recall(self, memory_builder):
        """Test formatting of recent memories for recall queries."""
        recent_memories = [
            {"content": "I work as a Software Engineer at Google.", "relevance": 80},
            {"content": "My family includes my spouse and two children.", "relevance": 70}
        ]
        
        formatted_memories = memory_builder._format_recent_memories_for_recall(recent_memories)
        
        # Check that the formatting includes the expected content
        assert "## Recent Conversation History" in formatted_memories
        assert "I work as a Software Engineer at Google." in formatted_memories
        assert "My family includes my spouse and two children." in formatted_memories
        
        # Test with empty recent memories
        assert memory_builder._format_recent_memories_for_recall([]) == ""
        
        # Test with low relevance memory (should be filtered out)
        low_relevance_memory = [
            {"content": "I work as a Software Engineer at Google.", "relevance": 20}
        ]
        formatted_low_relevance = memory_builder._format_recent_memories_for_recall(low_relevance_memory)
        assert "I work as a Software Engineer at Google." not in formatted_low_relevance

    def test_format_memories_with_timestamps(self, memory_builder):
        """Test formatting of memories with timestamps."""
        recent_memories = [
            {"content": "I work as a Software Engineer at Google.", "timestamp": "2023-05-15T10:00:00Z"},
            {"content": "My family includes my spouse and two children.", "timestamp": "2023-05-14T10:00:00Z"}
        ]
        
        topic_memories = [
            {
                "topic": {"name": "Work"},
                "messages": [
                    {"content": "My team is working on a new project.", "timestamp": "2023-05-14T11:00:00Z"}
                ]
            }
        ]
        
        formatted_memories = memory_builder._format_memories_with_timestamps(recent_memories, topic_memories)
        
        # Check that the formatting includes the expected content
        assert "## Conversation Timeline" in formatted_memories
        assert "I work as a Software Engineer at Google." in formatted_memories
        assert "My family includes my spouse and two children." in formatted_memories
        assert "My team is working on a new project." in formatted_memories
        assert "May 15, 2023" in formatted_memories or "2023-05-15" in formatted_memories
        
        # Test with empty memories
        assert memory_builder._format_memories_with_timestamps([], []) == ""

    def test_format_complete_memory_context(self, memory_builder, sample_memory_context):
        """Test formatting of complete memory context."""
        # Test recall verification query
        sample_memory_context["memory_query_type"] = "recall_verification"
        formatted_context = memory_builder.format_memory_context(sample_memory_context)
        
        # Check that the formatting includes the expected sections
        assert "### Memory Context ###" in formatted_context
        assert "## User Facts" in formatted_context
        assert "## Topic-Related Memories" in formatted_context
        assert "## Recent Conversation History" in formatted_context
        
        # Test temporal recall query
        sample_memory_context["memory_query_type"] = "temporal_recall"
        formatted_context = memory_builder.format_memory_context(sample_memory_context)
        
        # Check that the formatting includes the expected sections
        assert "### Memory Context ###" in formatted_context
        assert "## User Facts" in formatted_context
        assert "## Conversation Timeline" in formatted_context
        
        # Test existence verification query
        sample_memory_context["memory_query_type"] = "existence_verification"
        formatted_context = memory_builder.format_memory_context(sample_memory_context)
        
        # Check that the formatting includes the expected sections
        assert "### Memory Context ###" in formatted_context
        assert "## User Facts" in formatted_context
        assert "## Memory Verification" in formatted_context
        
        # Test knowledge query
        sample_memory_context["memory_query_type"] = "knowledge_query"
        formatted_context = memory_builder.format_memory_context(sample_memory_context)
        
        # Check that the formatting includes the expected sections
        assert "### Memory Context ###" in formatted_context
        assert "## User Facts" in formatted_context
        assert "## Knowledge About User" in formatted_context
        
        # Test non-memory query
        sample_memory_context["is_memory_query"] = False
        formatted_context = memory_builder.format_memory_context(sample_memory_context)
        
        # Check that the formatting includes the expected sections
        assert "### Memory Context ###" in formatted_context
        assert "## User Facts" in formatted_context
        assert "## Relevant Topics" in formatted_context or "## Recent Conversation" in formatted_context
