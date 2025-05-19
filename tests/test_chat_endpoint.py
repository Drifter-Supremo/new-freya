"""
test_chat_endpoint.py - Test the chat completions endpoint
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from uuid import UUID

from app.api.routes.chat import router
from app.core.db import SessionLocal


class TestChatEndpoint:
    """Test chat completions endpoint functionality."""
    
    def test_create_chat_completion_success(self, db_session, test_user):
        """Test successful chat completion creation."""
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        # Prepare test request
        request_data = {
            "messages": [
                {"role": "user", "content": "Hello Freya, how are you today?"}
            ],
            "user_id": str(test_user.id),
            "model": "ft:gpt-4.1-mini-2025-04-14:gorlea-industries:freya:BULkCmxj",
            "temperature": 1.0,
            "max_tokens": 800,
            "stream": False
        }
        
        # Mock OpenAI response
        mock_completion = Mock()
        mock_completion.choices = [
            Mock(message=Mock(content="I'm doing well, thank you for asking!"))
        ]
        mock_completion.usage = Mock(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150
        )
        
        with patch('app.services.openai_service.OpenAIService.create_chat_completion') as mock_openai:
            mock_openai.return_value = mock_completion
            
            # Make request
            response = client.post("/chat/completions", json=request_data)
            
            # Assert response
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["object"] == "chat.completion"
            assert response_data["model"] == request_data["model"]
            assert len(response_data["choices"]) == 1
            assert response_data["choices"][0]["message"]["role"] == "assistant"
            assert response_data["choices"][0]["message"]["content"] == "I'm doing well, thank you for asking!"
    
    def test_create_chat_completion_invalid_user(self, db_session):
        """Test chat completion with invalid user ID."""
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        # Prepare test request with invalid user ID
        request_data = {
            "messages": [
                {"role": "user", "content": "Hello Freya!"}
            ],
            "user_id": "00000000-0000-0000-0000-000000000000",
            "model": "ft:gpt-4.1-mini-2025-04-14:gorlea-industries:freya:BULkCmxj",
            "temperature": 1.0,
            "max_tokens": 800,
            "stream": False
        }
        
        # Make request
        response = client.post("/chat/completions", json=request_data)
        
        # Assert error response
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"
    
    def test_create_chat_completion_empty_messages(self, db_session, test_user):
        """Test chat completion with empty messages list."""
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        # Prepare test request with empty messages
        request_data = {
            "messages": [],
            "user_id": str(test_user.id),
            "model": "ft:gpt-4.1-mini-2025-04-14:gorlea-industries:freya:BULkCmxj",
            "temperature": 1.0,
            "max_tokens": 800,
            "stream": False
        }
        
        # Make request
        response = client.post("/chat/completions", json=request_data)
        
        # Assert validation error
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_create_chat_completion_invalid_temperature(self, db_session, test_user):
        """Test chat completion with invalid temperature."""
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        # Prepare test request with invalid temperature
        request_data = {
            "messages": [
                {"role": "user", "content": "Hello Freya!"}
            ],
            "user_id": str(test_user.id),
            "model": "ft:gpt-4.1-mini-2025-04-14:gorlea-industries:freya:BULkCmxj",
            "temperature": 3.0,  # Invalid: must be between 0 and 2
            "max_tokens": 800,
            "stream": False
        }
        
        # Make request
        response = client.post("/chat/completions", json=request_data)
        
        # Assert validation error
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_create_chat_completion_with_existing_conversation(self, db_session, test_user, test_conversation):
        """Test chat completion with existing conversation."""
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        # Prepare test request with existing conversation
        request_data = {
            "messages": [
                {"role": "user", "content": "Remember when we talked about Python?"},
                {"role": "assistant", "content": "Yes, I remember discussing Python with you."},
                {"role": "user", "content": "What did I say about it?"}
            ],
            "user_id": str(test_user.id),
            "conversation_id": str(test_conversation.id),
            "model": "ft:gpt-4.1-mini-2025-04-14:gorlea-industries:freya:BULkCmxj",
            "temperature": 1.0,
            "max_tokens": 800,
            "stream": False
        }
        
        # Mock OpenAI response
        mock_completion = Mock()
        mock_completion.choices = [
            Mock(message=Mock(content="You mentioned that you enjoy Python's simplicity and readability."))
        ]
        mock_completion.usage = Mock(
            prompt_tokens=150,
            completion_tokens=75,
            total_tokens=225
        )
        
        with patch('app.services.openai_service.OpenAIService.create_chat_completion') as mock_openai:
            mock_openai.return_value = mock_completion
            
            # Make request
            response = client.post("/chat/completions", json=request_data)
            
            # Assert response
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["id"] == str(test_conversation.id)
            assert response_data["choices"][0]["message"]["content"] == "You mentioned that you enjoy Python's simplicity and readability."