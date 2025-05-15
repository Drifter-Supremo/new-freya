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
        - Adjust relevance scores based on query content

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

        # 1. Prioritize user facts based on query topics
        if memory_context["user_facts"] and query_topics:
            memory_context["user_facts"] = self._prioritize_facts_by_topics(
                memory_context["user_facts"],
                query_topics
            )

        # 2. Filter and prioritize recent memories based on query content
        if memory_context["recent_memories"]:
            memory_context["recent_memories"] = self._prioritize_recent_memories(
                memory_context["recent_memories"],
                query
            )

        # 3. Adjust topic memories based on query topics
        if memory_context["topic_memories"]:
            memory_context["topic_memories"] = self._prioritize_topic_memories(
                memory_context["topic_memories"],
                query_topics
            )

        # 4. Add memory query type classification
        memory_context["memory_query_type"] = self._classify_memory_query_type(query)

        return memory_context

    def _prioritize_facts_by_topics(self, facts: List[Dict[str, Any]], topics: List[str]) -> List[Dict[str, Any]]:
        """
        Prioritize user facts based on query topics.

        Args:
            facts: List of user facts
            topics: List of topics extracted from the query

        Returns:
            Prioritized list of user facts
        """
        # Convert topics to lowercase for case-insensitive matching
        topics_lower = [topic.lower() for topic in topics]

        # Score each fact based on relevance to topics
        scored_facts = []
        for fact in facts:
            score = fact.get("confidence", 0)  # Start with existing confidence

            # Boost score if fact type matches a topic
            if fact["type"].lower() in topics_lower:
                score += 30

            # Boost score if fact value contains a topic
            for topic in topics_lower:
                if topic in fact["value"].lower():
                    score += 20
                    break

            # Add the fact with its new score
            fact_copy = fact.copy()
            fact_copy["confidence"] = min(100, score)  # Cap at 100
            scored_facts.append((fact_copy, score))

        # Sort by score (descending) and return the facts
        scored_facts.sort(key=lambda x: x[1], reverse=True)
        return [fact for fact, _ in scored_facts]

    def _prioritize_recent_memories(self, memories: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        Filter and prioritize recent memories based on query content.

        Args:
            memories: List of recent memories
            query: The user query

        Returns:
            Filtered and prioritized list of recent memories
        """
        # Clean query for matching
        query_lower = query.lower()
        query_terms = re.sub(r'[^\w\s]', ' ', query_lower).split()

        # Score each memory based on relevance to query
        scored_memories = []
        for memory in memories:
            content_lower = memory.get("content", "").lower()

            # Base score - more recent messages get higher base score
            # Assuming memories are already sorted by recency (newest first)
            base_score = 50

            # Calculate term match score
            term_match_score = 0
            for term in query_terms:
                if term in content_lower and len(term) > 3:  # Only consider meaningful terms
                    term_match_score += 10

            # Calculate exact phrase match score
            phrase_match_score = 0
            for i in range(len(query_terms) - 1):
                phrase = f"{query_terms[i]} {query_terms[i+1]}"
                if phrase in content_lower:
                    phrase_match_score += 15

            # Calculate final score
            final_score = base_score + term_match_score + phrase_match_score

            # Only include memories with a minimum score
            if final_score > 50:  # Only include if it has some relevance
                memory_copy = memory.copy()
                memory_copy["relevance"] = min(100, final_score)  # Cap at 100
                scored_memories.append((memory_copy, final_score))

        # If we have too few memories, include some regardless of score
        if len(scored_memories) < 3 and memories:
            for memory in memories[:3]:
                if not any(m[0].get("content") == memory.get("content") for m in scored_memories):
                    memory_copy = memory.copy()
                    memory_copy["relevance"] = 50  # Default relevance
                    scored_memories.append((memory_copy, 50))

        # Sort by score (descending) and return the memories
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        return [memory for memory, _ in scored_memories[:5]]  # Limit to top 5

    def _prioritize_topic_memories(self, topic_memories: List[Dict[str, Any]], query_topics: List[str]) -> List[Dict[str, Any]]:
        """
        Adjust topic memories based on query topics.

        Args:
            topic_memories: List of topic memories
            query_topics: List of topics extracted from the query

        Returns:
            Adjusted list of topic memories
        """
        # Convert query topics to lowercase for case-insensitive matching
        query_topics_lower = [topic.lower() for topic in query_topics]

        # Score each topic memory based on relevance to query topics
        scored_topic_memories = []
        for topic_memory in topic_memories:
            topic_name = topic_memory.get("topic", {}).get("name", "").lower()
            base_score = topic_memory.get("topic", {}).get("relevance", 0)

            # Boost score if topic name matches a query topic
            if topic_name in query_topics_lower:
                base_score += 30

            # Boost score for partial matches
            for query_topic in query_topics_lower:
                if query_topic in topic_name or topic_name in query_topic:
                    base_score += 15
                    break

            # Add the topic memory with its new score
            topic_memory_copy = topic_memory.copy()
            topic_memory_copy["topic"] = topic_memory["topic"].copy()
            topic_memory_copy["topic"]["relevance"] = min(100, base_score)  # Cap at 100
            scored_topic_memories.append((topic_memory_copy, base_score))

        # Sort by score (descending) and return the topic memories
        scored_topic_memories.sort(key=lambda x: x[1], reverse=True)
        return [topic_memory for topic_memory, _ in scored_topic_memories]

    def _classify_memory_query_type(self, query: str) -> str:
        """
        Classify the type of memory query.

        Args:
            query: The user query

        Returns:
            Memory query type classification
        """
        query_lower = query.lower()

        # Check for specific memory query types
        if re.search(r'(?i)do you remember', query_lower):
            return "recall_verification"
        elif re.search(r'(?i)what did (i|we|you) (say|tell|ask|talk|mention)', query_lower):
            return "content_recall"
        elif re.search(r'(?i)when did (i|we) (discuss|talk about|mention|say)', query_lower):
            return "temporal_recall"
        elif re.search(r'(?i)have (i|we) (talked|spoken|discussed|mentioned)', query_lower):
            return "existence_verification"
        elif re.search(r'(?i)what do you know about my', query_lower):
            return "knowledge_query"
        elif re.search(r'(?i)(last time|previously|earlier|before)', query_lower):
            return "previous_conversation"
        elif re.search(r'(?i)(didn\'t|did) (i|we) (talk|speak|discuss|mention|tell)', query_lower):
            return "fact_checking"
        else:
            return "general_memory_query"


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
