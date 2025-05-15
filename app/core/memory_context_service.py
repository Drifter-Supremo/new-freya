"""
memory_context_service.py - Service for assembling memory context for chat completions.
"""

from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from app.core.user_fact_service import get_relevant_facts_for_context, format_facts_for_context
from app.core.conversation_history_service import ConversationHistoryService
from app.repository.memory import MemoryQueryRepository
from app.services.topic_memory_service import TopicMemoryService


def assemble_memory_context(db: Session, user_id: int, query: str, use_advanced_scoring: bool = True) -> Dict[str, Any]:
    """
    Assemble a complete memory context for a chat completion request.

    This includes:
    - Relevant user facts with confidence scores
    - Recent conversation history
    - Topic-related memories with advanced relevance scoring

    Args:
        db: Database session
        user_id: User ID to retrieve memory for
        query: The current user query
        use_advanced_scoring: Whether to use advanced topic relevance scoring (default: True)

    Returns:
        Dict containing structured memory context
    """
    memory_context = {
        "user_facts": [],
        "recent_memories": [],
        "topic_memories": []
    }

    # Create services
    conversation_history_service = ConversationHistoryService(db)
    topic_memory_service = TopicMemoryService(db)

    # 1. Get and format relevant user facts
    relevant_facts = get_relevant_facts_for_context(db, user_id, query, limit=5)
    memory_context["user_facts"] = format_facts_for_context(relevant_facts)

    # 2. Get recent memories using the conversation history service
    recent_messages = conversation_history_service.get_recent_messages_across_conversations(
        user_id=user_id,
        limit=10,
        max_age_days=30  # Only include messages from the last 30 days
    )
    memory_context["recent_memories"] = conversation_history_service.format_messages_for_context(
        messages=recent_messages,
        include_timestamps=True
    )

    # 3. Get topic-related memories using the topic memory service
    topic_context = topic_memory_service.get_memory_context_by_query(
        user_id=user_id,
        query=query,
        topic_limit=3,
        message_limit=3,
        use_advanced_scoring=use_advanced_scoring
    )

    memory_context["topic_memories"] = topic_context["topic_memories"]

    return memory_context
