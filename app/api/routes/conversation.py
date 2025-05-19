"""
conversation.py - API endpoints for conversation history
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from app.core.db import get_db
from app.core.conversation_history_service import ConversationHistoryService
from app.repository.conversation import ConversationRepository

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("/", response_model=Dict[str, Any])
def create_conversation(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Create a new conversation for a user.
    
    Returns the created conversation with its ID and timestamp.
    """
    repo = ConversationRepository(db)
    
    # Create the conversation
    conversation = repo.create({
        "user_id": user_id,
        "started_at": datetime.now(timezone.utc)
    })
    
    return {
        "id": conversation.id,
        "user_id": conversation.user_id,
        "started_at": conversation.started_at.isoformat() if conversation.started_at else None
    }


@router.get("/{user_id}/recent", response_model=List[Dict[str, Any]])
def get_recent_conversations(
    user_id: int,
    limit: int = Query(5, description="Maximum number of conversations to return"),
    db: Session = Depends(get_db)
):
    """
    Retrieve recent conversations for a user.
    
    Returns conversations ordered by most recent activity.
    """
    service = ConversationHistoryService(db)
    conversations = service.get_recent_conversations(user_id, limit)
    
    return [
        {
            "id": conv.id,
            "user_id": conv.user_id,
            "started_at": conv.started_at.isoformat() if hasattr(conv, "started_at") else None
        }
        for conv in conversations
    ]

@router.get("/{conversation_id}/messages", response_model=List[Dict[str, Any]])
def get_conversation_messages(
    conversation_id: int,
    limit: int = Query(20, description="Maximum number of messages to return"),
    skip: int = Query(0, description="Number of messages to skip"),
    db: Session = Depends(get_db)
):
    """
    Retrieve messages from a specific conversation.
    
    Returns messages ordered by timestamp (newest first).
    """
    # First check if the conversation exists
    repo = ConversationRepository(db)
    conversation = repo.get(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    service = ConversationHistoryService(db)
    messages = service.get_conversation_history(conversation_id, limit, skip)
    
    return [
        {
            "id": msg.id,
            "conversation_id": msg.conversation_id,
            "user_id": msg.user_id,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat() if hasattr(msg, "timestamp") else None
        }
        for msg in messages
    ]

@router.get("/{user_id}/recent-messages", response_model=List[Dict[str, Any]])
def get_recent_messages(
    user_id: int,
    limit: int = Query(20, description="Maximum number of messages to return"),
    max_age_days: Optional[int] = Query(
        30, 
        description="Only include messages from the last N days (null for no limit)"
    ),
    db: Session = Depends(get_db)
):
    """
    Retrieve recent messages for a user across all conversations.
    
    Returns messages ordered by timestamp (newest first).
    """
    service = ConversationHistoryService(db)
    messages = service.get_recent_messages_across_conversations(
        user_id, 
        limit, 
        max_age_days
    )
    
    return [
        {
            "id": msg.id,
            "conversation_id": msg.conversation_id,
            "user_id": msg.user_id,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat() if hasattr(msg, "timestamp") else None
        }
        for msg in messages
    ]

@router.get("/{conversation_id}/context", response_model=Dict[str, Any])
def get_conversation_context(
    conversation_id: int,
    message_limit: int = Query(10, description="Maximum number of recent messages to include"),
    db: Session = Depends(get_db)
):
    """
    Get formatted conversation context for a specific conversation.
    
    Returns a dictionary with conversation metadata and recent messages.
    """
    service = ConversationHistoryService(db)
    context = service.get_conversation_context(conversation_id, message_limit)
    
    if "error" in context:
        raise HTTPException(status_code=404, detail=context["error"])
    
    return context


@router.get("/{user_id}/search", response_model=List[Dict[str, Any]])
def search_conversations(
    user_id: int,
    query: str = Query(..., min_length=1, description="Search query string"),
    limit: int = Query(20, description="Maximum number of messages to return"),
    db: Session = Depends(get_db)
):
    """
    Search through user's conversation messages using full-text search.
    
    Returns messages that match the search query.
    """
    from sqlalchemy import text
    
    # Use PostgreSQL full-text search to find matching messages
    # Note: we need to join with conversations to filter by user_id
    results = db.execute(
        text("""
        SELECT m.id, m.conversation_id, m.user_id, m.role, m.content, m.timestamp,
               ts_rank(m.content_tsv, plainto_tsquery(:query)) as rank
        FROM messages m
        JOIN conversations c ON m.conversation_id = c.id
        WHERE c.user_id = :user_id 
        AND m.content_tsv @@ plainto_tsquery(:query)
        ORDER BY rank DESC, m.timestamp DESC
        LIMIT :limit
        """),
        {"user_id": user_id, "query": query, "limit": limit}
    ).fetchall()
    
    # Format results
    messages = []
    for row in results:
        messages.append({
            "id": row.id,
            "conversation_id": row.conversation_id,
            "user_id": row.user_id,
            "role": row.role,
            "content": row.content,
            "timestamp": row.timestamp.isoformat() if row.timestamp else None,
            "rank": float(row.rank)  # Include relevance score
        })
    
    return messages


@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    user_id: int = Query(..., description="User ID for authorization"),
    db: Session = Depends(get_db)
):
    """
    Delete a conversation and all its messages.
    
    Requires user_id for authorization to ensure users can only delete their own conversations.
    """
    repo = ConversationRepository(db)
    
    # Get the conversation first to check ownership
    conversation = repo.get(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Verify the conversation belongs to the user
    if conversation.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this conversation")
    
    # Delete the conversation (cascades to messages due to relationship configuration)
    repo.delete(conversation_id)
    db.commit()  # Commit the deletion
    
    return {"message": f"Conversation {conversation_id} deleted successfully"}
