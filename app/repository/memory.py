from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, case, cast, Float, desc, and_, or_
from app.models import User, Message, Topic, MessageTopic, Conversation, UserFact
from typing import List, Optional, Tuple, Dict, Set
import re
from collections import defaultdict
from datetime import datetime, timedelta

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

    def get_topics_with_advanced_relevance(self, user_id: int, query: str, limit: int = 10) -> List[Tuple[Topic, float]]:
        """
        Get topics with advanced relevance scoring based on multiple factors.

        This method implements a more sophisticated relevance scoring algorithm that considers:
        1. Full-text search relevance (PostgreSQL ts_rank)
        2. Topic frequency (how often the topic appears in user messages)
        3. Recency (more recent topics get higher scores)
        4. Direct keyword matches between query and topic name

        Args:
            user_id: User ID to retrieve topics for
            query: Search query to evaluate relevance against
            limit: Maximum number of topics to return

        Returns:
            List of (Topic, score) tuples, sorted by relevance score in descending order
        """
        # First, get base relevance from PostgreSQL full-text search
        base_results = self.search_topics_by_message_content(user_id, query, limit=20)

        # If no results from full-text search, try direct topic name matching
        if not base_results:
            # Get all topics for the user
            all_topics = self.get_topics_for_user(user_id)

            # Clean query for matching
            clean_query = re.sub(r'[^\w\s]', '', query.lower())
            query_terms = clean_query.split()

            # Score topics based on direct name matching
            scored_topics = []
            for topic in all_topics:
                score = 0.0

                # Direct match bonus (if query contains topic name or vice versa)
                topic_name_lower = topic.name.lower()
                if topic_name_lower in clean_query or clean_query in topic_name_lower:
                    score += 2.0

                # Term match scoring
                for term in query_terms:
                    if term in topic_name_lower:
                        score += 1.0
                    # Partial term matching
                    elif any(term in word or word in term for word in topic_name_lower.split()):
                        score += 0.5

                if score > 0:
                    scored_topics.append((topic, score))

            # Sort by score and return limited results
            scored_topics.sort(key=lambda x: x[1], reverse=True)
            return scored_topics[:limit]

        # Process the base results with additional scoring factors
        topic_scores = {}
        for topic, base_score in base_results:
            # Start with the base score from full-text search
            topic_scores[topic.id] = base_score

        # Get topic frequency (count of messages per topic)
        topic_ids = [topic.id for topic, _ in base_results]
        topic_counts = (
            self.db.query(
                MessageTopic.topic_id,
                func.count(MessageTopic.message_id).label('message_count')
            )
            .filter(
                MessageTopic.topic_id.in_(topic_ids),
                MessageTopic.message_id.in_(
                    self.db.query(Message.id)
                    .filter(Message.user_id == user_id)
                )
            )
            .group_by(MessageTopic.topic_id)
            .all()
        )

        # Calculate frequency factor (normalized to 0-1 range)
        max_count = max([count for _, count in topic_counts]) if topic_counts else 1
        for topic_id, count in topic_counts:
            # Add frequency factor (normalized to 0-0.5 range)
            if topic_id in topic_scores:
                topic_scores[topic_id] += 0.5 * (count / max_count)

        # Get recency factor (most recent message timestamp per topic)
        recent_messages = (
            self.db.query(
                MessageTopic.topic_id,
                func.max(Message.timestamp).label('latest_timestamp')
            )
            .join(Message, Message.id == MessageTopic.message_id)
            .filter(
                MessageTopic.topic_id.in_(topic_ids),
                Message.user_id == user_id
            )
            .group_by(MessageTopic.topic_id)
            .all()
        )

        # Calculate recency factor
        now = datetime.now()
        for topic_id, latest_timestamp in recent_messages:
            if topic_id in topic_scores and latest_timestamp:
                # Calculate days since the latest message
                days_ago = (now - latest_timestamp).days
                # More recent topics get higher scores (max 0.5 for today, decreasing over time)
                recency_factor = max(0, 0.5 - (days_ago * 0.05))  # Decrease by 0.05 per day
                topic_scores[topic_id] += recency_factor

        # Add direct keyword matching between query and topic name
        clean_query = re.sub(r'[^\w\s]', '', query.lower())
        query_terms = clean_query.split()

        for topic, _ in base_results:
            topic_name_lower = topic.name.lower()

            # Direct match bonus
            if topic_name_lower in clean_query or clean_query in topic_name_lower:
                topic_scores[topic.id] += 1.0

            # Term match scoring
            for term in query_terms:
                if term in topic_name_lower:
                    topic_scores[topic.id] += 0.5

        # Create final scored results
        final_results = []
        for topic, _ in base_results:
            final_results.append((topic, topic_scores[topic.id]))

        # Sort by final score and return limited results
        final_results.sort(key=lambda x: x[1], reverse=True)
        return final_results[:limit]
