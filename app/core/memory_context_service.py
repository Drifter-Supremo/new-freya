"""
memory_context_service.py - Service for assembling memory context for chat completions.
"""

import re
from typing import Dict, List, Any, Optional, Tuple, Set
from sqlalchemy.orm import Session
from app.core.user_fact_service import get_relevant_facts_for_context, format_facts_for_context
from app.core.conversation_history_service import ConversationHistoryService
from app.repository.memory import MemoryQueryRepository
from app.services.topic_memory_service import TopicMemoryService
from app.services.topic_extraction import TopicExtractor


class MemoryContextBuilder:
    """
    Service for building memory context for chat completions.

    This class provides functionality for:
    - Detecting memory-related queries
    - Extracting topics from queries
    - Assembling relevant memory context
    - Prioritizing memories based on query relevance
    """

    # Memory query patterns for detecting when a user is asking about past conversations
    MEMORY_QUERY_PATTERNS = [
        # Direct memory questions
        re.compile(r'(?i)do you remember (when|what|how|where|why|who|if|that|about|our|my|the)', re.IGNORECASE),
        re.compile(r'(?i)what did (i|we|you) (say|tell|ask|talk|mention) (about|regarding|concerning)', re.IGNORECASE),
        re.compile(r'(?i)(what|when) did (i|we) (discuss|talk about|mention|say)', re.IGNORECASE),
        re.compile(r'(?i)have (i|we) (talked|spoken|discussed|mentioned) (about|regarding)', re.IGNORECASE),
        re.compile(r'(?i)(tell|remind) me (about|what|when|how|where|why) (i|we|you) (said|mentioned|talked about)', re.IGNORECASE),

        # Recall requests
        re.compile(r'(?i)(recall|remember|recollect) (our|the|that|when|what|how|where|why|who)', re.IGNORECASE),
        re.compile(r'(?i)(bring up|reference) (what|when|how|where|why|who|that|our|the)', re.IGNORECASE),

        # Topic-specific recall
        re.compile(r'(?i)what (did|do) you know about my', re.IGNORECASE),  # More general pattern for "what do you know about my X"
        re.compile(r'(?i)what (have|did) (i|we) (say|tell you|mention) about (my|our|the)', re.IGNORECASE),

        # Previous conversation references
        re.compile(r'(?i)(last time|previously|earlier|before) (we|you|i) (talked|spoke|discussed|mentioned|said)', re.IGNORECASE),
        re.compile(r'(?i)(in|during) (our|a) (previous|past|last|earlier|recent) (conversation|discussion|chat)', re.IGNORECASE),

        # Fact checking
        re.compile(r'(?i)(didn\'t|did) (i|we) (talk|speak|discuss|mention|tell you) (about|that|how|when|where|why)', re.IGNORECASE),
        re.compile(r'(?i)am i (right|correct) (that|when i say) (you|we|i)', re.IGNORECASE),

        # Additional patterns for knowledge questions
        re.compile(r'(?i)what do you know about (my|our|the)', re.IGNORECASE),  # Direct "what do you know about" questions
        re.compile(r'(?i)tell me what you know about (my|our|the)', re.IGNORECASE)
    ]

    # Topic extraction keywords for memory queries
    MEMORY_TOPIC_KEYWORDS = {
        "family": ["family", "parent", "father", "mother", "dad", "mom", "brother", "sister", "sibling",
                  "child", "son", "daughter", "grandparent", "grandmother", "grandfather", "aunt", "uncle",
                  "cousin", "niece", "nephew", "wife", "husband", "spouse", "partner"],
        "work": ["job", "work", "career", "company", "boss", "office", "colleague", "coworker", "project",
                "deadline", "meeting", "interview", "promotion", "salary", "profession", "business"],
        "health": ["health", "sick", "illness", "disease", "doctor", "hospital", "symptom", "medicine",
                  "pain", "injury", "exercise", "diet", "sleep", "stress", "anxiety", "depression"],
        "hobbies": ["hobby", "interest", "game", "sport", "book", "movie", "music", "art", "travel",
                   "cooking", "reading", "writing", "painting", "drawing", "photography", "gardening"],
        "education": ["school", "college", "university", "degree", "class", "course", "study", "student",
                     "teacher", "professor", "education", "learning", "grade", "exam", "test", "assignment"],
        "location": ["home", "house", "apartment", "city", "town", "state", "country", "address",
                    "neighborhood", "street", "location", "place", "area", "region", "live", "living"]
    }

    def __init__(self, db: Session):
        """
        Initialize the MemoryContextBuilder with a database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.memory_repo = MemoryQueryRepository(db)
        self.conversation_history_service = ConversationHistoryService(db)
        self.topic_memory_service = TopicMemoryService(db)
        self.topic_extractor = TopicExtractor()

    def is_memory_query(self, query: str) -> bool:
        """
        Detect if a query is asking about past conversations or memories.

        Args:
            query: The user query to analyze

        Returns:
            True if the query is memory-related, False otherwise
        """
        # Check against memory query patterns
        for pattern in self.MEMORY_QUERY_PATTERNS:
            if pattern.search(query):
                return True

        # Check for memory-related keywords
        memory_keywords = ["remember", "recall", "forget", "memory", "mentioned",
                          "told", "said", "talked about", "discussed", "conversation"]

        query_lower = query.lower()
        for keyword in memory_keywords:
            if keyword in query_lower:
                return True

        return False

    def extract_topics_from_query(self, query: str, top_n: int = 3) -> List[str]:
        """
        Extract potential topics from a query.

        Args:
            query: The user query to analyze
            top_n: Maximum number of topics to extract

        Returns:
            List of potential topic names
        """
        # First, use the TopicExtractor to get topics
        extracted_topics = self.topic_extractor.extract_topics(query, top_n=top_n)

        # If no topics found, try direct keyword matching
        if not extracted_topics:
            query_lower = query.lower()
            matched_topics = []

            for topic, keywords in self.MEMORY_TOPIC_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in query_lower:
                        matched_topics.append(topic)
                        break

            # Return unique topics
            return list(set(matched_topics))[:top_n]

        return extracted_topics

    def assemble_memory_context(self, user_id: int, query: str, use_advanced_scoring: bool = True) -> Dict[str, Any]:
        """
        Assemble a complete memory context for a chat completion request.

        This includes:
        - Relevant user facts with confidence scores
        - Recent conversation history
        - Topic-related memories with advanced relevance scoring

        Args:
            user_id: User ID to retrieve memory for
            query: The current user query
            use_advanced_scoring: Whether to use advanced topic relevance scoring (default: True)

        Returns:
            Dict containing structured memory context
        """
        memory_context = {
            "user_facts": [],
            "recent_memories": [],
            "topic_memories": [],
            "is_memory_query": self.is_memory_query(query)
        }

        # 1. Get and format relevant user facts
        relevant_facts = get_relevant_facts_for_context(self.db, user_id, query, limit=5)
        memory_context["user_facts"] = format_facts_for_context(relevant_facts)

        # 2. Get recent memories using the conversation history service
        recent_messages = self.conversation_history_service.get_recent_messages_across_conversations(
            user_id=user_id,
            limit=10,
            max_age_days=30  # Only include messages from the last 30 days
        )
        memory_context["recent_memories"] = self.conversation_history_service.format_messages_for_context(
            messages=recent_messages,
            include_timestamps=True
        )

        # 3. Get topic-related memories using the topic memory service
        topic_context = self.topic_memory_service.get_memory_context_by_query(
            user_id=user_id,
            query=query,
            topic_limit=3,
            message_limit=3,
            use_advanced_scoring=use_advanced_scoring
        )

        memory_context["topic_memories"] = topic_context["topic_memories"]

        # 4. If this is a memory query, prioritize memories
        if memory_context["is_memory_query"]:
            memory_context = self._prioritize_memories_for_memory_query(memory_context, query)

        return memory_context

    def _prioritize_memories_for_memory_query(self, memory_context: Dict[str, Any], query: str) -> Dict[str, Any]:
        """
        Adjust memory context for memory-specific queries.

        For memory queries, we want to:
        - Increase the number of topic memories
        - Prioritize recent memories that match the query
        - Add a memory_query_topics field with extracted topics

        Args:
            memory_context: The current memory context
            query: The user query

        Returns:
            Updated memory context with prioritized memories
        """
        # Extract topics from the query
        query_topics = self.extract_topics_from_query(query, top_n=5)

        # Add the extracted topics to the context
        memory_context["memory_query_topics"] = query_topics

        # For memory queries, we might want to add additional context or processing here

        return memory_context


# For backward compatibility, keep the function-based approach
def assemble_memory_context(db: Session, user_id: int, query: str, use_advanced_scoring: bool = True) -> Dict[str, Any]:
    """
    Assemble a complete memory context for a chat completion request.

    This is a wrapper around the MemoryContextBuilder class for backward compatibility.

    Args:
        db: Database session
        user_id: User ID to retrieve memory for
        query: The current user query
        use_advanced_scoring: Whether to use advanced topic relevance scoring (default: True)

    Returns:
        Dict containing structured memory context
    """
    builder = MemoryContextBuilder(db)
    return builder.assemble_memory_context(user_id, query, use_advanced_scoring)
