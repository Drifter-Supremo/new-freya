"""
events.py - Server-Sent Events (SSE) API endpoints
"""
from typing import AsyncGenerator, List, Dict, Any, Optional
import asyncio
from fastapi import APIRouter, Request, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from app.core.db import get_db
from app.core.config import logger
from app.services.event_service import EventService
from app.services.openai_service import OpenAIService
from app.core.memory_context_service import MemoryContextBuilder
from app.core.conversation_history_service import ConversationHistoryService
from app.repository.user import UserRepository
from app.repository.conversation import ConversationRepository
from app.repository.message import MessageRepository
from datetime import datetime

from app.core.openai_constants import (
    DEFAULT_MODEL, DEFAULT_TEMPERATURE, MAX_TOKENS,
    ROLE_USER, ROLE_ASSISTANT, ROLE_SYSTEM, FREYA_SYSTEM_PROMPT
)


router = APIRouter(prefix="/events", tags=["events"])


@router.get("/stream")
async def stream_events(
    request: Request,
    user_id: int = Query(..., description="User ID for authentication and context"),
    conversation_id: Optional[int] = Query(None, description="Conversation ID (optional, for continuing existing conversations)")
):
    """
    Establish an SSE connection for real-time event streaming.
    This endpoint creates a persistent connection that can be used to send
    events to the client (browser) as they occur.
    
    The frontend should listen for these events:
    - freya:listening - When Freya is ready to receive input
    - freya:thinking - When Freya is processing a response
    - freya:reply - When Freya has a response to send
    
    Returns:
        EventSourceResponse: An SSE stream that will emit events
    """
    # Verify user exists in a non-blocking way using the DB dependency
    db = next(get_db())
    user_repo = UserRepository(db)
    user = user_repo.get(user_id)
    if not user:
        logger.error(f"User {user_id} not found when establishing SSE connection")
        raise HTTPException(status_code=404, detail="User not found")
    
    # If conversation_id provided, verify it exists and belongs to the user
    if conversation_id:
        conversation_repo = ConversationRepository(db)
        conversation = conversation_repo.get(conversation_id)
        if not conversation:
            logger.error(f"Conversation {conversation_id} not found for SSE connection")
            raise HTTPException(status_code=404, detail="Conversation not found")
        if conversation.user_id != user_id:
            logger.error(f"Conversation {conversation_id} does not belong to user {user_id}")
            raise HTTPException(status_code=403, detail="Conversation does not belong to user")
    
    logger.info(f"Establishing SSE connection for user {user_id}, conversation {conversation_id or 'new'}")
    
    # Use EventSourceResponse for proper SSE handling
    return EventSourceResponse(EventService.event_generator(request))


@router.post("/chat")
async def chat_with_events(
    request: Request,
    user_id: int = Query(..., description="User ID for context and memory"),
    message: str = Query(..., description="User message content"),
    conversation_id: Optional[int] = Query(None, description="Conversation ID (optional)")
):
    """
    Process a chat message and return the response as an SSE stream.
    This endpoint handles:
    1. Sending the 'freya:listening' event when receiving the message
    2. Sending the 'freya:thinking' event while processing
    3. Streaming the 'freya:reply' event with the response
    
    Args:
        request: The FastAPI request object
        user_id: User ID for context and memory
        message: The user's message content
        conversation_id: Optional conversation ID to continue
        
    Returns:
        EventSourceResponse: An SSE stream with the response events
    """
    
    async def event_stream() -> AsyncGenerator[str, None]:
        # Send listening event immediately
        yield await EventService.create_listening_event()
        
        try:
            # Access database
            db = next(get_db())
            user_repo = UserRepository(db)
            conversation_repo = ConversationRepository(db)
            message_repo = MessageRepository(db)
            history_service = ConversationHistoryService(db)
            
            # Verify user exists
            user = user_repo.get(user_id)
            if not user:
                error = f"User {user_id} not found"
                logger.error(error)
                yield await EventService.format_sse("error", {"message": error})
                return
                
            # Send thinking event
            yield await EventService.create_thinking_event()
            
            # Delay for 1 second to give frontend time to transition
            await asyncio.sleep(1)
            
            # Get or create conversation
            if conversation_id:
                conversation = conversation_repo.get(conversation_id)
                if not conversation:
                    error = f"Conversation {conversation_id} not found"
                    logger.error(error)
                    yield await EventService.format_sse("error", {"message": error})
                    return
                if conversation.user_id != user_id:
                    error = f"Conversation {conversation_id} does not belong to user {user_id}"
                    logger.error(error)
                    yield await EventService.format_sse("error", {"message": error})
                    return
            else:
                # Create new conversation
                conversation = conversation_repo.create({
                    "user_id": user_id,
                    "started_at": datetime.utcnow()
                })
                logger.info(f"Created new conversation {conversation.id} for user {user_id}")
            
            # Store user message
            user_msg_record = message_repo.create({
                "conversation_id": conversation.id,
                "user_id": user_id,
                "role": ROLE_USER,
                "content": message,
                "timestamp": datetime.utcnow()
            })
            
            # Initialize services
            openai_service = OpenAIService()
            memory_builder = MemoryContextBuilder(db)
            
            # Build memory context
            memory_context = memory_builder.assemble_memory_context(
                user_id=user_id,
                query=message
            )
            
            # Get recent conversation history
            # Use the existing ConversationHistoryService which is already properly implemented
            recent_messages = history_service.get_conversation_history(
                conversation_id=conversation.id,
                limit=10,
                skip=0
            )
            
            # Format conversation history for OpenAI, but exclude the message we just added
            conversation_history = []
            for msg in recent_messages:
                if msg.id != user_msg_record.id and msg.role in [ROLE_USER, ROLE_ASSISTANT]:
                    conversation_history.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            
            # Format system prompt with memory context
            system_prompt = FREYA_SYSTEM_PROMPT
            if memory_context and memory_context.get("formatted_context"):
                system_prompt += "\n\n" + memory_context["formatted_context"]
            
            # Stream the chat completion
            completion_stream = await openai_service.create_freya_chat_completion(
                user_message=message,
                conversation_history=conversation_history,
                memory_context=memory_context.get("formatted_context") if memory_context else None,
                stream=True
            )
            
            # Collect the full response while streaming chunks
            full_response = ""
            
            # Handle the streaming response
            async for chunk in completion_stream:
                if chunk:
                    full_response += chunk
                    # Send each chunk as a reply event
                    yield await EventService.create_reply_event(chunk)
            
            # Store the complete assistant response
            assistant_msg_record = message_repo.create({
                "conversation_id": conversation.id,
                "user_id": user_id,
                "role": ROLE_ASSISTANT,
                "content": full_response,
                "timestamp": datetime.utcnow()
            })
            
            logger.info(f"Completed chat response for user {user_id}, conversation {conversation.id}")
            
        except Exception as e:
            logger.error(f"Error in chat event stream: {str(e)}")
            yield await EventService.format_sse("error", {"message": str(e)})
    
    return EventSourceResponse(event_stream())
