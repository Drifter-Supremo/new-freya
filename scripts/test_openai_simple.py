"""
Simple tests for OpenAI service with proper mocking
"""
import unittest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the project root to Python path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

# Import the service to test
from app.services.openai_service import OpenAIService


class TestOpenAIServiceSimple(unittest.TestCase):
    """Test the OpenAI service wrapper with proper mocking."""
    
    @patch('app.services.openai_service.OpenAI')
    def test_basic_functionality(self, mock_openai_class):
        """Test basic functionality of the OpenAI service."""
        # Set up mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Create a mock completion response
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Hello, I'm Freya!"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        # Configure the mock to return our mock_response
        mock_client.chat.completions.create.return_value = mock_response
        
        # Create service and test
        service = OpenAIService(api_key="test_key")
        user_message = "Hello there"
        completion = service.create_freya_chat_completion(user_message=user_message)
        
        # Verify the response content
        content = service.get_message_content(completion)
        self.assertEqual(content, "Hello, I'm Freya!")


if __name__ == "__main__":
    unittest.main()
