"""
Topic Search Service

This service provides functionality for searching topics and retrieving
topic-related information from the database.
"""
from typing import List, Dict, Tuple, Optional, Any
from sqlalchemy.orm import Session

from app.models.topic import Topic
from app.models.message import Message
from app.repository.memory import MemoryQueryRepository


class TopicSearchService:
    """
    Service for searching topics and retrieving topic-related information.

    This service provides methods for:
    - Searching topics based on message content
    - Retrieving messages for a specific topic
    - Getting all topics for a user
    """

    def __init__(self, db: Session):
        """
        Initialize the TopicSearchService with a database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.memory_repo = MemoryQueryRepository(db)

    def search_topics(self, user_id: int, query: str, limit: int = 10) -> List[Tuple[Topic, float]]:
        """
        Search for topics relevant to a query for a specific user.

        Args:
            user_id: ID of the user
            query: Search query string
            limit: Maximum number of topics to return (default: 10)

        Returns:
            List of (Topic, score) tuples, sorted by relevance score (highest first)
        """
        return self.memory_repo.search_topics_by_message_content(user_id, query, limit)

    def search_topics_advanced(self, user_id: int, query: str, limit: int = 10) -> List[Tuple[Topic, float]]:
        """
        Search for topics with advanced relevance scoring.

        This method uses a more sophisticated relevance scoring algorithm that considers:
        1. Full-text search relevance
        2. Topic frequency
        3. Recency
        4. Direct keyword matches

        Args:
            user_id: ID of the user
            query: Search query string
            limit: Maximum number of topics to return (default: 10)

        Returns:
            List of (Topic, score) tuples, sorted by relevance score (highest first)
        """
        return self.memory_repo.get_topics_with_advanced_relevance(user_id, query, limit)

    def get_messages_by_topic(self, user_id: int, topic_id: int, limit: int = 50) -> List[Message]:
        """
        Get messages for a specific topic and user.

        Args:
            user_id: ID of the user
            topic_id: ID of the topic
            limit: Maximum number of messages to return (default: 50)

        Returns:
            List of Message objects, sorted by timestamp (newest first)
        """
        return self.memory_repo.get_messages_for_user_topic(user_id, topic_id, limit)

    def get_user_topics(self, user_id: int) -> List[Topic]:
        """
        Get all topics for a specific user.

        Args:
            user_id: ID of the user

        Returns:
            List of Topic objects
        """
        return self.memory_repo.get_topics_for_user(user_id)

    def format_topic_search_results(self, results: List[Tuple[Topic, float]]) -> List[Dict[str, Any]]:
        """
        Format topic search results for API response.

        Args:
            results: List of (Topic, score) tuples from search_topics

        Returns:
            List of dictionaries with topic information and relevance score
        """
        return [
            {
                "id": topic.id,
                "name": topic.name,
                "relevance_score": float(score)  # Convert to float for JSON serialization
            }
            for topic, score in results
        ]

    def format_topic_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """
        Format messages for API response.

        Args:
            messages: List of Message objects

        Returns:
            List of dictionaries with message information
        """
        return [
            {
                "id": message.id,
                "content": message.content,
                "timestamp": message.timestamp.isoformat() if message.timestamp else None,
                "conversation_id": message.conversation_id
            }
            for message in messages
        ]
