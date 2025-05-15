"""
test_memory_context.py - Tests for memory context assembly functionality
"""

import sys
from pathlib import Path
import pytest
from sqlalchemy.orm import Session
import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.memory_context_service import assemble_memory_context
from app.models.user import User
from app.models.userfact import UserFact
from app.models.message import Message
from app.models.topic import Topic
from app.repository.memory import MemoryQueryRepository
from app.core.conversation_history_service import ConversationHistoryService

# Sample test data
TEST_USER = {"id": 1, "name": "Test User"}
TEST_FACTS = [
    {"id": 1, "user_id": 1, "fact_type": "job", "value": "Software Engineer at Google"},
    {"id": 2, "user_id": 1, "fact_type": "location", "value": "San Francisco"},
    {"id": 3, "user_id": 1, "fact_type": "interests", "value": "playing guitar and hiking"},
    {"id": 4, "user_id": 1, "fact_type": "family", "value": "married to Sarah, two kids: Emma and Jake"},
    {"id": 5, "user_id": 1, "fact_type": "preferences", "value": "loves Italian food"},
    {"id": 6, "user_id": 1, "fact_type": "pets", "value": "has a dog named Max"},
]
TEST_CONVERSATION = {"id": 1, "user_id": 1}
TEST_MESSAGES = [
    {"id": 1, "conversation_id": 1, "user_id": 1, "content": "I love working as a software engineer.", "timestamp": datetime.datetime.now() - datetime.timedelta(minutes=30)},
    {"id": 2, "conversation_id": 1, "user_id": 1, "content": "San Francisco is a beautiful city.", "timestamp": datetime.datetime.now() - datetime.timedelta(minutes=20)},
    {"id": 3, "conversation_id": 1, "user_id": 1, "content": "My daughter Emma is learning piano.", "timestamp": datetime.datetime.now() - datetime.timedelta(minutes=10)},
    {"id": 4, "conversation_id": 1, "user_id": 1, "content": "I might take Max for a walk later.", "timestamp": datetime.datetime.now() - datetime.timedelta(minutes=5)},
]
TEST_TOPICS = [
    {"id": 1, "name": "work"},
    {"id": 2, "name": "family"},
    {"id": 3, "name": "location"},
    {"id": 4, "name": "pets"},
]
# Message-topic associations
MESSAGE_TOPICS = [
    {"message_id": 1, "topic_id": 1},  # Message 1 is about work
    {"message_id": 2, "topic_id": 3},  # Message 2 is about location
    {"message_id": 3, "topic_id": 2},  # Message 3 is about family
    {"message_id": 4, "topic_id": 4},  # Message 4 is about pets
]

