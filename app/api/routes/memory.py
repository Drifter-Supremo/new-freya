"""
memory.py - API endpoints for memory context retrieval
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from app.core.db import get_db
from app.core.memory_context_service import assemble_memory_context
from app.services.topic_memory_service import TopicMemoryService

router = APIRouter(prefix="/memory", tags=["memory"])

@router.get("/context", response_model=Dict[str, Any])
def get_memory_context(
    user_id: int = Query(..., description="User ID to retrieve memory for"),
    query: str = Query(..., description="Current user query for context retrieval"),
    use_advanced_scoring: bool = Query(True, description="Whether to use advanced topic relevance scoring"),
    db: Session = Depends(get_db)
):
    """
    Retrieve complete memory context for a chat completion.
    
    This includes:
    - Relevant user facts with confidence scores
    - Recent conversation history
    - Topic-related memories with relevance scores
    
    The context is assembled based on the current user query and can be used
    to enhance chat completions with personalized memory.
    """
    memory_context = assemble_memory_context(
        db=db,
        user_id=user_id,
        query=query,
        use_advanced_scoring=use_advanced_scoring
    )
    
    return memory_context

@router.get("/topics", response_model=Dict[str, Any])
def get_topic_memory_context(
    user_id: int = Query(..., description="User ID to retrieve memory for"),
    query: str = Query(..., description="Search query for topic relevance"),
    topic_limit: int = Query(3, description="Maximum number of topics to include"),
    message_limit: int = Query(3, description="Maximum number of messages per topic"),
    use_advanced_scoring: bool = Query(True, description="Whether to use advanced topic relevance scoring"),
    db: Session = Depends(get_db)
):
    """
    Retrieve topic-based memory context.
    
    Returns relevant topics and associated messages based on the search query.
    Topics are ranked by relevance to the query, and messages are sorted by timestamp.
    """
    service = TopicMemoryService(db)
    topic_context = service.get_memory_context_by_query(
        user_id=user_id,
        query=query,
        topic_limit=topic_limit,
        message_limit=message_limit,
        use_advanced_scoring=use_advanced_scoring
    )
    
    return topic_context

@router.get("/topics/{topic_id}", response_model=Dict[str, Any])
def get_specific_topic_memory(
    topic_id: int,
    user_id: int = Query(..., description="User ID to retrieve memory for"),
    message_limit: int = Query(5, description="Maximum number of messages to include"),
    db: Session = Depends(get_db)
):
    """
    Retrieve memory context for a specific topic.
    
    Returns topic information and associated messages for a specific topic ID.
    Messages are sorted by timestamp (newest first).
    """
    service = TopicMemoryService(db)
    topic_context = service.get_topic_memory_context(
        user_id=user_id,
        topic_id=topic_id,
        message_limit=message_limit
    )
    
    if "error" in topic_context:
        raise HTTPException(status_code=404, detail=topic_context["error"])
    
    return topic_context

@router.get("/comprehensive", response_model=Dict[str, Any])
def get_comprehensive_memory_context(
    user_id: int = Query(..., description="User ID to retrieve memory for"),
    query: str = Query(..., description="Current user query for context retrieval"),
    topic_limit: int = Query(3, description="Maximum number of topics to include"),
    message_limit: int = Query(3, description="Maximum number of messages per topic"),
    use_advanced_scoring: bool = Query(True, description="Whether to use advanced topic relevance scoring"),
    db: Session = Depends(get_db)
):
    """
    Retrieve comprehensive memory context for a chat completion.
    
    This includes:
    - Topic-based memories with relevance scores
    - Recent conversation history
    - User facts (if implemented)
    
    The context is assembled based on the current user query and can be used
    to enhance chat completions with personalized memory.
    """
    service = TopicMemoryService(db)
    memory_context = service.get_comprehensive_memory_context(
        user_id=user_id,
        query=query,
        topic_limit=topic_limit,
        message_limit=message_limit,
        use_advanced_scoring=use_advanced_scoring
    )
    
    return memory_context
