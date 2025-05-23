"""
firebase_memory_service.py - Service for retrieving memory context from Firebase/Firestore

This service provides the same functionality as the existing memory context service,
but retrieves data from Firestore instead of PostgreSQL.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta, timezone
import logging

from app.services.firebase_service import FirebaseService
from app.services.topic_extraction import TopicExtractor
from app.core.config import logger
from app.core.firebase_config import COLLECTIONS

class FirebaseMemoryService:
    """
    Service for retrieving memory context from Firestore.
    
    This service provides methods for:
    - Retrieving user facts
    - Retrieving conversation history
    - Retrieving topic memories
    - Building comprehensive memory context
    """
    
    # Memory query patterns for detecting when a user is asking about past conversations
    MEMORY_QUERY_PATTERNS = [
        re.compile(r'(?i)do you remember (when|what|how|where|why|who|if|that|about|our|my|the)', re.IGNORECASE),
        re.compile(r'(?i)what did (i|we|you) (say|tell|ask|talk|mention) (about|regarding|concerning)', re.IGNORECASE),
        re.compile(r'(?i)(what|when) did (i|we) (discuss|talk about|mention|say)', re.IGNORECASE),
        re.compile(r'(?i)have (i|we) (talked|spoken|discussed|mentioned) (about|regarding)', re.IGNORECASE),
        re.compile(r'(?i)(tell|remind) me (about|what|when|how|where|why) (i|we|you) (said|mentioned|talked about)', re.IGNORECASE),
        re.compile(r'(?i)(recall|remember|recollect) (our|the|that|when|what|how|where|why|who)', re.IGNORECASE),
        re.compile(r'(?i)(bring up|reference) (what|when|how|where|why|who|that|our|the)', re.IGNORECASE),
        re.compile(r'(?i)what (did|do) you know about my', re.IGNORECASE),
        re.compile(r'(?i)what (have|did) (i|we) (say|tell you|mention) about (my|our|the)', re.IGNORECASE),
        re.compile(r'(?i)(last time|previously|earlier|before) (we|you|i) (talked|spoke|discussed|mentioned|said)', re.IGNORECASE),
        re.compile(r'(?i)(in|during) (our|a) (previous|past|last|earlier|recent) (conversation|discussion|chat)', re.IGNORECASE),
        re.compile(r'(?i)(didn\'t|did) (i|we) (talk|speak|discuss|mention|tell you) (about|that|how|when|where|why)', re.IGNORECASE),
        re.compile(r'(?i)am i (right|correct) (that|when i say) (you|we|i)', re.IGNORECASE),
        re.compile(r'(?i)what do you know about (my|our|the)', re.IGNORECASE),
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
    
    def __init__(self):
        """
        Initialize the FirebaseMemoryService.
        """
        self.firebase = FirebaseService()
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
    
    def get_user_facts(self, user_id: str, query: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get user facts with optional relevance filtering.
        
        Based on your Firestore structure, userFacts has:
        - timestamp: date
        - type: string (e.g., "interests")
        - value: string (e.g., "it!")
        
        Args:
            user_id: User ID (e.g., "Sencere")
            query: Optional query to filter facts by relevance
            limit: Maximum number of facts to return
            
        Returns:
            List of user facts
        """
        # Get all facts (we'll filter by user ID if that field exists)
        facts = self.firebase.get_user_facts(user_id)
        
        logger.info(f"Retrieved {len(facts)} facts from Firestore for user {user_id}")
        
        # If no query provided, return facts directly
        if not query:
            return facts[:limit]
        
        # Otherwise, score facts by relevance to query
        scored_facts = self._score_facts_by_relevance(facts, query)
        
        # Sort by score and return limited results
        scored_facts.sort(key=lambda x: x[1], reverse=True)
        return [fact for fact, _ in scored_facts[:limit]]
    
    def _score_facts_by_relevance(self, facts: List[Dict[str, Any]], query: str) -> List[Tuple[Dict[str, Any], float]]:
        """
        Score facts by relevance to a query.
        
        Args:
            facts: List of fact dictionaries
            query: Query to score against
            
        Returns:
            List of (fact, score) tuples
        """
        # Define fact type priority weights
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
        
        # Clean query for matching
        clean_query = re.sub(r'[^\w\s]', '', query.lower())
        query_terms = clean_query.split()
        
        # Score facts
        scored_facts = []
        for fact in facts:
            fact_type = fact.get('type', '')
            fact_value = fact.get('value', '')
            
            # Clean fact value for matching
            clean_value = re.sub(r'[^\w\s]', '', fact_value.lower())
            
            # Calculate text match score
            text_match_score = 0.0
            
            # Direct match bonus
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
                            if max_len > 0:
                                text_match_score += 0.5 * (overlap / max_len)
            
            # Special case for family queries
            if 'kids' in query_terms or 'children' in query_terms:
                if fact_type == 'family':
                    text_match_score += 2.0
            
            # Normalize by the number of terms
            if len(query_terms) > 0:
                text_match_score = text_match_score / len(query_terms)
            
            # Get the type weight
            type_weight = fact_type_weights.get(fact_type, default_weight)
            
            # Calculate final score
            final_score = type_weight * text_match_score
            
            # Only include facts with a non-zero score
            if final_score > 0:
                scored_facts.append((fact, final_score))
        
        return scored_facts
    
    def get_recent_messages(self, user_id: str, limit: int = 20, max_age_days: int = 30) -> List[Dict[str, Any]]:
        """
        Get recent messages across all conversations for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of messages to return
            max_age_days: Only include messages from the last N days
            
        Returns:
            List of recent messages
        """
        # Get recent conversations for the user
        conversations = self.firebase.get_user_conversations(user_id, limit=10)
        
        # Calculate cutoff date (make it timezone-aware)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        
        # Collect messages from each conversation
        all_messages = []
        for conv in conversations:
            conv_id = conv.get('id')
            messages = self.firebase.get_conversation_messages(conv_id, limit=10)
            
            # Filter by timestamp if available
            for msg in messages:
                timestamp = msg.get('timestamp')
                if timestamp:
                    # Convert timestamp to datetime if needed
                    if not isinstance(timestamp, datetime):
                        if hasattr(timestamp, 'seconds'):
                            # Convert Firestore timestamp to datetime (UTC)
                            timestamp = datetime.fromtimestamp(timestamp.seconds, tz=timezone.utc)
                    else:
                        # If it's already a datetime, ensure it has timezone info
                        if timestamp.tzinfo is None:
                            # Assume UTC for naive datetime
                            timestamp = timestamp.replace(tzinfo=timezone.utc)
                    
                    # Check if message is within cutoff
                    if timestamp > cutoff_date:
                        # Add conversation info to message
                        msg['conversation_id'] = conv_id
                        all_messages.append(msg)
                else:
                    # If no timestamp, include anyway
                    msg['conversation_id'] = conv_id
                    all_messages.append(msg)
        
        # Sort messages by timestamp (newest first)
        all_messages.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        # Return limited results
        return all_messages[:limit]
    
    def get_topic_memories(self, user_id: str, query: str, topic_limit: int = 3, message_limit: int = 3) -> List[Dict[str, Any]]:
        """
        Get topic memories for a user based on a query.
        
        Args:
            user_id: User ID
            query: Query string
            topic_limit: Maximum number of topics to return
            message_limit: Maximum number of messages per topic
            
        Returns:
            List of topic memories
        """
        # Get all topics for the user
        topics = self.firebase.get_user_topics(user_id)
        
        # If no topics, return empty list
        if not topics:
            return []
        
        # Score topics by relevance to query
        scored_topics = self._score_topics_by_relevance(topics, query)
        
        # Sort by score and limit
        scored_topics.sort(key=lambda x: x[1], reverse=True)
        top_topics = [topic for topic, _ in scored_topics[:topic_limit]]
        
        # Get messages for each topic
        topic_memories = []
        for topic in top_topics:
            topic_id = topic.get('id')
            topic_name = topic.get('name', '')
            
            # Get messages for this topic
            messages = self.firebase.query_collection(
                COLLECTIONS['messages'],
                filters=[('topicIds', 'array_contains', topic_id)],
                order_by='timestamp',
                desc=True,
                limit=message_limit
            )
            
            # Add to topic memories
            topic_memories.append({
                'topic': {
                    'id': topic_id,
                    'name': topic_name,
                    'relevance': min(100, int(topic.get('relevance_score', 0) * 100))
                },
                'messages': messages
            })
        
        return topic_memories
    
    def _score_topics_by_relevance(self, topics: List[Dict[str, Any]], query: str) -> List[Tuple[Dict[str, Any], float]]:
        """
        Score topics by relevance to a query.
        
        Args:
            topics: List of topic dictionaries
            query: Query to score against
            
        Returns:
            List of (topic, score) tuples
        """
        # Clean query for matching
        clean_query = re.sub(r'[^\w\s]', '', query.lower())
        query_terms = clean_query.split()
        
        # Extract topics from query
        query_topics = self.extract_topics_from_query(query, top_n=5)
        query_topics_lower = [t.lower() for t in query_topics]
        
        # Score topics
        scored_topics = []
        for topic in topics:
            topic_name = topic.get('name', '').lower()
            base_score = 0.5  # Base score for all topics
            
            # Direct topic match bonus
            if topic_name in query_topics_lower:
                base_score += 3.0
            
            # Partial topic match
            for q_topic in query_topics_lower:
                if q_topic in topic_name or topic_name in q_topic:
                    base_score += 1.5
                    break
            
            # Term match scoring
            for term in query_terms:
                if term in topic_name:
                    base_score += 1.0
                # Partial term matching
                elif any(term in word or word in term for word in topic_name.split()):
                    base_score += 0.5
            
            # Add recency factor if available
            if 'lastUsed' in topic:
                last_used = topic['lastUsed']
                # Convert to datetime if needed
                if not isinstance(last_used, datetime):
                    if hasattr(last_used, 'seconds'):
                        last_used = datetime.fromtimestamp(last_used.seconds, tz=timezone.utc)
                else:
                    # If it's already a datetime, ensure it has timezone info
                    if last_used.tzinfo is None:
                        last_used = last_used.replace(tzinfo=timezone.utc)
                
                # Calculate days since last used
                days_ago = (datetime.now(timezone.utc) - last_used).days
                # More recent topics get higher scores
                recency_factor = max(0, 0.5 - (days_ago * 0.05))  # Decrease by 0.05 per day
                base_score += recency_factor
            
            # Add to scored topics if score is positive
            if base_score > 0:
                # Add score to topic for later use
                topic_copy = topic.copy()
                topic_copy['relevance_score'] = base_score
                scored_topics.append((topic_copy, base_score))
        
        return scored_topics
    
    def assemble_memory_context(self, user_id: str, query: str) -> Dict[str, Any]:
        """
        Assemble a complete memory context for a chat completion request.
        
        Args:
            user_id: User ID to retrieve memory for
            query: The current user query
            
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
        user_facts = self.get_user_facts(user_id, query, limit=5)
        for fact in user_facts:
            memory_context["user_facts"].append({
                "type": fact.get('type', ''),
                "value": fact.get('value', ''),
                "confidence": fact.get('confidence', 70)  # Default confidence
            })
        
        # 2. Get recent memories
        recent_messages = self.get_recent_messages(user_id, limit=10, max_age_days=30)
        for msg in recent_messages:
            memory_context["recent_memories"].append({
                "content": msg.get('content', ''),
                "user_id": msg.get('userId', ''),
                "timestamp": msg.get('timestamp', '')
            })
        
        # 3. Get topic-related memories
        topic_results = self.get_topic_memories(user_id, query, topic_limit=3, message_limit=3)
        memory_context["topic_memories"] = []
        
        for topic_memory in topic_results:
            topic_dict = topic_memory.get('topic', {})
            messages = topic_memory.get('messages', [])
            
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "content": msg.get('content', ''),
                    "user_id": msg.get('userId', ''),
                    "timestamp": msg.get('timestamp', '')
                })
            
            memory_context["topic_memories"].append({
                "topic": topic_dict,
                "messages": formatted_messages
            })
        
        # 4. If this is a memory query, prioritize memories
        if memory_context["is_memory_query"]:
            memory_context = self._prioritize_memories_for_memory_query(memory_context, query)
        
        # 5. Format the memory context
        formatted_context = self.format_memory_context(memory_context, query)
        memory_context["formatted_context"] = formatted_context
        
        return memory_context
    
    def _prioritize_memories_for_memory_query(self, memory_context: Dict[str, Any], query: str) -> Dict[str, Any]:
        """
        Adjust memory context for memory-specific queries.
        
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
        
        # Classify the memory query type
        memory_context["memory_query_type"] = self._classify_memory_query_type(query)
        
        return memory_context
    
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
    
    def format_memory_context(self, memory_context: Dict[str, Any], query: str = "") -> str:
        """
        Format the memory context for chat completion.
        
        This creates a structured text representation of the memory context
        that can be included in the chat completion prompt.
        
        Args:
            memory_context: The memory context to format
            query: The user query (optional)
            
        Returns:
            Formatted memory context as a string
        """
        is_memory_query = memory_context.get("is_memory_query", False)
        memory_query_type = memory_context.get("memory_query_type", "general_memory_query")
        
        # Start with a header
        formatted_context = "### Memory Context ###\n\n"
        
        # Format user facts if available
        if memory_context["user_facts"]:
            formatted_context += self._format_user_facts(memory_context["user_facts"])
        
        # Format memories based on query type
        if is_memory_query:
            # For memory queries, format based on the query type
            if memory_query_type in ["recall_verification", "content_recall", "fact_checking"]:
                # For recall questions, prioritize topic memories and recent memories
                formatted_context += self._format_topic_memories_for_recall(memory_context["topic_memories"])
                formatted_context += self._format_recent_memories_for_recall(memory_context["recent_memories"])
                
            elif memory_query_type in ["temporal_recall", "previous_conversation"]:
                # For temporal questions, focus on when things were discussed
                formatted_context += self._format_memories_with_timestamps(
                    memory_context["recent_memories"],
                    memory_context["topic_memories"]
                )
                
            elif memory_query_type == "existence_verification":
                # For existence verification, provide a simple yes/no with evidence
                formatted_context += self._format_memories_for_existence_verification(
                    memory_context["topic_memories"],
                    memory_context["recent_memories"],
                    memory_context.get("memory_query_topics", [])
                )
                
            elif memory_query_type == "knowledge_query":
                # For knowledge queries, focus on facts and topic memories
                formatted_context += self._format_memories_for_knowledge_query(
                    memory_context["user_facts"],
                    memory_context["topic_memories"],
                    memory_context.get("memory_query_topics", [])
                )
                
            else:
                # Default formatting for other memory queries
                formatted_context += self._format_default_memory_context(memory_context)
        else:
            # For non-memory queries, use default formatting
            formatted_context += self._format_default_memory_context(memory_context)
            
        return formatted_context
    
    def _format_user_facts(self, facts: List[Dict[str, Any]]) -> str:
        """
        Format user facts for the memory context.
        
        Args:
            facts: List of user facts
            
        Returns:
            Formatted user facts as a string
        """
        if not facts:
            return ""
        
        formatted_facts = "## User Facts\n"
        
        # Sort facts by confidence (descending)
        sorted_facts = sorted(facts, key=lambda x: x.get("confidence", 0), reverse=True)
        
        # Format each fact
        for fact in sorted_facts:
            confidence = fact.get("confidence", 0)
            confidence_indicator = "★" * (1 + min(4, int(confidence / 20)))  # 1-5 stars based on confidence
            formatted_facts += f"- {fact['type'].capitalize()}: {fact['value']} {confidence_indicator}\n"
        
        return formatted_facts + "\n"
    
    def _format_topic_memories_for_recall(self, topic_memories: List[Dict[str, Any]]) -> str:
        """
        Format topic memories for recall-type queries.
        
        Args:
            topic_memories: List of topic memories
            
        Returns:
            Formatted topic memories as a string
        """
        if not topic_memories:
            return ""
        
        formatted_memories = "## Topic-Related Memories\n"
        
        # Sort topic memories by relevance (descending)
        sorted_topics = sorted(
            topic_memories,
            key=lambda x: x.get("topic", {}).get("relevance", 0),
            reverse=True
        )
        
        # Format each topic memory
        for topic_memory in sorted_topics:
            topic_name = topic_memory.get("topic", {}).get("name", "Unknown Topic")
            relevance = topic_memory.get("topic", {}).get("relevance", 0)
            
            # Only include topics with reasonable relevance
            if relevance < 30:
                continue
            
            formatted_memories += f"### {topic_name}\n"
            
            # Format messages for this topic
            messages = topic_memory.get("messages", [])
            if messages:
                for message in messages:
                    content = message.get("content", "")
                    formatted_memories += f"- {content}\n"
            
            formatted_memories += "\n"
        
        return formatted_memories
    
    def _format_recent_memories_for_recall(self, recent_memories: List[Dict[str, Any]]) -> str:
        """
        Format recent memories for recall-type queries.
        
        Args:
            recent_memories: List of recent memories
            
        Returns:
            Formatted recent memories as a string
        """
        if not recent_memories:
            return ""
        
        formatted_memories = "## Recent Conversation History\n"
        
        # Sort by relevance if available, otherwise assume they're already sorted by recency
        if recent_memories and "relevance" in recent_memories[0]:
            sorted_memories = sorted(
                recent_memories,
                key=lambda x: x.get("relevance", 0),
                reverse=True
            )
        else:
            sorted_memories = recent_memories
        
        # Format each memory
        for memory in sorted_memories[:5]:  # Limit to top 5
            content = memory.get("content", "")
            relevance = memory.get("relevance", 0)
            
            # Only include memories with reasonable relevance if relevance is available
            if "relevance" in memory and relevance < 30:
                continue
            
            formatted_memories += f"- {content}\n"
        
        return formatted_memories + "\n"
    
    def _format_memories_with_timestamps(self, recent_memories: List[Dict[str, Any]], topic_memories: List[Dict[str, Any]]) -> str:
        """
        Format memories with timestamps for temporal queries.
        
        Args:
            recent_memories: List of recent memories
            topic_memories: List of topic memories
            
        Returns:
            Formatted memories with timestamps as a string
        """
        if not recent_memories and not topic_memories:
            return ""
        
        formatted_memories = "## Conversation Timeline\n"
        
        # Collect all messages with timestamps
        all_messages = []
        
        # Add recent memories
        for memory in recent_memories:
            if "timestamp" in memory:
                all_messages.append({
                    "content": memory.get("content", ""),
                    "timestamp": memory.get("timestamp", ""),
                    "relevance": memory.get("relevance", 0)
                })
        
        # Add topic memories
        for topic_memory in topic_memories:
            topic_name = topic_memory.get("topic", {}).get("name", "")
            messages = topic_memory.get("messages", [])
            
            for message in messages:
                if "timestamp" in message:
                    all_messages.append({
                        "content": message.get("content", ""),
                        "timestamp": message.get("timestamp", ""),
                        "topic": topic_name,
                        "relevance": topic_memory.get("topic", {}).get("relevance", 0)
                    })
        
        # Sort by timestamp (newest first)
        sorted_messages = sorted(
            all_messages,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )
        
        # Format each message with timestamp
        for message in sorted_messages:
            content = message.get("content", "")
            timestamp = message.get("timestamp", "")
            topic = message.get("topic", "")
            
            # Format timestamp
            if timestamp:
                try:
                    # Convert ISO format to more readable format
                    if isinstance(timestamp, str):
                        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    elif isinstance(timestamp, datetime):
                        dt = timestamp
                    else:
                        # If it's a Firestore timestamp, convert to datetime
                        if hasattr(timestamp, 'seconds'):
                            dt = datetime.fromtimestamp(timestamp.seconds, tz=timezone.utc)
                        else:
                            dt = datetime.now(timezone.utc)  # Fallback
                    
                    formatted_date = dt.strftime("%b %d, %Y")
                    formatted_time = dt.strftime("%I:%M %p")
                    timestamp_str = f"{formatted_date} at {formatted_time}"
                except:
                    # If parsing fails, use the original timestamp
                    timestamp_str = str(timestamp)
            else:
                timestamp_str = "Unknown time"
            
            # Add topic if available
            topic_str = f" (Topic: {topic})" if topic else ""
            
            formatted_memories += f"- {timestamp_str}{topic_str}: {content}\n"
        
        return formatted_memories + "\n"
    
    def _format_memories_for_existence_verification(self, topic_memories: List[Dict[str, Any]], recent_memories: List[Dict[str, Any]], query_topics: List[str]) -> str:
        """
        Format memories for existence verification queries.
        
        Args:
            topic_memories: List of topic memories
            recent_memories: List of recent memories
            query_topics: List of topics extracted from the query
            
        Returns:
            Formatted memories for existence verification as a string
        """
        if not topic_memories and not recent_memories:
            return "## Memory Verification\nNo relevant memories found about this topic.\n\n"
        
        # Check if we have any relevant memories
        has_relevant_memories = False
        
        # Check topic memories
        for topic_memory in topic_memories:
            topic_name = topic_memory.get("topic", {}).get("name", "").lower()
            relevance = topic_memory.get("topic", {}).get("relevance", 0)
            
            # Check if topic is relevant to query
            if relevance >= 50 or any(query_topic.lower() in topic_name for query_topic in query_topics):
                has_relevant_memories = True
                break
        
        # Check recent memories if no relevant topic memories found
        if not has_relevant_memories and recent_memories:
            for memory in recent_memories:
                relevance = memory.get("relevance", 0)
                if relevance >= 50:
                    has_relevant_memories = True
                    break
        
        # Format the verification result
        formatted_memories = "## Memory Verification\n"
        
        if has_relevant_memories:
            formatted_memories += "Yes, we have discussed this topic before. Here are the relevant memories:\n\n"
            
            # Add topic memories
            if topic_memories:
                formatted_memories += self._format_topic_memories_for_recall(topic_memories)
            
            # Add recent memories
            if recent_memories:
                formatted_memories += self._format_recent_memories_for_recall(recent_memories)
        else:
            formatted_memories += "No, we haven't discussed this topic in detail before.\n\n"
        
        return formatted_memories
    
    def _format_memories_for_knowledge_query(self, user_facts: List[Dict[str, Any]], topic_memories: List[Dict[str, Any]], query_topics: List[str]) -> str:
        """
        Format memories for knowledge queries.
        
        Args:
            user_facts: List of user facts
            topic_memories: List of topic memories
            query_topics: List of topics extracted from the query
            
        Returns:
            Formatted memories for knowledge queries as a string
        """
        formatted_memories = "## Knowledge About User\n"
        
        # Filter user facts by query topics
        relevant_facts = []
        for fact in user_facts:
            fact_type = fact.get("type", "").lower()
            fact_value = fact.get("value", "").lower()
            
            # Check if fact is relevant to query topics
            if any(query_topic.lower() in fact_type or query_topic.lower() in fact_value for query_topic in query_topics):
                relevant_facts.append(fact)
        
        # Format relevant facts
        if relevant_facts:
            formatted_memories += "### Known Facts\n"
            for fact in relevant_facts:
                formatted_memories += f"- {fact['type'].capitalize()}: {fact['value']}\n"
            formatted_memories += "\n"
        
        # Format topic memories
        if topic_memories:
            formatted_memories += "### Related Conversations\n"
            
            # Filter topic memories by query topics
            relevant_topics = []
            for topic_memory in topic_memories:
                topic_name = topic_memory.get("topic", {}).get("name", "").lower()
                relevance = topic_memory.get("topic", {}).get("relevance", 0)
                
                # Check if topic is relevant to query
                if relevance >= 30 or any(query_topic.lower() in topic_name for query_topic in query_topics):
                    relevant_topics.append(topic_memory)
            
            # Format relevant topic memories
            for topic_memory in relevant_topics:
                topic_name = topic_memory.get("topic", {}).get("name", "")
                messages = topic_memory.get("messages", [])
                
                if messages:
                    formatted_memories += f"#### {topic_name}\n"
                    for message in messages:
                        content = message.get("content", "")
                        formatted_memories += f"- {content}\n"
                    formatted_memories += "\n"
        
        if not relevant_facts and not topic_memories:
            formatted_memories += "I don't have much information about this topic yet.\n\n"
        
        return formatted_memories
    
    def _format_default_memory_context(self, memory_context: Dict[str, Any]) -> str:
        """
        Format default memory context for general queries.
        
        Args:
            memory_context: The memory context to format
            
        Returns:
            Formatted default memory context as a string
        """
        formatted_context = ""
        
        # Format topic memories if available
        if memory_context["topic_memories"]:
            formatted_context += "## Relevant Topics\n"
            
            # Sort topic memories by relevance
            sorted_topics = sorted(
                memory_context["topic_memories"],
                key=lambda x: x.get("topic", {}).get("relevance", 0),
                reverse=True
            )
            
            # Format each topic memory
            for topic_memory in sorted_topics[:3]:  # Limit to top 3
                topic_name = topic_memory.get("topic", {}).get("name", "")
                messages = topic_memory.get("messages", [])
                
                if messages:
                    formatted_context += f"### {topic_name}\n"
                    for message in messages[:2]:  # Limit to top 2 messages per topic
                        content = message.get("content", "")
                        formatted_context += f"- {content}\n"
                    formatted_context += "\n"
        
        # Format recent memories if available
        if memory_context["recent_memories"]:
            formatted_context += "## Recent Conversation\n"
            
            # Format recent memories (limit to top 3)
            for memory in memory_context["recent_memories"][:3]:
                content = memory.get("content", "")
                formatted_context += f"- {content}\n"
            
            formatted_context += "\n"
        
        return formatted_context