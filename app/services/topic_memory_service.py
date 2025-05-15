"""
topic_memory_service.py - Service for retrieving topic-based memory context.

This service provides functionality for retrieving memory context based on topics,
including relevant messages, topic information, and formatted context for chat completions.
"""
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.topic import Topic
from app.models.message import Message
from app.repository.memory import MemoryQueryRepository
from app.services.topic_search import TopicSearchService
from app.core.conversation_history_service import ConversationHistoryService


class TopicMemoryService:
    """
    Service for retrieving topic-based memory context.
    
    This service provides methods for:
    - Retrieving memory context based on topics
    - Retrieving memory context based on a query
    - Formatting topic-based memory for chat completions
    """
    
    def __init__(self, db: Session):
        """
        Initialize the TopicMemoryService with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.memory_repo = MemoryQueryRepository(db)
        self.topic_search_service = TopicSearchService(db)
        self.conversation_history_service = ConversationHistoryService(db)
    
    def get_topic_memory_context(
        self, 
        user_id: int, 
        topic_id: int, 
        message_limit: int = 5
    ) -> Dict[str, Any]:
        """
        Get memory context for a specific topic.
        
        Args:
            user_id: ID of the user
            topic_id: ID of the topic
            message_limit: Maximum number of messages to include (default: 5)
            
        Returns:
            Dictionary with topic information and related messages
        """
        # Get the topic
        topic = self.db.query(Topic).filter(Topic.id == topic_id).first()
        if not topic:
            return {"error": "Topic not found"}
        
        # Get messages for the topic
        messages = self.memory_repo.get_messages_for_user_topic(user_id, topic_id, message_limit)
        
        # Format the context
        return {
            "topic": {
                "id": topic.id,
                "name": topic.name
            },
            "message_count": len(messages),
            "messages": self.conversation_history_service.format_messages_for_context(
                messages=messages,
                include_timestamps=True
            )
        }
    
    def get_memory_context_by_query(
        self, 
        user_id: int, 
        query: str, 
        topic_limit: int = 3, 
        message_limit: int = 3,
        use_advanced_scoring: bool = True
    ) -> Dict[str, Any]:
        """
        Get memory context based on a query.
        
        Args:
            user_id: ID of the user
            query: Search query string
            topic_limit: Maximum number of topics to include (default: 3)
            message_limit: Maximum number of messages per topic (default: 3)
            use_advanced_scoring: Whether to use advanced relevance scoring (default: True)
            
        Returns:
            Dictionary with topic memories
        """
        # Search for relevant topics
        if use_advanced_scoring:
            topic_results = self.topic_search_service.search_topics_advanced(user_id, query, topic_limit)
        else:
            topic_results = self.topic_search_service.search_topics(user_id, query, topic_limit)
        
        # If no topics found, return empty context
        if not topic_results:
            return {"topic_memories": []}
        
        # Build context for each topic
        topic_memories = []
        for topic, score in topic_results:
            # Get messages for the topic
            messages = self.memory_repo.get_messages_for_user_topic(user_id, topic.id, message_limit)
            
            # Add topic memory to the list
            topic_memories.append({
                "topic": {
                    "id": topic.id,
                    "name": topic.name,
                    "relevance_score": float(score),  # Convert to float for JSON serialization
                    "relevance": min(100, int(score * 100))  # 0-100 scale for frontend
                },
                "message_count": len(messages),
                "messages": self.conversation_history_service.format_messages_for_context(
                    messages=messages,
                    include_timestamps=True
                )
            })
        
        return {"topic_memories": topic_memories}
    
    def get_comprehensive_memory_context(
        self, 
        user_id: int, 
        query: str, 
        topic_limit: int = 3, 
        message_limit: int = 3,
        use_advanced_scoring: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive memory context for a chat completion.
        
        This includes:
        - Topic-based memories with relevance scores
        - Recent conversation history
        - User facts (if implemented)
        
        Args:
            user_id: ID of the user
            query: Search query string
            topic_limit: Maximum number of topics to include (default: 3)
            message_limit: Maximum number of messages per topic (default: 3)
            use_advanced_scoring: Whether to use advanced relevance scoring (default: True)
            
        Returns:
            Dictionary with comprehensive memory context
        """
        # Get topic memories
        topic_context = self.get_memory_context_by_query(
            user_id=user_id,
            query=query,
            topic_limit=topic_limit,
            message_limit=message_limit,
            use_advanced_scoring=use_advanced_scoring
        )
        
        # Get recent conversation history
        recent_messages = self.conversation_history_service.get_recent_messages_across_conversations(
            user_id=user_id,
            limit=10,
            max_age_days=30  # Only include messages from the last 30 days
        )
        
        # Build comprehensive context
        memory_context = {
            "topic_memories": topic_context["topic_memories"],
            "recent_memories": self.conversation_history_service.format_messages_for_context(
                messages=recent_messages,
                include_timestamps=True
            )
        }
        
        # Add user facts if available (this would be integrated with the user fact service)
        # This is a placeholder for future integration
        memory_context["user_facts"] = []
        
        return memory_context
