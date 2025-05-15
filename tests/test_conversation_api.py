"""
test_conversation_api.py - Tests for conversation API endpoints
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

@pytest.fixture
def mock_conversation_service():
    """Mock the ConversationHistoryService."""
    with patch("app.core.conversation_history_service.ConversationHistoryService") as mock:
        # Create an instance of the mock
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        
        # Set up mock methods
        def mock_get_recent_conversations(user_id, limit=5):
            # Create Conversation objects
            conversations = []
            for conv_data in TEST_CONVERSATIONS:
                conv = MagicMock(spec=Conversation)
                for k, v in conv_data.items():
                    setattr(conv, k, v)
                conversations.append(conv)
            return conversations[:limit]
        
        def mock_get_conversation_history(conversation_id, limit=20, skip=0):
            # Create Message objects
            messages = []
            for msg_data in TEST_MESSAGES:
                if msg_data["conversation_id"] == conversation_id:
                    msg = MagicMock(spec=Message)
                    for k, v in msg_data.items():
                        setattr(msg, k, v)
                    messages.append(msg)
            # Sort by timestamp (newest first)
            messages.sort(key=lambda x: x.timestamp, reverse=True)
            return messages[skip:skip+limit]
        
        def mock_get_recent_messages_across_conversations(user_id, limit=20, max_age_days=None):
            # Create Message objects
            messages = []
            for msg_data in TEST_MESSAGES:
                if msg_data["user_id"] == user_id:
                    # Apply max_age_days filter if specified
                    if max_age_days is not None:
                        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=max_age_days)
                        if msg_data["timestamp"] < cutoff_date:
                            continue
                    
                    msg = MagicMock(spec=Message)
                    for k, v in msg_data.items():
                        setattr(msg, k, v)
                    messages.append(msg)
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
            messages = []
            for msg_data in TEST_MESSAGES:
                if msg_data["conversation_id"] == conversation_id:
                    messages.append({
                        "id": msg_data["id"],
                        "content": msg_data["content"],
                        "timestamp": msg_data["timestamp"].isoformat(),
                        "user_id": msg_data["user_id"]
                    })
            
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
        
        yield mock_instance

@pytest.fixture
def mock_conversation_repo():
    """Mock the ConversationRepository."""
    with patch("app.repository.conversation.ConversationRepository") as mock:
        # Create an instance of the mock
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        
        # Set up mock methods
        def mock_get(id):
            # Check if conversation exists
            conv_exists = any(c["id"] == id for c in TEST_CONVERSATIONS)
            if not conv_exists:
                return None
            
            # Create Conversation object
            conv_data = next(c for c in TEST_CONVERSATIONS if c["id"] == id)
            conv = MagicMock(spec=Conversation)
            for k, v in conv_data.items():
                setattr(conv, k, v)
            return conv
        
        # Assign mock methods
        mock_instance.get.side_effect = mock_get
        
        yield mock_instance

def test_get_recent_conversations(mock_conversation_service, mock_conversation_repo):
    """Test GET /conversations/{user_id}/recent endpoint."""
    response = client.get(f"/conversations/{TEST_USER_ID}/recent")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3  # All test conversations
    
    # Check that conversations are returned in the expected format
    for conv in data:
        assert "id" in conv
        assert "user_id" in conv
        assert "started_at" in conv

def test_get_conversation_messages(mock_conversation_service, mock_conversation_repo):
    """Test GET /conversations/{conversation_id}/messages endpoint."""
    response = client.get(f"/conversations/{TEST_CONVERSATION_ID}/messages")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2  # Messages for conversation 1
    
    # Check that messages are returned in the expected format
    for msg in data:
        assert "id" in msg
        assert "conversation_id" in msg
        assert "user_id" in msg
        assert "content" in msg
        assert "timestamp" in msg

def test_get_conversation_messages_not_found(mock_conversation_service, mock_conversation_repo):
    """Test GET /conversations/{conversation_id}/messages with non-existent conversation."""
    # Set up mock to return None for non-existent conversation
    mock_conversation_repo.get.return_value = None
    
    response = client.get("/conversations/999/messages")
    
    # Check response
    assert response.status_code == 404
    assert "detail" in response.json()

def test_get_recent_messages(mock_conversation_service, mock_conversation_repo):
    """Test GET /conversations/{user_id}/recent-messages endpoint."""
    response = client.get(f"/conversations/{TEST_USER_ID}/recent-messages")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3  # All test messages
    
    # Check that messages are returned in the expected format
    for msg in data:
        assert "id" in msg
        assert "conversation_id" in msg
        assert "user_id" in msg
        assert "content" in msg
        assert "timestamp" in msg

def test_get_conversation_context(mock_conversation_service, mock_conversation_repo):
    """Test GET /conversations/{conversation_id}/context endpoint."""
    response = client.get(f"/conversations/{TEST_CONVERSATION_ID}/context")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    
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
    assert "detail" in response.json()
