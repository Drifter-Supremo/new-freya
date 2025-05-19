"""
event_service.py - Service for handling Server-Sent Events (SSE) formatting and emission
"""
from typing import Dict, Any, Optional, AsyncGenerator
import json
import asyncio
from datetime import datetime
from fastapi import Request

from app.core.config import logger


class EventService:
    """
    Service for handling Server-Sent Events (SSE) formatting and emission.
    Provides methods for creating event streams and sending different event types.
    """

    @staticmethod
    async def format_sse(event: str, data: Any) -> str:
        """
        Format data as a Server-Sent Event.
        
        Args:
            event: The event type (e.g., "freya:listening", "freya:thinking", "freya:reply")
            data: The data to send (will be JSON-serialized)
            
        Returns:
            Properly formatted SSE message
        """
        if isinstance(data, dict) or isinstance(data, list):
            json_data = json.dumps(data)
        else:
            json_data = json.dumps({"message": str(data)})
            
        return f"event: {event}\ndata: {json_data}\n\n"

    @staticmethod
    async def create_listening_event() -> str:
        """Create a 'freya:listening' event"""
        return await EventService.format_sse(
            "freya:listening", 
            {
                "timestamp": datetime.utcnow().isoformat(),
                "state": "listening"
            }
        )

    @staticmethod
    async def create_thinking_event() -> str:
        """Create a 'freya:thinking' event"""
        return await EventService.format_sse(
            "freya:thinking", 
            {
                "timestamp": datetime.utcnow().isoformat(),
                "state": "thinking"
            }
        )

    @staticmethod
    async def create_reply_event(message: str) -> str:
        """Create a 'freya:reply' event with the response message"""
        return await EventService.format_sse(
            "freya:reply", 
            {
                "timestamp": datetime.utcnow().isoformat(),
                "message": message,
                "state": "reply"
            }
        )

    @staticmethod
    async def event_generator(request: Request) -> AsyncGenerator[str, None]:
        """
        Generate SSE events while checking if the client is still connected.
        
        Args:
            request: The FastAPI request object
            
        Yields:
            Formatted SSE events
        """
        # Send initial connection established event
        yield await EventService.format_sse("connection", {"status": "established"})
        
        # Keep the connection alive
        while True:
            # Check if client is still connected
            if await request.is_disconnected():
                logger.info("Client disconnected from SSE stream")
                break
                
            # Send a heartbeat comment every 15 seconds to keep the connection alive
            yield ": heartbeat\n\n"
            
            # Wait before the next heartbeat
            await asyncio.sleep(15)