class TestMemoryContext:
    @pytest.fixture
    def mock_db_session(self, mocker):
        """Create a mock DB session with pre-loaded test data."""
        mock_session = mocker.MagicMock(spec=Session)

        # Mock app.repository.memory
        # Create an instance with the real get_facts_with_relevance method
        mock_memory_repo = mocker.MagicMock()

        # Define custom implementation for get_facts_with_relevance
        def mock_get_facts_with_relevance(user_id, query, limit=10):
            # Create UserFact objects from test data
            facts = []
            for fact_data in TEST_FACTS:
                fact = mocker.MagicMock(spec=UserFact)
                for k, v in fact_data.items():
                    setattr(fact, k, v)
                facts.append(fact)

            # Simple scoring logic
            scored_facts = []
            for fact in facts:
                score = 0.0
                query_terms = query.lower().split()

                # Special keywords boost
                if ('job' in query_terms or 'work' in query_terms) and fact.fact_type == 'job':
                    score += 2.0
                if ('kids' in query_terms or 'children' in query_terms) and fact.fact_type == 'family':
                    score += 2.0
                if ('live' in query_terms or 'location' in query_terms) and fact.fact_type == 'location':
                    score += 2.0
                if ('food' in query_terms or 'like' in query_terms) and fact.fact_type == 'preferences':
                    score += 1.5

                # Simple term matching
                for term in query_terms:
                    if term.lower() in fact.value.lower():
                        score += 1.0

                # Apply type weights
                type_weights = {
                    'job': 1.5,
                    'location': 1.3,
                    'family': 1.4,
                    'interests': 1.2,
                    'preferences': 1.1,
                    'pets': 1.0
                }

                if score > 0:
                    type_weight = type_weights.get(fact.fact_type, 1.0)
                    final_score = score * type_weight
                    scored_facts.append((fact, final_score))

            # Sort by score
            scored_facts.sort(key=lambda x: x[1], reverse=True)
            return scored_facts[:limit]

        # Mock get_recent_memories_for_user
        def mock_get_recent_memories(user_id, limit=20):
            recent_messages = []

            # Create Message objects
            for msg_data in TEST_MESSAGES:
                msg = mocker.MagicMock(spec=Message)
                for k, v in msg_data.items():
                    setattr(msg, k, v)
                recent_messages.append(msg)

            # Sort by timestamp (newest first)
            recent_messages.sort(key=lambda x: x.timestamp, reverse=True)
            return recent_messages[:limit]

        # Mock search_topics_by_message_content
        def mock_search_topics(user_id, query, limit=10):
            # Simple topic matching based on query terms
            matched_topics = []

            for topic_data in TEST_TOPICS:
                topic = mocker.MagicMock(spec=Topic)
                for k, v in topic_data.items():
                    setattr(topic, k, v)

                # Calculate score based on if topic name is in query
                score = 0.0
                if topic.name in query.lower():
                    score = 1.0
                elif topic.name == 'work' and ('job' in query.lower() or 'google' in query.lower()):
                    score = 0.8
                elif topic.name == 'family' and ('kids' in query.lower() or 'children' in query.lower()):
                    score = 0.8

                if score > 0:
                    matched_topics.append((topic, score))

            return matched_topics[:limit]

        # Mock get_messages_for_user_topic
        def mock_get_topic_messages(user_id, topic_id, limit=50):
            # Return messages associated with the topic
            topic_messages = []

            for assoc in MESSAGE_TOPICS:
                if assoc["topic_id"] == topic_id:
                    # Find the corresponding message
                    for msg_data in TEST_MESSAGES:
                        if msg_data["id"] == assoc["message_id"]:
                            msg = mocker.MagicMock(spec=Message)
                            for k, v in msg_data.items():
                                setattr(msg, k, v)
                            topic_messages.append(msg)

            return topic_messages[:limit]

        # Assign the mock methods
        mock_memory_repo.get_facts_with_relevance.side_effect = mock_get_facts_with_relevance
        mock_memory_repo.get_recent_memories_for_user.side_effect = mock_get_recent_memories
        mock_memory_repo.search_topics_by_message_content.side_effect = mock_search_topics
        mock_memory_repo.get_messages_for_user_topic.side_effect = mock_get_topic_messages

        # Mock the repository creation
        mocker.patch("app.repository.memory.MemoryQueryRepository", return_value=mock_memory_repo)

        # Mock the conversation history service
        mock_conversation_service = mocker.MagicMock()

        # Mock get_recent_messages_across_conversations
        def mock_get_recent_messages_across_conversations(user_id, limit=10, max_age_days=None):
            # Reuse the same logic as mock_get_recent_memories
            recent_messages = []

            # Create Message objects
            for msg_data in TEST_MESSAGES:
                msg = mocker.MagicMock(spec=Message)
                for k, v in msg_data.items():
                    setattr(msg, k, v)
                recent_messages.append(msg)

            # Sort by timestamp (newest first)
            recent_messages.sort(key=lambda x: x.timestamp, reverse=True)
            return recent_messages[:limit]

        # Mock format_messages_for_context
        def mock_format_messages_for_context(messages, include_timestamps=True):
            formatted_messages = []
            for msg in messages:
                message_dict = {
                    "content": msg.content,
                    "user_id": msg.user_id
                }
                if include_timestamps and hasattr(msg, "timestamp"):
                    message_dict["timestamp"] = msg.timestamp.isoformat()
                formatted_messages.append(message_dict)
            return formatted_messages

        # Assign the mock methods
        mock_conversation_service.get_recent_messages_across_conversations.side_effect = mock_get_recent_messages_across_conversations
        mock_conversation_service.format_messages_for_context.side_effect = mock_format_messages_for_context

        # Mock the service creation
        mocker.patch("app.core.conversation_history_service.ConversationHistoryService", return_value=mock_conversation_service)

        return mock_session

    def test_assemble_memory_context_job_query(self, mock_db_session):
        """Test memory context assembly for a job-related query."""
        # Call the service
        memory_context = assemble_memory_context(mock_db_session, 1, "Tell me about your job at Google")

        # Assertions
        assert "user_facts" in memory_context
        assert "recent_memories" in memory_context
        assert "topic_memories" in memory_context

        # Check that job fact is included and has high confidence
        job_facts = [f for f in memory_context["user_facts"] if f["type"] == "job"]
        assert len(job_facts) > 0
        assert "Google" in job_facts[0]["value"]
        assert job_facts[0]["confidence"] >= 90  # Should have high confidence

        # Print the memory context for debugging
        print("\nMemory Context for job query:")
        print(f"User Facts: {memory_context['user_facts']}")
        print(f"Recent Memories: {len(memory_context['recent_memories'])}")
        print(f"Topic Memories: {memory_context['topic_memories']}")

    def test_assemble_memory_context_combined_query(self, mock_db_session):
        """Test memory context assembly for a query with multiple topics."""
        # Call the service
        memory_context = assemble_memory_context(
            mock_db_session, 1,
            "Do you have kids and where do you live?"
        )

        # Assertions
        assert "user_facts" in memory_context

        # Should include both family and location facts
        fact_types = [f["type"] for f in memory_context["user_facts"]]
        assert "family" in fact_types
        assert "location" in fact_types

        # Print the memory context for debugging
        print("\nMemory Context for combined query:")
        print(f"User Facts: {memory_context['user_facts']}")
        print(f"Recent Memories: {len(memory_context['recent_memories'])}")
        print(f"Topic Memories: {memory_context['topic_memories']}")

if __name__ == "__main__":
    pytest.main(["-v", "test_memory_context.py"])
