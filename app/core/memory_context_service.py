"""
memory_context_service.py - Service for assembling memory context for chat completions.
"""

from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from app.core.user_fact_service import get_relevant_facts_for_context, format_facts_for_context
from app.core.conversation_history_service import ConversationHistoryService
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

    # Create conversation history service
    conversation_history_service = ConversationHistoryService(db)

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

    # 3. Search for topic-related memories (will be expanded in future tasks)
    topic_results = memory_repo.search_topics_by_message_content(user_id, query, limit=2)
    if topic_results:
        # We found some topics - get related messages
        for topic, score in topic_results:
            topic_messages = memory_repo.get_messages_for_user_topic(user_id, topic.id, limit=3)
            memory_context["topic_memories"].append({
                "topic": topic.name,
                "relevance": min(100, int(score * 100)),
                "messages": conversation_history_service.format_messages_for_context(
                    messages=topic_messages,
                    include_timestamps=True
                )
            })

    return memory_context
