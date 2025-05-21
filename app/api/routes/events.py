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
from app.services.event_dispatcher import EventDispatcher
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
    
    async def event_stream():
        # Create a queue for the event dispatcher to use
        event_queue = asyncio.Queue()
        
        # Create event dispatcher
        event_dispatcher = EventDispatcher()
        
        # Define function to yield events from the queue
        async def generate_events():
            while True:
                # Wait for an event to be available
                event = await event_queue.get()
                yield event
                event_queue.task_done()
                
                # If client disconnected, stop processing
                if await request.is_disconnected():
                    logger.info("Client disconnected, stopping event processing")
                    break
        
        # Use the generator function directly - don't create a task
        
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
                await event_dispatcher.dispatch_error_event(event_queue, error)
                return
            
            # Stream chat processing steps through event dispatcher
            # First dispatch listening event
            await event_dispatcher.dispatch_listening_event(event_queue)
            
            # Then dispatch thinking event
            await event_dispatcher.dispatch_thinking_event(event_queue)
            
            # Delay for 1 second to give frontend time to transition
            await asyncio.sleep(1)
            
            # Get or create conversation
            if conversation_id:
                conversation = conversation_repo.get(conversation_id)
                if not conversation:
                    error = f"Conversation {conversation_id} not found"
                    logger.error(error)
                    await event_dispatcher.dispatch_error_event(event_queue, error)
                    return
                if conversation.user_id != user_id:
                    error = f"Conversation {conversation_id} does not belong to user {user_id}"
                    logger.error(error)
                    await event_dispatcher.dispatch_error_event(event_queue, error)
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
            
            # Define an async function to get the streaming chat completion
            async def get_streaming_completion(user_msg: str):
                completion_stream = await openai_service.create_freya_chat_completion(
                    user_message=user_msg,
                    conversation_history=conversation_history,
                    memory_context=memory_context.get("formatted_context") if memory_context else None,
                    stream=True
                )
                
                # Return the generator
                return completion_stream
            
            # Use the event dispatcher to handle the streaming chat sequence
            full_response = await event_dispatcher.dispatch_streaming_chat_sequence(
                client_queue=event_queue,
                streaming_processor=get_streaming_completion,
                user_message=message,
                thinking_delay=0  # We already added a delay above
            )
            
            # Store the complete assistant response (if we got a valid response)
            if full_response:
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
            # No need to yield here, the event_dispatcher will handle the error event
            await event_dispatcher.dispatch_error_event(event_queue, str(e))
        
        # Send first events through the queue and then use the generator
        # The chat sequence will continue to send events as they become available
        
        # Return an async generator that yields events from the queue
        return generate_events()
    
    # Use the async generator directly in the EventSourceResponse
    return EventSourceResponse(event_stream())


@router.post("/legacy")
async def legacy_compatibility_chat(
    request: Request,
    user_id: int = Query(..., description="User ID for context and memory"),
    message: str = Query(..., description="User message content"),
    conversation_id: Optional[int] = Query(None, description="Conversation ID (optional)")
):
    """
    Backward compatibility endpoint for the legacy frontend.
    This endpoint implements the same flow as /chat but adds compatibility
    with the window.sendMessageToAPI frontend function, dispatching browser events.
    
    The events dispatched are:
    - freya:listening - When Freya starts listening (immediately)
    - freya:thinking - When Freya is processing (after validation)
    - freya:reply - When Freya sends a response (after processing)
    
    Args:
        request: The FastAPI request object
        user_id: User ID for context and memory
        message: The user's message content
        conversation_id: Optional conversation ID to continue
    
    Returns:
        Dict: A JSON response with the full text response and metadata
    """
    async def event_stream():
        # Create a queue for the event dispatcher to use
        event_queue = asyncio.Queue()
        
        # Create event dispatcher
        event_dispatcher = EventDispatcher()
        
        # Define function to yield events from the queue
        async def generate_events():
            while True:
                # Wait for an event to be available
                event = await event_queue.get()
                yield event
                event_queue.task_done()
                
                # If client disconnected, stop processing
                if await request.is_disconnected():
                    logger.info("Client disconnected, stopping event processing")
                    break
        
        # Use the generator function directly - don't create a task
        
        try:
            # Process the chat using the same logic as /chat endpoint
            # But for legacy compatibility, we'll add explicit browser events
            
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
                await event_dispatcher.dispatch_error_event(event_queue, error)
                return
            
            # Use the event dispatcher to handle the sequence
            await event_dispatcher.dispatch_listening_event(event_queue)
            
            # Get or create conversation
            if conversation_id:
                conversation = conversation_repo.get(conversation_id)
                if not conversation:
                    error = f"Conversation {conversation_id} not found"
                    logger.error(error)
                    await event_dispatcher.dispatch_error_event(event_queue, error)
                    return
                if conversation.user_id != user_id:
                    error = f"Conversation {conversation_id} does not belong to user {user_id}"
                    logger.error(error)
                    await event_dispatcher.dispatch_error_event(event_queue, error)
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
            
            # Build memory context and conversation history
            memory_context = memory_builder.assemble_memory_context(
                user_id=user_id,
                query=message
            )
            
            recent_messages = history_service.get_conversation_history(
                conversation_id=conversation.id,
                limit=10,
                skip=0
            )
            
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
            
            # Now send the thinking event before processing
            await event_dispatcher.dispatch_thinking_event(event_queue)
            
            # Define an async function to get the complete (non-streaming) chat completion
            async def get_completion(user_msg: str) -> str:
                response = await openai_service.create_freya_chat_completion(
                    user_message=user_msg,
                    conversation_history=conversation_history,
                    memory_context=memory_context.get("formatted_context") if memory_context else None,
                    stream=False  # For legacy mode, we use the non-streaming API for simplicity
                )
                return response
            
            # Use the event dispatcher for the chat sequence
            full_response = await event_dispatcher.dispatch_chat_sequence(
                client_queue=event_queue,
                message_processor=get_completion,
                user_message=message,
                thinking_delay=1.0
            )
            
            # Store the assistant response
            if full_response:
                assistant_msg_record = message_repo.create({
                    "conversation_id": conversation.id,
                    "user_id": user_id,
                    "role": ROLE_ASSISTANT, 
                    "content": full_response,
                    "timestamp": datetime.utcnow()
                })
                
                logger.info(f"Completed legacy chat response for user {user_id}, conversation {conversation.id}")
            
        except Exception as e:
            logger.error(f"Error in legacy chat event stream: {str(e)}")
            await event_dispatcher.dispatch_error_event(event_queue, str(e))
        
        # Send first events through the queue and then use the generator
        # The chat sequence will continue to send events as they become available
        
        # Return an async generator that yields events from the queue
        return generate_events()
    
    # Use the async generator directly in the EventSourceResponse
    return EventSourceResponse(event_stream())