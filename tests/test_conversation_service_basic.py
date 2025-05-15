"""
test_conversation_service_basic.py - Basic tests for conversation history service
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch
import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.conversation_history_service import ConversationHistoryService
from app.models.conversation import Conversation
from app.models.message import Message

# Sample test data
TEST_CONVERSATIONS = [
    {"id": 1, "user_id": 1, "started_at": datetime.datetime.now() - datetime.timedelta(days=5)},
    {"id": 2, "user_id": 1, "started_at": datetime.datetime.now() - datetime.timedelta(days=2)},
    {"id": 3, "user_id": 1, "started_at": datetime.datetime.now() - datetime.timedelta(days=1)},
]

TEST_MESSAGES = [
    {"id": 1, "conversation_id": 1, "user_id": 1, "content": "Hello, this is the first message",
     "timestamp": datetime.datetime.now() - datetime.timedelta(days=5, hours=1)},
    {"id": 2, "conversation_id": 1, "user_id": 1, "content": "This is a follow-up message",
     "timestamp": datetime.datetime.now() - datetime.timedelta(days=5)},
    {"id": 3, "conversation_id": 2, "user_id": 1, "content": "Starting a new conversation",
     "timestamp": datetime.datetime.now() - datetime.timedelta(days=2, hours=3)},
]

def create_mock_message(msg_data):
    """Helper to create a mock Message object from test data."""
    msg = MagicMock(spec=Message)
    for k, v in msg_data.items():
        setattr(msg, k, v)
    return msg

def create_mock_conversation(conv_data):
    """Helper to create a mock Conversation object from test data."""
    conv = MagicMock(spec=Conversation)
    for k, v in conv_data.items():
        setattr(conv, k, v)
    return conv

class TestConversationHistoryServiceBasic:
    def test_format_messages_for_context(self):
        """Test the format_messages_for_context method."""
        # Create mock DB session
        mock_db = MagicMock()

        # Create test messages
        messages = [create_mock_message(msg_data) for msg_data in TEST_MESSAGES]

        # Create service
        service = ConversationHistoryService(mock_db)

        # Test with timestamps
        formatted_with_timestamps = service.format_messages_for_context(
            messages=messages,
            include_timestamps=True
        )

        # Test without timestamps
        formatted_without_timestamps = service.format_messages_for_context(
            messages=messages,
            include_timestamps=False
        )

        # Assertions
        assert len(formatted_with_timestamps) == len(messages)
        assert all("timestamp" in msg for msg in formatted_with_timestamps)
        assert all("content" in msg for msg in formatted_with_timestamps)

        assert len(formatted_without_timestamps) == len(messages)
        assert all("timestamp" not in msg for msg in formatted_without_timestamps)
        assert all("content" in msg for msg in formatted_without_timestamps)

    def test_get_conversation_context(self):
        """Test the get_conversation_context method."""
        # Create mock DB session
        mock_db = MagicMock()

        # Create a service
        service = ConversationHistoryService(mock_db)

        # Create a mock conversation
        mock_conversation = create_mock_conversation(TEST_CONVERSATIONS[1])  # Conversation ID 2

        # Create mock messages for this conversation
        mock_messages = [
            create_mock_message(msg)
            for msg in TEST_MESSAGES
            if msg["conversation_id"] == 2
        ]

        # Directly patch the conversation_repo attribute
        service.conversation_repo = MagicMock()
        service.conversation_repo.get.return_value = mock_conversation

        # Mock the get_conversation_history method
        with patch.object(service, 'get_conversation_history', return_value=mock_messages):
            # Get conversation context
            context = service.get_conversation_context(conversation_id=2, message_limit=3)

            # Assertions
            assert context["conversation_id"] == mock_conversation.id
            assert context["user_id"] == mock_conversation.user_id
            assert "started_at" in context
            assert "messages" in context
            assert isinstance(context["messages"], list)
            assert len(context["messages"]) <= 3  # Should respect the message_limit

    def test_get_conversation_context_not_found(self):
        """Test the get_conversation_context method when conversation is not found."""
        # Create mock DB session
        mock_db = MagicMock()

        # Create a service
        service = ConversationHistoryService(mock_db)

        # Directly patch the conversation_repo attribute to return None
        service.conversation_repo = MagicMock()
        service.conversation_repo.get.return_value = None

        # Get conversation context
        context = service.get_conversation_context(conversation_id=999)

        # Assertions
        assert "error" in context
        assert context["error"] == "Conversation not found"
