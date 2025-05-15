"""
Unit tests for the OpenAI service wrapper
"""
import unittest
from unittest.mock import patch, MagicMock, Mock

from app.services.openai_service import OpenAIService
from app.core.openai_constants import DEFAULT_MODEL, DEFAULT_TEMPERATURE, MAX_TOKENS


class TestOpenAIService(unittest.TestCase):
    """Test the OpenAI service wrapper."""

    def setUp(self):
        """Set up test fixtures, if any."""
        # Use a non-existent API key for tests
        self.openai_service = OpenAIService(api_key="test_key")
        
    @patch('app.services.openai_service.OpenAI')
    def test_init(self, mock_openai):
        """Test service initialization."""
        service = OpenAIService(api_key="test_key")
        mock_openai.assert_called_once_with(api_key="test_key")
        
    @patch('app.services.openai_service.OpenAI')
    def test_create_chat_completion(self, mock_openai):
        """Test creating a chat completion."""
        # Mock the OpenAI client and its chat.completions.create method
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_response = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        
        # Create test data
        messages = [
            {"role": "system", "content": "You are Freya, an AI assistant."},
            {"role": "user", "content": "Hello, how are you?"}
        ]
        
        # Call the method
        response = self.openai_service.create_chat_completion(messages)
        
        # Assert the OpenAI client was called correctly
        mock_client.chat.completions.create.assert_called_once_with(
            model=DEFAULT_MODEL,
            messages=messages,
            temperature=DEFAULT_TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False
        )
        
        # Assert the response is returned correctly
        self.assertEqual(response, mock_response)
        
    @patch('app.services.openai_service.OpenAI')
    @patch('app.services.openai_service.time.sleep')
    def test_retry_on_rate_limit(self, mock_sleep, mock_openai):
        """Test retry behavior on rate limit errors."""
        # Mock the OpenAI client
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Set up the client to raise a rate limit error once, then succeed
        from openai import RateLimitError
        mock_client.chat.completions.create.side_effect = [
            RateLimitError("Rate limit exceeded", response=None, body=None),
            MagicMock()  # Success on second try
        ]
        
        # Create test data
        messages = [{"role": "user", "content": "Test message"}]
        
        # Call the method
        self.openai_service.create_chat_completion(messages)
        
        # Assert sleep was called once for the retry
        mock_sleep.assert_called_once()
        
        # Assert create was called twice (initial + retry)
        self.assertEqual(mock_client.chat.completions.create.call_count, 2)
        
    def test_format_system_prompt(self):
        """Test formatting system prompt with memory context."""
        # Test with no memory context
        base_prompt = "You are Freya, an AI assistant."
        result = self.openai_service.format_system_prompt(base_prompt)
        self.assertEqual(result, [{"role": "system", "content": base_prompt}])
        
        # Test with memory context
        memory_context = "User likes pizza. User lives in Seattle."
        expected = [{"role": "system", "content": f"{base_prompt}\n\n## Memory Context\n{memory_context}"}]
        result = self.openai_service.format_system_prompt(base_prompt, memory_context)
        self.assertEqual(result, expected)
        
    @patch('app.services.openai_service.OpenAI')
    def test_create_freya_chat_completion(self, mock_openai):
        """Test creating a Freya-specific chat completion."""
        # Mock the OpenAI client
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_response = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        
        # Test with basic parameters
        user_message = "Hello Freya"
        response = self.openai_service.create_freya_chat_completion(user_message=user_message)
        
        # Verify the correct messages were sent
        call_args = mock_client.chat.completions.create.call_args[1]
        messages = call_args["messages"]
        
        # Check system message and user message
        self.assertEqual(messages[0]["role"], "system")
        self.assertTrue("F.R.E.Y.A." in messages[0]["content"])
        self.assertEqual(messages[1]["role"], "user")
        self.assertEqual(messages[1]["content"], user_message)
        
        # Check model and other parameters
        self.assertEqual(call_args["model"], DEFAULT_MODEL)
        self.assertEqual(call_args["temperature"], DEFAULT_TEMPERATURE)
        self.assertEqual(call_args["max_tokens"], MAX_TOKENS)
        self.assertEqual(call_args["stream"], False)
        
        # Verify the response is returned
        self.assertEqual(response, mock_response)
        
    @patch('app.services.openai_service.OpenAI')
    def test_freya_chat_with_memory_context(self, mock_openai):
        """Test creating a Freya chat completion with memory context."""
        # Mock the OpenAI client
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_response = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        
        # Test with memory context
        user_message = "Do you remember my name?"
        memory_context = "User is named Sencere. User works as a developer."
        
        response = self.openai_service.create_freya_chat_completion(
            user_message=user_message,
            memory_context=memory_context
        )
        
        # Verify the correct messages were sent
        call_args = mock_client.chat.completions.create.call_args[1]
        messages = call_args["messages"]
        
        # Check that system message includes both prompt and memory context
        self.assertEqual(messages[0]["role"], "system")
        self.assertTrue("F.R.E.Y.A." in messages[0]["content"])
        self.assertTrue("Memory Context" in messages[0]["content"])
        self.assertTrue("User is named Sencere" in messages[0]["content"])
        
        # Check user message
        self.assertEqual(messages[1]["role"], "user")
        self.assertEqual(messages[1]["content"], user_message)
        
    @patch('app.services.openai_service.OpenAI')
    def test_freya_chat_with_conversation_history(self, mock_openai):
        """Test creating a Freya chat completion with conversation history."""
        # Mock the OpenAI client
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_response = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        
        # Test with conversation history
        user_message = "And what about our earlier discussion?"
        conversation_history = [
            {"role": "user", "content": "Hello Freya"},
            {"role": "assistant", "content": "Hi there! How can I help you today?"},
            {"role": "user", "content": "Let's talk about AI ethics"},
            {"role": "assistant", "content": "That's an interesting topic. What aspect interests you?"}
        ]
        
        response = self.openai_service.create_freya_chat_completion(
            user_message=user_message,
            conversation_history=conversation_history
        )
        
        # Verify the correct messages were sent
        call_args = mock_client.chat.completions.create.call_args[1]
        messages = call_args["messages"]
        
        # Check that all messages are included in the right order
        self.assertEqual(len(messages), 6)  # system + 4 history + current
        self.assertEqual(messages[0]["role"], "system")  # System message first
        
        # Check conversation history
        for i in range(4):
            self.assertEqual(messages[i+1]["role"], conversation_history[i]["role"])
            self.assertEqual(messages[i+1]["content"], conversation_history[i]["content"])
        
        # Check current user message is last
        self.assertEqual(messages[5]["role"], "user")
        self.assertEqual(messages[5]["content"], user_message)
        
    def test_get_message_content(self):
        """Test extracting message content from ChatCompletion."""
        # Create a mock ChatCompletion with message content
        mock_completion = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Hello, I'm Freya!"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_completion.choices = [mock_choice]
        
        # Test content extraction
        content = self.openai_service.get_message_content(mock_completion)
        self.assertEqual(content, "Hello, I'm Freya!")
        
        # Test with empty content
        mock_message.content = ""
        content = self.openai_service.get_message_content(mock_completion)
        self.assertEqual(content, "")
        
        # Test with no message
        mock_completion.choices = []
        content = self.openai_service.get_message_content(mock_completion)
        self.assertEqual(content, "")


if __name__ == "__main__":
    unittest.main()
