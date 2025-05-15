"""
Example usage of the OpenAI service wrapper
"""
import sys
import os
import asyncio
from pathlib import Path

# Add the project root directory to Python path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from app.services.openai_service import OpenAIService
from app.core.config import OPENAI_API_KEY


async def main():
    # Create an instance of the OpenAI service
    openai_service = OpenAIService(api_key=OPENAI_API_KEY)
    
    # Test with a simple user message
    user_message = "Hello Freya, how are you feeling today?"
    print(f"User: {user_message}")
    
    # Get response from OpenAI API
    completion = openai_service.create_freya_chat_completion(user_message=user_message)
    
    # Extract and print the message content
    content = openai_service.get_message_content(completion)
    print(f"Freya: {content}")
    
    # Test with a memory-related query
    memory_context = "User is named Sencere. User works as a software developer. User lives in Seattle."
    user_message = "Do you remember what I do for work?"
    print(f"\nUser: {user_message}")
    
    # Get response with memory context
    completion = openai_service.create_freya_chat_completion(
        user_message=user_message,
        memory_context=memory_context
    )
    
    # Extract and print the message content
    content = openai_service.get_message_content(completion)
    print(f"Freya: {content}")
    
    # Test with a streaming response
    user_message = "Tell me about your memories of Saturn."
    print(f"\nUser: {user_message}")
    print("Freya (streaming): ", end="", flush=True)
    
    # Process the streaming response
    streaming_generator = openai_service.create_freya_chat_completion(
        user_message=user_message,
        stream=True
    )
    
    # Print each chunk as it arrives
    async for chunk in async_generator_from_sync(streaming_generator):
        print(chunk, end="", flush=True)
    print()  # Add newline at the end


async def async_generator_from_sync(sync_gen):
    """Convert a synchronous generator to an asynchronous one."""
    for item in sync_gen:
        yield item


if __name__ == "__main__":
    asyncio.run(main())
