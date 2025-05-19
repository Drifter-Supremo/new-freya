"""
chat.py - Chat completion API endpoints
"""
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, Field, field_validator

from app.core.db import get_db
from app.core.config import logger
from app.services.openai_service import OpenAIService
from app.core.memory_context_service import MemoryContextBuilder
from app.repository.user import UserRepository
from app.repository.conversation import ConversationRepository
from app.repository.message import MessageRepository
from app.core.openai_constants import (
    DEFAULT_MODEL, DEFAULT_TEMPERATURE, MAX_TOKENS,
    ROLE_USER, ROLE_ASSISTANT, ROLE_SYSTEM, FREYA_SYSTEM_PROMPT
)


router = APIRouter(prefix="/chat", tags=["chat"])


# Pydantic models for request/response
class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role (user/assistant/system)")
    content: str = Field(..., description="Message content")


class ChatCompletionRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="List of messages in the conversation")
    user_id: int = Field(..., description="User ID for context and memory")
    conversation_id: Optional[int] = Field(None, description="Conversation ID to continue existing conversation")
    model: str = Field(DEFAULT_MODEL, description="Model to use for completion")
    temperature: float = Field(DEFAULT_TEMPERATURE, description="Sampling temperature")
    max_tokens: int = Field(MAX_TOKENS, description="Maximum tokens to generate")
    stream: bool = Field(False, description="Whether to stream the response")
    
    @field_validator('messages')
    def validate_messages(cls, v):
        if not v:
            raise ValueError("Messages list cannot be empty")
        return v
    
    @field_validator('temperature')
    def validate_temperature(cls, v):
        if not 0 <= v <= 2:
            raise ValueError("Temperature must be between 0 and 2")
        return v


class ChatCompletionResponse(BaseModel):
    id: str = Field(..., description="Unique completion ID")
    object: str = Field("chat.completion", description="Object type")
    created: int = Field(..., description="Unix timestamp")
    model: str = Field(..., description="Model used")
    choices: List[Dict[str, Any]] = Field(..., description="Completion choices")
    usage: Optional[Dict[str, int]] = Field(None, description="Token usage statistics")


@router.post("/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    request: ChatCompletionRequest = Body(...),
    db=Depends(get_db)
):
    """
    Create a chat completion with Freya's personality and memory context.
    """
    logger.info(f"Creating chat completion for user {request.user_id}")
    
    # Initialize services
    openai_service = OpenAIService()
    memory_builder = MemoryContextBuilder(db)
    user_repo = UserRepository(db)
    conversation_repo = ConversationRepository(db)
    message_repo = MessageRepository(db)
    
    try:
        # Verify user exists
        user = user_repo.get(request.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get or create conversation
        if request.conversation_id:
            conversation = conversation_repo.get(request.conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
            if conversation.user_id != request.user_id:
                raise HTTPException(status_code=403, detail="Conversation does not belong to user")
        else:
            # Create new conversation
            conversation = conversation_repo.create({
                "user_id": request.user_id,
                "started_at": datetime.utcnow()
            })
            logger.info(f"Created new conversation {conversation.id} for user {request.user_id}")
        
        # Get the last user message
        user_messages = [msg for msg in request.messages if msg.role == ROLE_USER]
        if not user_messages:
            raise HTTPException(status_code=400, detail="No user messages found")
        
        latest_user_message = user_messages[-1].content
        
        # Build memory context based on the user's query
        memory_context = memory_builder.assemble_memory_context(
            user_id=request.user_id,
            query=latest_user_message
        )
        
        # Create system message with memory context
        system_message = FREYA_SYSTEM_PROMPT
        if memory_context.get("formatted_context"):
            system_message += "\n\n" + memory_context["formatted_context"]
        
        # Prepare messages for OpenAI API
        openai_messages = [
            {"role": ROLE_SYSTEM, "content": system_message}
        ]
        
        # Add conversation messages
        for msg in request.messages:
            openai_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Store the user message
        user_msg_record = message_repo.create({
            "conversation_id": conversation.id,
            "user_id": request.user_id,
            "role": ROLE_USER,
            "content": latest_user_message,
            "timestamp": datetime.utcnow()
        })
        
        # Create chat completion
        logger.info(f"Calling OpenAI API with {len(openai_messages)} messages")
        completion = openai_service.create_chat_completion(
            messages=openai_messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=request.stream
        )
        
        # Extract assistant response
        assistant_content = completion.choices[0].message.content
        
        # Store the assistant message
        assistant_msg_record = message_repo.create({
            "conversation_id": conversation.id,
            "user_id": request.user_id,
            "role": ROLE_ASSISTANT,
            "content": assistant_content,
            "timestamp": datetime.utcnow()
        })
        
        # Format response to match OpenAI API structure
        response = ChatCompletionResponse(
            id=str(conversation.id),
            created=int(datetime.utcnow().timestamp()),
            model=request.model,
            choices=[{
                "index": 0,
                "message": {
                    "role": ROLE_ASSISTANT,
                    "content": assistant_content
                },
                "finish_reason": "stop"
            }],
            usage={
                "prompt_tokens": completion.usage.prompt_tokens if completion.usage else 0,
                "completion_tokens": completion.usage.completion_tokens if completion.usage else 0,
                "total_tokens": completion.usage.total_tokens if completion.usage else 0
            }
        )
        
        logger.info(f"Chat completion successful for conversation {conversation.id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating chat completion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))