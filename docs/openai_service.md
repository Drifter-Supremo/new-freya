# OpenAI Service Wrapper

This module provides a service wrapper for interacting with the OpenAI API, specifically configured for the Freya AI Companion backend.

## Features

- Handles API authentication and request formatting
- Implements retry logic with exponential backoff for rate limits and API errors
- Supports both streaming and non-streaming responses
- Provides formatted system prompts with memory context integration
- Includes specialized methods for Freya-specific chat completions

## Usage Examples

### Basic Chat Completion

```python
from app.services.openai_service import OpenAIService
from app.core.config import OPENAI_API_KEY

# Initialize the service
openai_service = OpenAIService(api_key=OPENAI_API_KEY)

# Create a simple message list
messages = [
    {"role": "system", "content": "You are Freya, an AI assistant."},
    {"role": "user", "content": "Hello, how are you?"}
]

# Get a completion
completion = openai_service.create_chat_completion(messages)

# Extract the response content
response_text = openai_service.get_message_content(completion)
print(response_text)
```

### Using the Freya-Specific Method

```python
from app.services.openai_service import OpenAIService
from app.core.config import OPENAI_API_KEY

# Initialize the service
openai_service = OpenAIService(api_key=OPENAI_API_KEY)

# Create a chat completion with Freya's persona and memory
user_message = "Do you remember where I live?"
memory_context = "User is named Sencere. User lives in Seattle."

completion = openai_service.create_freya_chat_completion(
    user_message=user_message,
    memory_context=memory_context
)

# Extract the response
response_text = openai_service.get_message_content(completion)
print(response_text)
```

### Handling Streaming Responses

```python
from app.services.openai_service import OpenAIService
from app.core.config import OPENAI_API_KEY

# Initialize the service
openai_service = OpenAIService(api_key=OPENAI_API_KEY)

# Create a streaming completion
user_message = "Tell me about Saturn."

# Get a streaming generator
streaming_response = openai_service.create_freya_chat_completion(
    user_message=user_message,
    stream=True
)

# Process each chunk as it arrives
for chunk in streaming_response:
    print(chunk, end="", flush=True)
```

## Configuration

The service uses the following configuration values from `openai_constants.py`:

- `DEFAULT_MODEL`: The default OpenAI model to use (fine-tuned GPT-4.1 mini for Freya)
- `DEFAULT_TEMPERATURE`: The default temperature setting (1.0)
- `MAX_TOKENS`: Maximum tokens to generate in a response (800)
- `MAX_RETRIES`: Maximum retry attempts for API errors (3)
- `RETRY_DELAY_SECONDS`: Initial delay between retries (2 seconds)
- `BACKOFF_FACTOR`: Exponential backoff multiplier for retries (2)
- `FREYA_SYSTEM_PROMPT`: Freya's default system prompt

## Error Handling

The service implements comprehensive error handling with retries for common API issues:

1. Rate limit errors: Retries with exponential backoff
2. API connection errors: Retries with exponential backoff
3. Internal server errors: Retries with exponential backoff
4. Other errors: Logged and re-raised

## Testing

Unit tests are available in `tests/test_openai_service.py` and cover:

- Service initialization
- Creating chat completions
- Retry behavior
- System prompt formatting
- Memory context integration
- Conversation history handling
- Response content extraction

A working example is also provided in `examples/openai_service_demo.py`.
