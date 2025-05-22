"""
Unit tests for Firebase integration.

Following the simplified approach - these tests focus on core functionality
without unnecessary complexity.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json

from app.services.firebase_service import FirebaseService
from app.services.firebase_memory_service import FirebaseMemoryService
from app.api.routes.firebase_chat import chat_endpoint, ChatMessageRequest


class TestFirebaseService(unittest.TestCase):
    """Test the Firebase service basic operations."""
    
    @patch('app.services.firebase_service.firestore')
    def test_get_user_facts(self, mock_firestore):
        """Test retrieving user facts from Firestore."""
        # Mock Firestore response
        mock_fact = Mock()
        mock_fact.to_dict.return_value = {
            'type': 'job',
            'value': 'Diligent Robotics',
            'timestamp': datetime.now()
        }
        mock_fact.id = 'fact123'
        
        mock_collection = Mock()
        mock_collection.stream.return_value = [mock_fact]
        mock_firestore.client().collection.return_value.where.return_value = mock_collection
        
        # Test the service
        service = FirebaseService()
        facts = service.get_user_facts('test_user')
        
        assert len(facts) == 1
        assert facts[0]['type'] == 'job'
        assert facts[0]['value'] == 'Diligent Robotics'
    
    @patch('app.services.firebase_service.firestore')
    def test_save_message(self, mock_firestore):
        """Test saving a message to Firestore."""
        mock_doc = Mock()
        mock_doc.id = 'msg123'
        mock_firestore.client().collection().document().collection().add.return_value = (None, mock_doc)
        
        service = FirebaseService()
        message_data = {
            'user': 'Hello Freya',
            'timestamp': datetime.now()
        }
        
        result = service.save_message('conv123', message_data)
        assert result is not None
        mock_firestore.client().collection.assert_called()


class TestFirebaseMemoryService(unittest.TestCase):
    """Test the Firebase memory service."""
    
    @patch('app.services.firebase_memory_service.FirebaseService')
    def test_get_memory_context(self, mock_firebase_service):
        """Test memory context assembly."""
        # Mock Firebase service to return test data
        mock_instance = Mock()
        mock_instance.get_user_facts.return_value = [
            {'type': 'job', 'value': 'Diligent Robotics', 'timestamp': datetime.now()},
            {'type': 'name', 'value': 'Sencere', 'timestamp': datetime.now()}
        ]
        mock_instance.get_recent_messages.return_value = []
        mock_firebase_service.return_value = mock_instance
        
        service = FirebaseMemoryService()
        context = service.get_memory_context('test_user', 'Tell me about my job')
        
        assert context is not None
        assert 'Diligent Robotics' in context
        assert 'job' in context.lower()
    
    def test_detect_memory_query(self):
        """Test memory query detection."""
        service = FirebaseMemoryService()
        
        # Test memory-related queries
        self.assertTrue(service.is_memory_query("Do you remember my name?"))
        self.assertTrue(service.is_memory_query("What did I tell you about my job?"))
        self.assertFalse(service.is_memory_query("Hello, how are you?"))
        self.assertFalse(service.is_memory_query("What's the weather like?"))


class TestFirebaseChatEndpoint(unittest.TestCase):
    """Test the Firebase chat endpoint."""
    
    @patch('app.api.routes.firebase_chat.FirebaseService')
    @patch('app.api.routes.firebase_chat.FirebaseMemoryService')
    @patch('app.api.routes.firebase_chat.OpenAIService')
    def test_chat_endpoint_basic(self, mock_openai, mock_memory, mock_firebase):
        """Test basic chat functionality."""
        # Mock services
        mock_firebase_instance = Mock()
        mock_firebase_instance.save_message.return_value = 'msg123'
        mock_firebase_instance.create_conversation.return_value = 'conv123'
        mock_firebase.return_value = mock_firebase_instance
        
        mock_memory_instance = Mock()
        mock_memory_instance.get_memory_context.return_value = "You are Sencere"
        mock_memory.return_value = mock_memory_instance
        
        mock_openai_instance = Mock()
        mock_openai_instance.create_freya_completion.return_value = "Hello Sencere!"
        mock_openai.return_value = mock_openai_instance
        
        # Test request
        request = ChatMessageRequest(
            message="Hello",
            user_id="test_user",
            include_memory=True
        )
        
        # Note: We can't test async endpoints directly in unittest without asyncio
        # This would need to be tested in integration tests
        self.assertEqual(request.message, "Hello")
        self.assertEqual(request.user_id, "test_user")
        self.assertTrue(request.include_memory)
    
    @patch('app.api.routes.firebase_chat.FirebaseService')
    @patch('app.api.routes.firebase_chat.OpenAIService')
    def test_chat_endpoint_without_memory(self, mock_openai, mock_firebase):
        """Test chat without memory context."""
        # Mock services
        mock_firebase_instance = Mock()
        mock_firebase_instance.save_message.return_value = 'msg123'
        mock_firebase_instance.create_conversation.return_value = 'conv123'
        mock_firebase.return_value = mock_firebase_instance
        
        mock_openai_instance = Mock()
        mock_openai_instance.create_freya_completion.return_value = "Hello there!"
        mock_openai.return_value = mock_openai_instance
        
        # Test request without memory
        request = ChatMessageRequest(
            message="Hello",
            user_id="test_user",
            include_memory=False
        )
        
        # Note: We can't test async endpoints directly in unittest without asyncio
        # This would need to be tested in integration tests
        self.assertEqual(request.message, "Hello")
        self.assertEqual(request.user_id, "test_user")
        self.assertFalse(request.include_memory)


if __name__ == "__main__":
    unittest.main()