"""
Simple example of using the OpenAI service to get a real response from Freya
"""
import sys
import os
import json
from pathlib import Path

# Add the project root to Python path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

# Import the service
from app.services.openai_service import OpenAIService
from app.core.config import OPENAI_API_KEY

def main():
    # Create the OpenAI service with the real API key
    print(f"Using API key: {OPENAI_API_KEY[:5]}...")
    service = OpenAIService(api_key=OPENAI_API_KEY)
    
    # Simple user message
    user_message = "Hello Freya, how are you today?"
    print(f"User: {user_message}")
    
    try:
        # Get a response using Freya's system prompt
        completion = service.create_freya_chat_completion(user_message=user_message)
        
        # Print the raw completion for debugging
        print("\nRaw completion:")
        print(f"ID: {completion.id}")
        print(f"Model: {completion.model}")
        print(f"Usage: {completion.usage}")
        
        # Extract the content
        content = service.get_message_content(completion)
        print(f"\nFreya: {content}")
        
        # Try with some memory context
        memory_context = "User's name is Sencere. User is a software developer. User lives in Seattle."
        user_message = "Do you remember what I do for work?"
        print(f"\nUser: {user_message}")
        
        completion = service.create_freya_chat_completion(
            user_message=user_message,
            memory_context=memory_context
        )
        
        # Print the raw completion for debugging
        print("\nRaw completion:")
        print(f"ID: {completion.id}")
        print(f"Model: {completion.model}")
        print(f"Usage: {completion.usage}")
        
        content = service.get_message_content(completion)
        print(f"\nFreya: {content}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
