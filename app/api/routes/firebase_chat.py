"""
firebase_chat.py - Simple API for chat interactions using Firebase

This module provides a simplified chat API that uses Firebase/Firestore for data storage
and retrieves memory context to enhance the chat experience.
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
import logging

from app.services.firebase_service import FirebaseService
from app.services.firebase_memory_service import FirebaseMemoryService
from app.services.openai_service import OpenAIService
from app.core.openai_constants import ROLE_USER, ROLE_ASSISTANT
from app.core.config import logger

router = APIRouter()

# Models for request/response
class ChatMessageRequest(BaseModel):
    """Request model for chat messages."""
    message: str = Field(..., min_length=1, description="The user's message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID (optional, will create new if not provided)")
    user_id: str = Field(..., min_length=1, description="User ID")
    include_memory: bool = Field(True, description="Whether to include memory context (default: True)")

class ChatMessageResponse(BaseModel):
    """Response model for chat messages."""
    message: str = Field(..., description="The assistant's response message")
    conversation_id: str = Field(..., description="Conversation ID")
    message_id: str = Field(..., description="Message ID")
    timestamp: str = Field(..., description="Timestamp")
    state_flags: Dict[str, bool] = Field(
        default_factory=lambda: {"listening": False, "thinking": False, "reply": True},
        description="UI state flags"
    )

@router.post("/chat", response_model=ChatMessageResponse)
async def chat_endpoint(
    request: ChatMessageRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Simple chat endpoint that receives a message and returns a response.
    
    This endpoint:
    1. Receives a user message
    2. Retrieves relevant memory context from Firestore
    3. Sends the message with context to OpenAI
    4. Stores the conversation in Firestore
    5. Returns the response
    
    Args:
        request: ChatMessageRequest object
        authorization: Optional authorization header
        
    Returns:
        ChatMessageResponse with the AI's response
    """
    try:
        # Initialize services
        firebase = FirebaseService()
        memory_service = FirebaseMemoryService()
        openai_service = OpenAIService()
        
        # Verify user authentication if token provided
        if authorization:
            # Remove 'Bearer ' prefix if present
            token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
            try:
                claims = firebase.verify_auth_token(token)
                # Ensure user_id matches authenticated user
                if claims.get('uid') != request.user_id:
                    raise HTTPException(status_code=403, detail="User ID doesn't match authenticated user")
            except Exception as e:
                logger.error(f"Authentication error: {str(e)}")
                raise HTTPException(status_code=401, detail="Invalid authentication token")
        
        # Get or create conversation
        conversation_id = request.conversation_id
        if not conversation_id:
            # Create a new conversation
            conversation_data = {
                "userId": request.user_id,
                "createdAt": datetime.now(),
                "updatedAt": datetime.now(),
                "title": f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            }
            conversation_id = firebase.add_document("conversations", conversation_data)
            if not conversation_id:
                raise HTTPException(status_code=500, detail="Failed to create conversation")
        else:
            # Update existing conversation timestamp
            firebase.update_document("conversations", conversation_id, {"updatedAt": datetime.now()})
        
        # Store user message using your field structure: 'user' field for content
        user_message_data = {
            "user": request.message,  # Your structure uses 'user' field, not 'content'
            "timestamp": datetime.now()
        }
        try:
            user_message_id = firebase.add_message(conversation_id, user_message_data)
            if not user_message_id:
                logger.warning("Failed to store user message, but continuing with request")
        except Exception as e:
            logger.error(f"Error storing user message: {str(e)}")
            # Continue with the request even if storing fails
        
        # Get conversation history (last 10 messages)
        history = firebase.get_conversation_messages(conversation_id, limit=10)
        # Format for OpenAI API (excluding the message we just added)
        # Note: Your messages use 'user' field for content, not 'content'
        conversation_history = [
            {"role": ROLE_USER, "content": msg.get("user", "")}
            for msg in history if msg.get("id") != user_message_id and msg.get("user")
        ]
        
        # Retrieve memory context if requested
        memory_context = None
        if request.include_memory:
            memory_result = memory_service.assemble_memory_context(request.user_id, request.message)
            memory_context = memory_result.get("formatted_context")
        
        # Get response from OpenAI
        response = await openai_service.create_freya_chat_completion(
            user_message=request.message,
            conversation_history=conversation_history,
            memory_context=memory_context
        )
        
        # Extract response message
        response_content = openai_service.get_message_content(response)
        
        # Store assistant response in Firestore using your field structure
        assistant_message_data = {
            "user": response_content,  # Your structure uses 'user' field for all message content
            "timestamp": datetime.now()
        }
        try:
            assistant_message_id = firebase.add_message(conversation_id, assistant_message_data)
            if not assistant_message_id:
                logger.warning("Failed to store assistant message, using temporary ID instead")
                assistant_message_id = f"temp_{uuid.uuid4().hex}"
        except Exception as e:
            logger.error(f"Error storing assistant message: {str(e)}")
            # Generate a temporary message ID if storage fails
            assistant_message_id = f"temp_{uuid.uuid4().hex}"
        
        # Extract user facts from the message
        # This is simplified compared to the existing implementation
        # In a real implementation, you'd use more sophisticated fact extraction
        # using the existing facts pattern matching logic
        
        # Return response
        return ChatMessageResponse(
            message=response_content,
            conversation_id=conversation_id,
            message_id=assistant_message_id,
            timestamp=datetime.now().isoformat(),
            state_flags={"listening": False, "thinking": False, "reply": True}
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log and convert other exceptions
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/conversations/{user_id}")
async def get_user_conversations(
    user_id: str,
    limit: int = 10,
    authorization: Optional[str] = Header(None)
):
    """
    Get conversations for a user.
    
    Args:
        user_id: User ID
        limit: Maximum number of conversations to return
        authorization: Optional authorization header
        
    Returns:
        List of conversation objects
    """
    try:
        # Initialize service
        firebase = FirebaseService()
        
        # Verify user authentication if token provided
        if authorization:
            token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
            try:
                claims = firebase.verify_auth_token(token)
                # Ensure user_id matches authenticated user
                if claims.get('uid') != user_id:
                    raise HTTPException(status_code=403, detail="User ID doesn't match authenticated user")
            except Exception as e:
                logger.error(f"Authentication error: {str(e)}")
                raise HTTPException(status_code=401, detail="Invalid authentication token")
        
        # Get conversations
        conversations = firebase.get_user_conversations(user_id, limit=limit)
        return {"conversations": conversations}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    limit: int = 50,
    authorization: Optional[str] = Header(None)
):
    """
    Get messages for a conversation.
    
    Args:
        conversation_id: Conversation ID
        limit: Maximum number of messages to return
        authorization: Optional authorization header
        
    Returns:
        List of message objects
    """
    try:
        # Initialize service
        firebase = FirebaseService()
        
        # Get conversation to check ownership
        conversation = firebase.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Verify user authentication if token provided
        if authorization:
            token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
            try:
                claims = firebase.verify_auth_token(token)
                # Ensure user owns the conversation
                if claims.get('uid') != conversation.get('userId'):
                    raise HTTPException(status_code=403, detail="User doesn't own this conversation")
            except Exception as e:
                logger.error(f"Authentication error: {str(e)}")
                raise HTTPException(status_code=401, detail="Invalid authentication token")
        
        # Get messages
        messages = firebase.get_conversation_messages(conversation_id, limit=limit)
        return {"messages": messages}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting messages: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Delete a conversation.
    
    Args:
        conversation_id: Conversation ID
        authorization: Optional authorization header
        
    Returns:
        Success message
    """
    try:
        # Initialize service
        firebase = FirebaseService()
        
        # Get conversation to check ownership
        conversation = firebase.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Verify user authentication if token provided
        if authorization:
            token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
            try:
                claims = firebase.verify_auth_token(token)
                # Ensure user owns the conversation
                if claims.get('uid') != conversation.get('userId'):
                    raise HTTPException(status_code=403, detail="User doesn't own this conversation")
            except Exception as e:
                logger.error(f"Authentication error: {str(e)}")
                raise HTTPException(status_code=401, detail="Invalid authentication token")
        
        # Delete conversation
        success = firebase.delete_document("conversations", conversation_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete conversation")
        
        return {"message": "Conversation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/topics/{user_id}")
async def get_user_topics(
    user_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Get topics for a user.
    
    Args:
        user_id: User ID
        authorization: Optional authorization header
        
    Returns:
        List of topic objects
    """
    try:
        # Initialize service
        firebase = FirebaseService()
        
        # Verify user authentication if token provided
        if authorization:
            token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
            try:
                claims = firebase.verify_auth_token(token)
                # Ensure user_id matches authenticated user
                if claims.get('uid') != user_id:
                    raise HTTPException(status_code=403, detail="User ID doesn't match authenticated user")
            except Exception as e:
                logger.error(f"Authentication error: {str(e)}")
                raise HTTPException(status_code=401, detail="Invalid authentication token")
        
        # Get topics
        topics = firebase.get_user_topics(user_id)
        return {"topics": topics}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting topics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/facts/{user_id}")
async def get_user_facts(
    user_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Get facts for a user.
    
    Args:
        user_id: User ID
        authorization: Optional authorization header
        
    Returns:
        List of fact objects
    """
    try:
        # Initialize service
        firebase = FirebaseService()
        
        # Verify user authentication if token provided
        if authorization:
            token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
            try:
                claims = firebase.verify_auth_token(token)
                # Ensure user_id matches authenticated user
                if claims.get('uid') != user_id:
                    raise HTTPException(status_code=403, detail="User ID doesn't match authenticated user")
            except Exception as e:
                logger.error(f"Authentication error: {str(e)}")
                raise HTTPException(status_code=401, detail="Invalid authentication token")
        
        # Get facts
        facts = firebase.get_user_facts(user_id)
        return {"facts": facts}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting facts: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")