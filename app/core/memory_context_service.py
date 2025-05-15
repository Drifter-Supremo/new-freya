"""
memory_context_service.py - Service for assembling memory context for chat completions.
"""

from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from app.core.user_fact_service import get_relevant_facts_for_context, format_facts_for_context
from app.repository.memory import MemoryQueryRepository


def assemble_memory_context(db: Session, user_id: int, query: str) -> Dict[str, Any]:
    """
    Assemble a complete memory context for a chat completion request.
    
    This includes:
    - Relevant user facts with confidence scores
    - Recent conversation history
    - Topic-related memories (if applicable)
    
    Args:
        db: Database session
        user_id: User ID to retrieve memory for
        query: The current user query
        
    Returns:
        Dict containing structured memory context
    """
    memory_context = {
        "user_facts": [],
        "recent_memories": [],
        "topic_memories": []
    }
    
    # Get repository for memory queries
    memory_repo = MemoryQueryRepository(db)
    
    # 1. Get and format relevant user facts
    relevant_facts = get_relevant_facts_for_context(db, user_id, query, limit=5)
    memory_context["user_facts"] = format_facts_for_context(relevant_facts)
    
    # 2. Get recent memories (will be expanded in future tasks)
    # Placeholder for now
    recent_messages = memory_repo.get_recent_memories_for_user(user_id, limit=5)
    memory_context["recent_memories"] = [
        {
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat() if hasattr(msg, "timestamp") else None
        }
        for msg in recent_messages
    ]
    
    # 3. Search for topic-related memories (will be expanded in future tasks)
    # Placeholder for now - this will be expanded when implementing Topic Memory
    topic_results = memory_repo.search_topics_by_message_content(user_id, query, limit=2)
    if topic_results:
        # We found some topics - get related messages
        for topic, score in topic_results:
            topic_messages = memory_repo.get_messages_for_user_topic(user_id, topic.id, limit=3)
            memory_context["topic_memories"].append({
                "topic": topic.name,
                "relevance": min(100, int(score * 100)),
                "messages": [
                    {
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat() if hasattr(msg, "timestamp") else None
                    }
                    for msg in topic_messages
                ]
            })
    
    return memory_context
