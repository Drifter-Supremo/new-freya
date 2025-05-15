"""
conversation_history_service.py - Service for managing conversation history and context.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func

from app.models.conversation import Conversation
from app.models.message import Message
from app.repository.conversation import ConversationRepository
from app.repository.message import MessageRepository


class ConversationHistoryService:
    def __init__(self, db: Session):
        self.db = db
        self.conversation_repo = ConversationRepository(db)
        self.message_repo = MessageRepository(db)
    
    def get_conversation_history(
        self, 
        conversation_id: int, 
        limit: int = 20, 
        skip: int = 0
    ) -> List[Message]:
        """
        Retrieve messages from a specific conversation, ordered by timestamp (newest first).
        
        Args:
            conversation_id: ID of the conversation to retrieve messages from
            limit: Maximum number of messages to return
            skip: Number of messages to skip (for pagination)
            
        Returns:
            List of Message objects
        """
        return (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(desc(Message.timestamp))
            .offset(skip)
            .limit(limit)
            .options(joinedload(Message.user))
            .all()
        )
    
    def get_recent_conversations(
        self, 
        user_id: int, 
        limit: int = 5
    ) -> List[Conversation]:
        """
        Get the most recent conversations for a user.
        
        Args:
            user_id: User ID to retrieve conversations for
            limit: Maximum number of conversations to return
            
        Returns:
            List of Conversation objects, ordered by most recent activity
        """
        # Get conversations with their latest message timestamp
        subquery = (
            self.db.query(
                Message.conversation_id,
                func.max(Message.timestamp).label("latest_message")
            )
            .filter(Message.user_id == user_id)
            .group_by(Message.conversation_id)
            .subquery()
        )
        
        # Join with the conversations table and order by latest message
        return (
            self.db.query(Conversation)
            .join(
                subquery, 
                Conversation.id == subquery.c.conversation_id
            )
            .filter(Conversation.user_id == user_id)
            .order_by(desc(subquery.c.latest_message))
            .limit(limit)
            .all()
        )
    
    def get_recent_messages_across_conversations(
        self, 
        user_id: int, 
        limit: int = 20, 
        max_age_days: Optional[int] = 30
    ) -> List[Message]:
        """
        Get recent messages for a user across all conversations.
        
        Args:
            user_id: User ID to retrieve messages for
            limit: Maximum number of messages to return
            max_age_days: Only include messages from the last N days (None for no limit)
            
        Returns:
            List of Message objects, ordered by timestamp (newest first)
        """
        query = (
            self.db.query(Message)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .filter(Conversation.user_id == user_id)
        )
        
        # Apply time filter if specified
        if max_age_days is not None:
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            query = query.filter(Message.timestamp >= cutoff_date)
        
        # Complete the query with ordering, limit and eager loading
        return (
            query
            .order_by(desc(Message.timestamp))
            .limit(limit)
            .options(
                joinedload(Message.conversation),
                joinedload(Message.user)
            )
            .all()
        )
    
    def get_conversation_context(
        self, 
        conversation_id: int, 
        message_limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get formatted conversation context for a specific conversation.
        
        Args:
            conversation_id: ID of the conversation to retrieve context for
            message_limit: Maximum number of recent messages to include
            
        Returns:
            Dictionary with conversation metadata and recent messages
        """
        # Get the conversation
        conversation = self.conversation_repo.get(conversation_id)
        if not conversation:
            return {"error": "Conversation not found"}
        
        # Get recent messages
        recent_messages = self.get_conversation_history(
            conversation_id=conversation_id,
            limit=message_limit
        )
        
        # Format the context
        return {
            "conversation_id": conversation.id,
            "user_id": conversation.user_id,
            "started_at": conversation.started_at.isoformat() if hasattr(conversation, "started_at") else None,
            "message_count": len(recent_messages),
            "messages": [
                {
                    "id": msg.id,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat() if hasattr(msg, "timestamp") else None,
                    "user_id": msg.user_id
                }
                for msg in recent_messages
            ]
        }
    
    def format_messages_for_context(
        self, 
        messages: List[Message], 
        include_timestamps: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Format a list of messages for inclusion in memory context.
        
        Args:
            messages: List of Message objects to format
            include_timestamps: Whether to include timestamps in the output
            
        Returns:
            List of formatted message dictionaries
        """
        formatted_messages = []
        
        for msg in messages:
            message_dict = {
                "content": msg.content,
                "user_id": msg.user_id
            }
            
            if include_timestamps and hasattr(msg, "timestamp"):
                message_dict["timestamp"] = msg.timestamp.isoformat()
                
            formatted_messages.append(message_dict)
            
        return formatted_messages
