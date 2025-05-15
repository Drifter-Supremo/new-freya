"""
openai_service.py - Service for handling OpenAI API interactions
"""
import os
import logging
import time
from typing import Dict, List, Optional, Union, Any, Generator

from openai import OpenAI, APIError, RateLimitError, APIConnectionError, InternalServerError
from openai.types.chat import ChatCompletion, ChatCompletionMessage, ChatCompletionChunk
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam

from app.core.config import OPENAI_API_KEY, logger
from app.core.openai_constants import (
    DEFAULT_MODEL, DEFAULT_TEMPERATURE, MAX_TOKENS, MAX_RETRIES,
    RETRY_DELAY_SECONDS, BACKOFF_FACTOR, ROLE_SYSTEM, ROLE_USER, ROLE_ASSISTANT,
    FREYA_SYSTEM_PROMPT
)


class OpenAIService:
    """
    Service for interacting with the OpenAI API.
    Handles API calls, retries, and error handling.
    """

    def __init__(self, api_key: str = OPENAI_API_KEY):
        """Initialize the OpenAI service with API key."""
        self.client = OpenAI(api_key=api_key)
        self.logger = logger

    def create_chat_completion(
        self,
        messages: List[ChatCompletionMessageParam],
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = MAX_TOKENS,
        stream: bool = False,
    ) -> Union[ChatCompletion, ChatCompletionChunk]:
        """
        Create a chat completion using the OpenAI API.
        
        Args:
            messages: List of message objects in the conversation history
            model: OpenAI model ID to use
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            
        Returns:
            ChatCompletion object from OpenAI API response
            
        Raises:
            Exception: If the API call fails after retries
        """
        retries = 0
        delay = RETRY_DELAY_SECONDS
        
        while retries <= MAX_RETRIES:
            try:
                # Log the request (excluding potentially sensitive message content)
                self.logger.info(
                    f"Creating chat completion with model={model}, temp={temperature}, "
                    f"max_tokens={max_tokens}, stream={stream}, messages_count={len(messages)}"
                )
                
                # Make the API call
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=stream,
                )
                
                # Log success
                self.logger.info(f"Chat completion successful: {type(response)}")
                return response
                
            except RateLimitError as e:
                retries += 1
                if retries > MAX_RETRIES:
                    self.logger.error(f"Rate limit exceeded after {MAX_RETRIES} retries: {str(e)}")
                    raise
                
                self.logger.warning(f"Rate limit error, retrying in {delay}s ({retries}/{MAX_RETRIES}): {str(e)}")
                time.sleep(delay)
                delay *= BACKOFF_FACTOR  # Exponential backoff
                
            except (APIError, APIConnectionError, InternalServerError) as e:
                retries += 1
                if retries > MAX_RETRIES:
                    self.logger.error(f"API error after {MAX_RETRIES} retries: {str(e)}")
                    raise
                
                self.logger.warning(f"API error, retrying in {delay}s ({retries}/{MAX_RETRIES}): {str(e)}")
                time.sleep(delay)
                delay *= BACKOFF_FACTOR  # Exponential backoff
                
            except Exception as e:
                self.logger.error(f"Unexpected error in OpenAI API call: {str(e)}")
                raise

    def handle_streaming_response(self, streaming_response) -> Generator[str, None, str]:
        """
        Process a streaming response from the OpenAI API.
        
        Args:
            streaming_response: The streaming response from OpenAI
            
        Returns:
            Generator yielding content chunks as they arrive
            Final return value is the complete combined response
        """
        full_response = ""
        
        try:
            for chunk in streaming_response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content
        except Exception as e:
            self.logger.error(f"Error processing streaming response: {str(e)}")
            raise
        
        return full_response

    def create_freya_chat_completion(
        self,
        user_message: str,
        conversation_history: List[ChatCompletionMessageParam] = None,
        memory_context: Optional[str] = None,
        system_prompt: Optional[str] = FREYA_SYSTEM_PROMPT,
        stream: bool = False,
    ) -> Union[ChatCompletion, Generator[str, None, str]]:
        """
        Create a chat completion specifically for Freya, with her system prompt.
        
        Args:
            user_message: The latest user message
            conversation_history: Previous messages in the conversation
            memory_context: Optional memory context to inject into system prompt
            system_prompt: Optional custom system prompt (defaults to Freya's)
            stream: Whether to stream the response
            
        Returns:
            ChatCompletion or a generator of content chunks if streaming
        """
        # Start with system message
        messages = self.format_system_prompt(system_prompt, memory_context)
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add the current user message
        messages.append({"role": ROLE_USER, "content": user_message})
        
        # Get the completion
        response = self.create_chat_completion(
            messages=messages,
            model=DEFAULT_MODEL,
            temperature=DEFAULT_TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=stream,
        )
        
        # Handle streaming vs. non-streaming responses
        if stream:
            return self.handle_streaming_response(response)
        return response
        
    def get_message_content(self, completion: ChatCompletion) -> str:
        """
        Extract the message content from a chat completion response.
        
        Args:
            completion: ChatCompletion object from OpenAI API
            
        Returns:
            The content of the assistant's message
        """
        if not completion.choices or not completion.choices[0].message:
            self.logger.error("Invalid completion format: no choices or message")
            return ""
            
        return completion.choices[0].message.content or ""
        
    def format_system_prompt(self, system_prompt: str, memory_context: Optional[str] = None) -> List[ChatCompletionMessageParam]:
        """
        Format the system prompt with memory context if provided.
        
        Args:
            system_prompt: The base system prompt
            memory_context: Optional memory context to inject
            
        Returns:
            List containing the formatted system message
        """
        formatted_prompt = system_prompt
        
        if memory_context and memory_context.strip():
            # Add memory context to system prompt
            formatted_prompt += f"\n\n## Memory Context\n{memory_context}"
        
        # Format as system message for API
        return [{"role": ROLE_SYSTEM, "content": formatted_prompt}]
