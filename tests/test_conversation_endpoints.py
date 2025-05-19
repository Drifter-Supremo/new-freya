"""
test_conversation_endpoints.py - Unit tests for conversation management endpoints
"""
import pytest
from datetime import datetime, timezone
from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.repository.user import UserRepository
from app.repository.conversation import ConversationRepository
from app.repository.message import MessageRepository


@pytest.fixture
def client(db_session):
    """Create a test client with database session override"""
    from app.core.db import get_db
    
    # Override the get_db dependency
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield TestClient(app)
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user_repo = UserRepository(db_session)
    unique_id = uuid4().hex[:8]
    user_data = {
        "username": f"testuser_{unique_id}",
        "email": f"test_{unique_id}@example.com",
        "hashed_password": "dummy_password_hash"
    }
    return user_repo.create(user_data)


@pytest.fixture
def test_conversation(db_session, test_user):
    """Create a test conversation"""
    conv_repo = ConversationRepository(db_session)
    conv_data = {
        "user_id": test_user.id,
        "started_at": datetime.now(timezone.utc)
    }
    return conv_repo.create(conv_data)


@pytest.fixture
def test_message(db_session, test_conversation, test_user):
    """Create a test message"""
    msg_repo = MessageRepository(db_session)
    msg_data = {
        "conversation_id": test_conversation.id,
        "user_id": test_user.id,
        "role": "user",
        "content": "Test message for search",
        "timestamp": datetime.now(timezone.utc)
    }
    return msg_repo.create(msg_data)


class TestConversationEndpoints:
    """Test conversation management endpoints"""
    
    def test_create_conversation(self, client, test_user, db_session):
        """Test POST /conversations/ endpoint"""
        user_id = test_user.id  # Get the ID before the request
        response = client.post(f"/conversations/?user_id={user_id}")
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert data["user_id"] == user_id
        assert "started_at" in data
        
        # Verify conversation was created in database
        conv_repo = ConversationRepository(db_session)
        conversation = conv_repo.get(data["id"])
        assert conversation is not None
        assert conversation.user_id == user_id
    
    def test_get_recent_conversations(self, client, test_user, test_conversation, test_message):
        """Test GET /conversations/{user_id}/recent endpoint"""
        user_id = test_user.id
        conversation_id = test_conversation.id
        response = client.get(f"/conversations/{user_id}/recent?limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # Should have at least the test conversation (now it has a message)
        assert len(data) >= 1
        
        # Verify the test conversation is in the results
        conversation_ids = [conv["id"] for conv in data]
        assert conversation_id in conversation_ids
    
    def test_get_conversation_messages(self, client, test_conversation, test_message):
        """Test GET /conversations/{conversation_id}/messages endpoint"""
        conversation_id = test_conversation.id
        message_id = test_message.id
        response = client.get(
            f"/conversations/{conversation_id}/messages?limit=10"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # Should have at least the test message
        assert len(data) >= 1
        
        # Verify the test message is in the results
        message_ids = [msg["id"] for msg in data]
        assert message_id in message_ids
    
    def test_search_conversations(self, client, test_user, test_message):
        """Test GET /conversations/{user_id}/search endpoint"""
        user_id = test_user.id
        message_id = test_message.id
        # Search for the test message content
        response = client.get(
            f"/conversations/{user_id}/search?query=test&limit=10"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # Should find at least the test message
        assert len(data) >= 1
        
        # Verify the test message is in the results
        message_ids = [msg["id"] for msg in data]
        assert message_id in message_ids
        
        # Verify rank is included
        assert all("rank" in msg for msg in data)
    
    def test_get_conversation_context(self, client, test_conversation, test_message):
        """Test GET /conversations/{conversation_id}/context endpoint"""
        conversation_id = test_conversation.id
        response = client.get(
            f"/conversations/{conversation_id}/context?message_limit=5"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "conversation_id" in data
        assert "messages" in data
        assert data["conversation_id"] == conversation_id
        
        # Should have the test message in context
        assert len(data["messages"]) >= 1
    
    def test_delete_conversation(self, client, test_conversation, test_user):
        """Test DELETE /conversations/{conversation_id} endpoint"""
        conversation_id = test_conversation.id
        user_id = test_user.id
        response = client.delete(
            f"/conversations/{conversation_id}?user_id={user_id}"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert f"Conversation {test_conversation.id} deleted successfully" in data["message"]
    
    def test_delete_conversation_unauthorized(self, client, test_conversation, test_user):
        """Test DELETE with wrong user ID"""
        conversation_id = test_conversation.id
        wrong_user_id = test_user.id + 999999  # Make sure this user doesn't exist
        response = client.delete(
            f"/conversations/{conversation_id}?user_id={wrong_user_id}"
        )
        assert response.status_code == 403
        
        data = response.json()
        assert "Not authorized to delete this conversation" in data["error"]
    
    def test_delete_nonexistent_conversation(self, client, test_user):
        """Test DELETE with non-existent conversation"""
        user_id = test_user.id
        fake_conversation_id = 99999
        response = client.delete(
            f"/conversations/{fake_conversation_id}?user_id={user_id}"
        )
        assert response.status_code == 404
        
        data = response.json()
        assert "Conversation not found" in data["error"]


# Edge cases and error handling
class TestConversationEndpointsEdgeCases:
    """Test edge cases for conversation endpoints"""
    
    def test_get_messages_nonexistent_conversation(self, client):
        """Test getting messages for non-existent conversation"""
        fake_conversation_id = 99999
        response = client.get(f"/conversations/{fake_conversation_id}/messages")
        assert response.status_code == 404
        
        data = response.json()
        assert "Conversation not found" in data["error"]
    
    def test_search_with_empty_query(self, client, test_user):
        """Test search with empty query string"""
        user_id = test_user.id
        response = client.get(f"/conversations/{user_id}/search?query=")
        assert response.status_code == 422  # Validation error
    
    def test_get_context_nonexistent_conversation(self, client):
        """Test getting context for non-existent conversation"""
        fake_conversation_id = 99999
        response = client.get(f"/conversations/{fake_conversation_id}/context")
        # This should return 404 because of our error handling
        assert response.status_code == 404