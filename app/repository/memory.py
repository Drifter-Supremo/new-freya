from sqlalchemy.orm import Session, joinedload
from app.models import User, Message, Topic, MessageTopic, Conversation, UserFact
from typing import List, Optional

class MemoryQueryRepository:
    def __init__(self, db: Session):
        self.db = db

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
