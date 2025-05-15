"""
topic.py - API endpoints for topic search and retrieval
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.core.db import get_db
from app.services.topic_search import TopicSearchService
from app.repository.topic import TopicRepository

router = APIRouter(prefix="/topics", tags=["topics"])

@router.get("/search", response_model=List[Dict[str, Any]])
def search_topics(
    user_id: int = Query(..., description="User ID to search topics for"),
    query: str = Query(..., description="Search query string"),
    limit: int = Query(10, description="Maximum number of topics to return"),
    db: Session = Depends(get_db)
):
    """
    Search for topics relevant to a query for a specific user.
    
    Topics are ranked by relevance to the search query using PostgreSQL full-text search.
    Returns a list of topics with relevance scores.
    """
    service = TopicSearchService(db)
    results = service.search_topics(user_id, query, limit)
    
    if not results:
        return []
    
    return service.format_topic_search_results(results)

@router.get("/{topic_id}/messages", response_model=List[Dict[str, Any]])
def get_topic_messages(
    topic_id: int,
    user_id: int = Query(..., description="User ID to get messages for"),
    limit: int = Query(50, description="Maximum number of messages to return"),
    db: Session = Depends(get_db)
):
    """
    Get messages for a specific topic and user.
    
    Returns messages sorted by timestamp (newest first).
    """
    # First check if the topic exists
    repo = TopicRepository(db)
    topic = repo.get(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    service = TopicSearchService(db)
    messages = service.get_messages_by_topic(user_id, topic_id, limit)
    
    if not messages:
        return []
    
    return service.format_topic_messages(messages)

@router.get("/user/{user_id}", response_model=List[Dict[str, Any]])
def get_user_topics(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all topics for a specific user.
    
    Returns a list of topics the user has discussed in their messages.
    """
    service = TopicSearchService(db)
    topics = service.get_user_topics(user_id)
    
    if not topics:
        return []
    
    return [
        {
            "id": topic.id,
            "name": topic.name
        }
        for topic in topics
    ]
