"""
test_conversation_api_basic.py - Basic tests for conversation API endpoints
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.main import app
from app.models.conversation import Conversation
from app.models.message import Message

client = TestClient(app)

# Sample test data
TEST_USER_ID = 1
TEST_CONVERSATION_ID = 1
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

@pytest.fixture
def mock_conversation_service():
    """Mock the ConversationHistoryService."""
    with patch("app.core.conversation_history_service.ConversationHistoryService") as mock:
        # Create an instance of the mock
        mock_instance = MagicMock()

        # Set up mock methods
        def mock_get_recent_conversations(user_id, limit=5):
            # Create Conversation objects
            conversations = [create_mock_conversation(conv_data) for conv_data in TEST_CONVERSATIONS]
            return conversations[:limit]

        def mock_get_conversation_history(conversation_id, limit=20, skip=0):
            # Create Message objects
            messages = [
                create_mock_message(msg_data)
                for msg_data in TEST_MESSAGES
                if msg_data["conversation_id"] == conversation_id
            ]
            # Sort by timestamp (newest first)
            messages.sort(key=lambda x: x.timestamp, reverse=True)
            return messages[skip:skip+limit]

        def mock_get_recent_messages_across_conversations(user_id, limit=20, max_age_days=None):
            # Create Message objects
            messages = [create_mock_message(msg_data) for msg_data in TEST_MESSAGES]
            # Sort by timestamp (newest first)
            messages.sort(key=lambda x: x.timestamp, reverse=True)
            return messages[:limit]

        def mock_get_conversation_context(conversation_id, message_limit=10):
            # Check if conversation exists
            conv_exists = any(c["id"] == conversation_id for c in TEST_CONVERSATIONS)
            if not conv_exists:
                return {"error": "Conversation not found"}

            # Get conversation data
            conv_data = next(c for c in TEST_CONVERSATIONS if c["id"] == conversation_id)

            # Get messages
            messages = [
                {
                    "id": msg["id"],
                    "content": msg["content"],
                    "timestamp": msg["timestamp"].isoformat(),
                    "user_id": msg["user_id"]
                }
                for msg in TEST_MESSAGES
                if msg["conversation_id"] == conversation_id
            ]

            # Sort by timestamp (newest first)
            messages.sort(key=lambda x: x["timestamp"], reverse=True)

            return {
                "conversation_id": conv_data["id"],
                "user_id": conv_data["user_id"],
                "started_at": conv_data["started_at"].isoformat(),
                "message_count": len(messages),
                "messages": messages[:message_limit]
            }

        # Assign mock methods
        mock_instance.get_recent_conversations.side_effect = mock_get_recent_conversations
        mock_instance.get_conversation_history.side_effect = mock_get_conversation_history
        mock_instance.get_recent_messages_across_conversations.side_effect = mock_get_recent_messages_across_conversations
        mock_instance.get_conversation_context.side_effect = mock_get_conversation_context

        # Return the mock
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_conversation_repo():
    """Mock the ConversationRepository."""
    with patch("app.repository.conversation.ConversationRepository") as mock:
        # Create an instance of the mock
        mock_instance = MagicMock()

        # Set up mock methods
        def mock_get(id):
            # Check if conversation exists
            conv_exists = any(c["id"] == id for c in TEST_CONVERSATIONS)
            if not conv_exists:
                return None

            # Create Conversation object
            conv_data = next(c for c in TEST_CONVERSATIONS if c["id"] == id)
            return create_mock_conversation(conv_data)

        # Assign mock methods
        mock_instance.get.side_effect = mock_get

        # Return the mock
        mock.return_value = mock_instance
        yield mock_instance

def test_get_recent_conversations(mock_conversation_service, mock_conversation_repo):
    """Test GET /conversations/{user_id}/recent endpoint."""
    response = client.get(f"/conversations/{TEST_USER_ID}/recent")

    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    # Check that conversations are returned in the expected format
    for conv in data:
        assert "id" in conv
        assert "user_id" in conv
        assert "started_at" in conv

def test_get_conversation_context(mock_conversation_service, mock_conversation_repo):
    """Test GET /conversations/{conversation_id}/context endpoint."""
    response = client.get(f"/conversations/{TEST_CONVERSATION_ID}/context")

    # Check response
    assert response.status_code == 200
    data = response.json()

    # Check that context is returned in the expected format
    assert "conversation_id" in data
    assert "user_id" in data
    assert "started_at" in data
    assert "message_count" in data
    assert "messages" in data
    assert isinstance(data["messages"], list)

def test_get_conversation_context_not_found(mock_conversation_service, mock_conversation_repo):
    """Test GET /conversations/{conversation_id}/context with non-existent conversation."""
    # Set up mock to return error for non-existent conversation
    mock_conversation_service.get_conversation_context.return_value = {"error": "Conversation not found"}

    response = client.get("/conversations/999/context")

    # Check response
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"] == "Conversation not found"
