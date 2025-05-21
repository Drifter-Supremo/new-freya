"""
event_dispatcher.py - Custom event dispatching service for frontend integration
"""
from typing import Dict, Any, Optional, List, Callable, Awaitable, AsyncGenerator
import json
import asyncio
from datetime import datetime
from fastapi import Request

from app.core.config import logger
from app.services.event_service import EventService


class EventDispatcher:
    """
    Service for managing and dispatching sequences of events to clients.
    Provides methods for dispatching custom events in the expected sequence
    and formatting data according to frontend requirements.
    """
    
    def __init__(self):
        """Initialize the event dispatcher"""
        self.event_service = EventService()
        
    async def dispatch_listening_event(self, client_queue: asyncio.Queue) -> None:
        """
        Dispatch a freya:listening event to the client.
        
        Args:
            client_queue: The asyncio queue to send events to
        """
        event = await self.event_service.create_listening_event()
        await client_queue.put(event)
        logger.info("Dispatched freya:listening event")
        
    async def dispatch_thinking_event(self, client_queue: asyncio.Queue) -> None:
        """
        Dispatch a freya:thinking event to the client.
        
        Args:
            client_queue: The asyncio queue to send events to
        """
        event = await self.event_service.create_thinking_event()
        await client_queue.put(event)
        logger.info("Dispatched freya:thinking event")
        
    async def dispatch_reply_event(self, client_queue: asyncio.Queue, message: str) -> None:
        """
        Dispatch a freya:reply event to the client.
        
        Args:
            client_queue: The asyncio queue to send events to
            message: The response message to include
        """
        event = await self.event_service.create_reply_event(message)
        await client_queue.put(event)
        logger.debug(f"Dispatched freya:reply event with message: {message[:30]}...")
        
    async def dispatch_error_event(self, client_queue: asyncio.Queue, error_message: str) -> None:
        """
        Dispatch an error event to the client.
        
        Args:
            client_queue: The asyncio queue to send events to
            error_message: The error message to include
        """
        logger.error(f"Creating error event with message: {error_message}")
        event = await self.event_service.format_sse("error", {"message": error_message})
        logger.error(f"Formatted error event: {event}")
        await client_queue.put(event)
        logger.error(f"Dispatched error event: {error_message}")
        
    async def dispatch_custom_event(
        self, 
        client_queue: asyncio.Queue, 
        event_type: str, 
        data: Any
    ) -> None:
        """
        Dispatch a custom event to the client.
        
        Args:
            client_queue: The asyncio queue to send events to
            event_type: The type of event to dispatch
            data: The data to include in the event
        """
        event = await self.event_service.format_sse(event_type, data)
        await client_queue.put(event)
        logger.info(f"Dispatched custom event: {event_type}")
        
    async def dispatch_chat_sequence(
        self,
        client_queue: asyncio.Queue,
        message_processor: Callable[[str], Awaitable[str]],
        user_message: str,
        thinking_delay: float = 1.0
    ) -> str:
        """
        Dispatch a complete chat sequence with proper event ordering:
        1. freya:listening
        2. freya:thinking (with optional delay)
        3. Process the message
        4. freya:reply
        
        Args:
            client_queue: The asyncio queue to send events to
            message_processor: An async function that processes the user message and returns a response
            user_message: The user's message to process
            thinking_delay: The delay in seconds after the thinking event (gives UI time to transition)
            
        Returns:
            The final response message from the message processor
        """
        try:
            # Send listening event immediately
            await self.dispatch_listening_event(client_queue)
            
            # Send thinking event
            await self.dispatch_thinking_event(client_queue)
            
            # Delay for a moment to give frontend time to transition
            await asyncio.sleep(thinking_delay)
            
            # Process the message with the provided function
            response = await message_processor(user_message)
            
            # Send the reply event
            await self.dispatch_reply_event(client_queue, response)
            
            return response
            
        except Exception as e:
            error_message = f"Error in chat sequence: {str(e)}"
            logger.error(error_message)
            await self.dispatch_error_event(client_queue, error_message)
            return ""
            
    async def dispatch_streaming_chat_sequence(
        self,
        client_queue: asyncio.Queue,
        streaming_processor: Callable[[str], Awaitable[Any]],
        user_message: str,
        thinking_delay: float = 1.0
    ) -> str:
        """
        Dispatch a complete streaming chat sequence with proper event ordering:
        1. freya:listening
        2. freya:thinking (with optional delay)
        3. Process the message with streaming response
        4. freya:reply for each chunk
        
        Args:
            client_queue: The asyncio queue to send events to
            streaming_processor: An async function that returns a stream of response chunks
            user_message: The user's message to process
            thinking_delay: The delay in seconds after the thinking event
            
        Returns:
            The complete response (concatenated from all chunks)
        """
        try:
            # Send listening event immediately
            await self.dispatch_listening_event(client_queue)
            
            # Send thinking event
            await self.dispatch_thinking_event(client_queue)
            
            # Delay for a moment to give frontend time to transition
            await asyncio.sleep(thinking_delay)
            
            # Process the message with the provided streaming function
            response_stream = await streaming_processor(user_message)
            full_response = ""
            
            # Stream each chunk as a reply event
            async for chunk in response_stream:
                if chunk:
                    full_response += chunk
                    await self.dispatch_reply_event(client_queue, chunk)
            
            return full_response
            
        except Exception as e:
            error_message = f"Error in streaming chat sequence: {str(e)}"
            logger.error(error_message)
            await self.dispatch_error_event(client_queue, error_message)
            return ""