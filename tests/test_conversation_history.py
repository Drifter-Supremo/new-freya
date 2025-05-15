"""
test_conversation_history.py - Tests for conversation history service
"""

import sys
from pathlib import Path
import pytest
from sqlalchemy.orm import Session
import datetime
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.conversation_history_service import ConversationHistoryService
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message

# Test data
TEST_USER = {"id": 1, "username": "testuser", "email": "test@example.com"}
TEST_CONVERSATIONS = [
    {"id": 1, "user_id": 1, "started_at": datetime.datetime.now() - datetime.timedelta(days=5)},
    {"id": 2, "user_id": 1, "started_at": datetime.datetime.now() - datetime.timedelta(days=2)},
    {"id": 3, "user_id": 1, "started_at": datetime.datetime.now() - datetime.timedelta(days=1)},
]
TEST_MESSAGES = [
    # Conversation 1 messages
    {"id": 1, "conversation_id": 1, "user_id": 1, "content": "Hello, this is the first message",
     "timestamp": datetime.datetime.now() - datetime.timedelta(days=5, hours=1)},
    {"id": 2, "conversation_id": 1, "user_id": 1, "content": "This is a follow-up message",
     "timestamp": datetime.datetime.now() - datetime.timedelta(days=5)},

    # Conversation 2 messages
    {"id": 3, "conversation_id": 2, "user_id": 1, "content": "Starting a new conversation",
     "timestamp": datetime.datetime.now() - datetime.timedelta(days=2, hours=3)},
    {"id": 4, "conversation_id": 2, "user_id": 1, "content": "This is interesting",
     "timestamp": datetime.datetime.now() - datetime.timedelta(days=2, hours=2)},
    {"id": 5, "conversation_id": 2, "user_id": 1, "content": "Let's continue this discussion",
     "timestamp": datetime.datetime.now() - datetime.timedelta(days=2, hours=1)},

    # Conversation 3 messages (most recent)
    {"id": 6, "conversation_id": 3, "user_id": 1, "content": "New topic for today",
     "timestamp": datetime.datetime.now() - datetime.timedelta(hours=5)},
    {"id": 7, "conversation_id": 3, "user_id": 1, "content": "I have a question about this",
     "timestamp": datetime.datetime.now() - datetime.timedelta(hours=4)},
    {"id": 8, "conversation_id": 3, "user_id": 1, "content": "Thanks for the information",
     "timestamp": datetime.datetime.now() - datetime.timedelta(hours=3)},
]

