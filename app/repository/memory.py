from sqlalchemy.orm import Session, joinedload
from app.models import User, Message, Topic, MessageTopic, Conversation, UserFact
from typing import List, Optional

class MemoryQueryRepository:
    def __init__(self, db: Session):
        self.db = db

    def search_topics_by_message_content(self, user_id: int, query: str, limit: int = 10):
        """
        Perform a full-text search on messages for a user and return relevant topics with relevance scores.
        Returns: List of (Topic, score) tuples, sorted by score descending.
        """
        from sqlalchemy import func
        # Convert the query to a tsquery - use plainto_tsquery directly for better compatibility
        ts_query = func.plainto_tsquery('english', query)
        # Use ts_rank to compute relevance
        score = func.max(func.ts_rank(Message.content_tsv, ts_query)).label('score')
        results = (
            self.db.query(Topic, score)
            .join(MessageTopic, Topic.id == MessageTopic.topic_id)
            .join(Message, Message.id == MessageTopic.message_id)
            .filter(Message.user_id == user_id)
            .filter(Message.content_tsv.op('@@')(ts_query))
            .group_by(Topic.id)
            .order_by(score.desc())
            .limit(limit)
            .all()
        )
        # Return list of (Topic, score) tuples
        return results

    def get_messages_for_user_topic(self, user_id: int, topic_id: int, limit: int = 50) -> List[Message]:
        """Optimized: Get all messages for a user in a topic, ordered by time (newest first)."""
        return (
            self.db.query(Message)
            .join(MessageTopic, Message.id == MessageTopic.message_id)
            .filter(Message.user_id == user_id, MessageTopic.topic_id == topic_id)
            .order_by(Message.timestamp.desc())
            .limit(limit)
            .options(joinedload(Message.user), joinedload(Message.conversation))
            .all()
        )

    def get_recent_memories_for_user(self, user_id: int, limit: int = 20) -> List[Message]:
        """Optimized: Get most recent messages for a user across all topics."""
        return (
            self.db.query(Message)
            .filter(Message.user_id == user_id)
            .order_by(Message.timestamp.desc())
            .limit(limit)
            .options(joinedload(Message.user), joinedload(Message.conversation))
            .all()
        )

    def get_facts_for_user(self, user_id: int) -> List[UserFact]:
        """Optimized: Get all user facts for a user."""
        return (
            self.db.query(UserFact)
            .filter(UserFact.user_id == user_id)
            .all()
        )

    def get_topics_for_user(self, user_id: int) -> List[Topic]:
        """Optimized: Get all unique topics a user has messages in."""
        return (
            self.db.query(Topic)
            .join(MessageTopic, Topic.id == MessageTopic.topic_id)
            .join(Message, Message.id == MessageTopic.message_id)
            .filter(Message.user_id == user_id)
            .distinct()
            .all()
        )
