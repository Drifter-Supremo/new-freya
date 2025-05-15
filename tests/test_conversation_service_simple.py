"""
test_conversation_service_simple.py - Simplified tests for conversation history service
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

class TestConversationHistoryServiceSimple:
    @pytest.fixture
    def mock_db_session(self):
        """Create a simple mock DB session."""
        return MagicMock()
    
    @pytest.fixture
    def mock_conversation_repo(self):
        """Create a mock conversation repository."""
        with patch("app.repository.conversation.ConversationRepository") as mock:
            # Create an instance of the mock
            mock_instance = MagicMock()
            
            # Set up mock methods
            def mock_get(id):
                # Create a conversation mock
                for conv_data in TEST_CONVERSATIONS:
                    if conv_data["id"] == id:
                        conv = MagicMock(spec=Conversation)
                        for k, v in conv_data.items():
                            setattr(conv, k, v)
                        return conv
                return None
            
            # Assign mock methods
            mock_instance.get.side_effect = mock_get
            
            # Return the mock instance
            mock.return_value = mock_instance
            yield mock_instance
    
    @pytest.fixture
    def mock_message_repo(self):
        """Create a mock message repository."""
        with patch("app.repository.message.MessageRepository") as mock:
            # Create an instance of the mock
            mock_instance = MagicMock()
            yield mock_instance
    
    def test_format_messages_for_context(self, mock_db_session):
        """Test formatting messages for context."""
        # Create test messages
        messages = []
        for msg_data in TEST_MESSAGES:
            msg = MagicMock(spec=Message)
            for k, v in msg_data.items():
                setattr(msg, k, v)
            messages.append(msg)
        
        # Create service
        service = ConversationHistoryService(mock_db_session)
        
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
    
    def test_get_conversation_context(self, mock_db_session, mock_conversation_repo):
        """Test retrieving conversation context with mocked dependencies."""
        # Create a service with mocked get_conversation_history method
        service = ConversationHistoryService(mock_db_session)
        
        # Mock the get_conversation_history method
        mock_messages = []
        for msg_data in TEST_MESSAGES:
            if msg_data["conversation_id"] == 2:
                msg = MagicMock(spec=Message)
                for k, v in msg_data.items():
                    setattr(msg, k, v)
                mock_messages.append(msg)
        
        # Patch the get_conversation_history method
        with patch.object(service, 'get_conversation_history', return_value=mock_messages):
            # Get conversation context
            context = service.get_conversation_context(conversation_id=2, message_limit=3)
            
            # Assertions
            assert context["conversation_id"] == 2
            assert context["user_id"] == 1
            assert "started_at" in context
            assert "messages" in context
            assert isinstance(context["messages"], list)
            assert len(context["messages"]) <= 3  # Should respect the message_limit