class TestConversationHistoryService:
    @pytest.fixture
    def mock_db_session(self, mocker):
        """Create a mock DB session with pre-loaded test data."""
        mock_session = mocker.MagicMock(spec=Session)

        # Mock query builder
        mock_query = mocker.MagicMock()
        mock_session.query.return_value = mock_query

        # Set up the mock query chain for different scenarios
        self._setup_conversation_history_mock(mock_query, mocker)
        self._setup_recent_conversations_mock(mock_query, mocker)
        self._setup_recent_messages_mock(mock_query, mocker)

        # Mock repositories
        mocker.patch("app.repository.conversation.ConversationRepository")
        mocker.patch("app.repository.message.MessageRepository")

        return mock_session

    def _setup_conversation_history_mock(self, mock_query, mocker):
        """Set up mocks for get_conversation_history method."""
        # Create a direct mock for the entire query chain
        mock_result = mocker.MagicMock()

        # Set up the final result
        def mock_all_for_conversation(*args, **kwargs):
            # Extract conversation_id from the filter call
            # This is a simplification - in a real scenario we'd need to parse the filter args
            conversation_id = None
            for call in mock_query.mock_calls:
                if call[0] == 'filter' and len(call[1]) > 0:
                    # Look for Message.conversation_id == conversation_id pattern
                    for arg in call[1]:
                        if hasattr(arg, 'right') and hasattr(arg, 'left'):
                            conversation_id = getattr(arg, 'right', None)
                            break

            # If we couldn't extract it from calls, use a default
            conversation_id = conversation_id or 2  # Default to conversation 2 for testing

            # Filter messages by conversation_id
            filtered_messages = [
                self._create_message_mock(msg, mocker)
                for msg in TEST_MESSAGES
                if msg["conversation_id"] == conversation_id
            ]
            # Sort by timestamp (newest first)
            filtered_messages.sort(key=lambda x: x.timestamp, reverse=True)
            return filtered_messages

        # Set up the entire chain to return our mock result
        mock_query.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.options.return_value.all.side_effect = mock_all_for_conversation

    def _setup_recent_conversations_mock(self, mock_query, mocker):
        """Set up mocks for get_recent_conversations method."""
        # Set up the final result
        def mock_all_for_recent_conversations(*args, **kwargs):
            # Create conversation mocks
            conversations = [
                self._create_conversation_mock(conv, mocker)
                for conv in TEST_CONVERSATIONS
            ]
            # Sort by the timestamp of their latest message
            conversations.sort(
                key=lambda x: max(
                    msg["timestamp"] for msg in TEST_MESSAGES
                    if msg["conversation_id"] == x.id
                ),
                reverse=True
            )
            return conversations

        # Set up the entire chain to return our mock result
        mock_query.query.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.side_effect = mock_all_for_recent_conversations

    def _setup_recent_messages_mock(self, mock_query, mocker):
        """Set up mocks for get_recent_messages_across_conversations method."""
        # Set up the final result
        def mock_all_for_recent_messages(*args, **kwargs):
            # Create message mocks
            messages = [
                self._create_message_mock(msg, mocker)
                for msg in TEST_MESSAGES
            ]
            # Sort by timestamp (newest first)
            messages.sort(key=lambda x: x.timestamp, reverse=True)
            return messages

        # Set up the entire chain to return our mock result
        mock_query.query.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.options.return_value.all.side_effect = mock_all_for_recent_messages

    def _create_message_mock(self, msg_data, mocker):
        """Create a mock Message object from test data."""
        msg = mocker.MagicMock(spec=Message)
        for k, v in msg_data.items():
            setattr(msg, k, v)
        return msg

    def _create_conversation_mock(self, conv_data, mocker):
        """Create a mock Conversation object from test data."""
        conv = mocker.MagicMock(spec=Conversation)
        for k, v in conv_data.items():
            setattr(conv, k, v)
        return conv

    def test_get_conversation_history(self, mock_db_session):
        """Test retrieving conversation history."""
        service = ConversationHistoryService(mock_db_session)

        # Get history for conversation 2
        messages = service.get_conversation_history(conversation_id=2, limit=10)

        # Assertions
        assert len(messages) == 3
        assert all(msg.conversation_id == 2 for msg in messages)
        # Check that messages are ordered by timestamp (newest first)
        timestamps = [msg.timestamp for msg in messages]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_get_recent_conversations(self, mock_db_session):
        """Test retrieving recent conversations."""
        service = ConversationHistoryService(mock_db_session)

        # Get recent conversations
        conversations = service.get_recent_conversations(user_id=1, limit=3)

        # Assertions
        assert len(conversations) == 3
        # Conversation 3 should be first (most recent)
        assert conversations[0].id == 3

    def test_get_recent_messages_across_conversations(self, mock_db_session):
        """Test retrieving recent messages across all conversations."""
        service = ConversationHistoryService(mock_db_session)

        # Get recent messages
        messages = service.get_recent_messages_across_conversations(user_id=1, limit=5)

        # Assertions
        assert len(messages) == 5
        # Messages should be ordered by timestamp (newest first)
        timestamps = [msg.timestamp for msg in messages]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_get_conversation_context(self, mock_db_session, mocker):
        """Test retrieving formatted conversation context."""
        # Mock the conversation repository
        mock_repo = mocker.MagicMock()

        # Create a conversation mock with explicit attributes
        conv_mock = mocker.MagicMock(spec=Conversation)
        conv_mock.id = 2
        conv_mock.user_id = 1
        conv_mock.started_at = datetime.datetime.now() - datetime.timedelta(days=2)

        # Set up the mock repository to return our conversation
        mock_repo.get.return_value = conv_mock
        mocker.patch("app.repository.conversation.ConversationRepository", return_value=mock_repo)

        # Mock the get_conversation_history method
        mock_messages = [
            self._create_message_mock(msg, mocker)
            for msg in TEST_MESSAGES
            if msg["conversation_id"] == 2
        ]

        # Create a service with mocked methods
        service = ConversationHistoryService(mock_db_session)
        service.get_conversation_history = mocker.MagicMock(return_value=mock_messages)

        # Get conversation context
        context = service.get_conversation_context(conversation_id=2, message_limit=3)

        # Assertions
        assert context["conversation_id"] == 2
        assert context["user_id"] == 1
        assert "started_at" in context
        assert "messages" in context
        assert isinstance(context["messages"], list)

    def test_format_messages_for_context(self, mock_db_session, mocker):
        """Test formatting messages for context."""
        service = ConversationHistoryService(mock_db_session)

        # Create some test messages
        messages = [
            self._create_message_mock(TEST_MESSAGES[0], mocker),
            self._create_message_mock(TEST_MESSAGES[1], mocker),
        ]

        # Format messages with timestamps
        formatted_with_timestamps = service.format_messages_for_context(
            messages, include_timestamps=True
        )

        # Format messages without timestamps
        formatted_without_timestamps = service.format_messages_for_context(
            messages, include_timestamps=False
        )

        # Assertions
        assert len(formatted_with_timestamps) == 2
        assert all("timestamp" in msg for msg in formatted_with_timestamps)
        assert all("content" in msg for msg in formatted_with_timestamps)

        assert len(formatted_without_timestamps) == 2
        assert all("timestamp" not in msg for msg in formatted_without_timestamps)
        assert all("content" in msg for msg in formatted_without_timestamps)
