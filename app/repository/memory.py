from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, case, cast, Float
from app.models import User, Message, Topic, MessageTopic, Conversation, UserFact
from typing import List, Optional, Tuple, Dict
import re

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
        
    def get_facts_with_relevance(self, user_id: int, query: str, limit: int = 10) -> List[Tuple[UserFact, float]]:
        """
        Get user facts with relevance scores based on a query.
        
        Args:
            user_id: User ID to retrieve facts for
            query: Search query to evaluate relevance against
            limit: Maximum number of facts to return
            
        Returns:
            List of (UserFact, score) tuples, sorted by relevance score in descending order
        """
        # Define fact type priority weights (can be adjusted based on importance)
        fact_type_weights = {
            'job': 1.5,
            'location': 1.3,
            'family': 1.4,
            'interests': 1.2,
            'preferences': 1.1,
            'pets': 1.0
        }
        
        # Default weight for fact types not in the dictionary
        default_weight = 1.0
        
        # Clean query for matching (lowercase, remove punctuation)
        clean_query = re.sub(r'[^\w\s]', '', query.lower())
        query_terms = clean_query.split()
        
        # Prepare the query with custom scoring
        # Get all user facts without type weighting for now
        # We'll apply type weights in Python for more flexibility
        facts_query = (
            self.db.query(UserFact)
            .filter(UserFact.user_id == user_id)
            .all()
        )
        
        # Process facts with scoring logic in Python for more flexibility
        scored_facts = []
        for fact in facts_query:
            # Clean fact value for matching
            clean_value = re.sub(r'[^\w\s]', '', fact.value.lower())
            
            # Calculate text match score
            text_match_score = 0.0
            
            # Direct match bonus (if query matches fact exactly)
            if clean_query in clean_value or clean_value in clean_query:
                text_match_score += 3.0
            
            # Term match scoring
            value_terms = clean_value.split()
            for term in query_terms:
                if term in value_terms:
                    text_match_score += 1.0
                # Partial term matching
                else:
                    for value_term in value_terms:
                        if term in value_term or value_term in term:
                            # Longer partial matches score higher
                            overlap = min(len(term), len(value_term))
                            max_len = max(len(term), len(value_term))
                            if max_len > 0:  # Avoid division by zero
                                text_match_score += 0.5 * (overlap / max_len)
            
            # Special case for family queries
            if 'kids' in query_terms or 'children' in query_terms:
                if fact.fact_type == 'family':
                    text_match_score += 2.0
            
            # Normalize by the number of terms to avoid bias toward longer text
            if len(query_terms) > 0:
                text_match_score = text_match_score / len(query_terms)
            
            # Get the type weight
            type_weight = fact_type_weights.get(fact.fact_type, default_weight)
            
            # Calculate final score: type_weight * text_match_score
            final_score = type_weight * text_match_score
            
            # Only include facts with a non-zero score
            if final_score > 0:
                scored_facts.append((fact, final_score))
        
        # Sort by score in descending order and limit results
        scored_facts.sort(key=lambda x: x[1], reverse=True)
        return scored_facts[:limit]

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
