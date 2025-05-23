"""
firebase_memory_service_optimized.py - Optimized memory service with performance improvements

This service provides optimized memory retrieval and assembly:
- Parallel query execution
- Smarter relevance scoring
- Reduced memory allocation
- Cached topic extraction
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta, timezone
import logging
import concurrent.futures
from functools import lru_cache

from app.services.firebase_service_optimized import OptimizedFirebaseService
from app.services.topic_extraction import TopicExtractor
from app.core.config import logger
from app.core.firebase_config import COLLECTIONS

class OptimizedFirebaseMemoryService:
    """
    Optimized service for retrieving memory context from Firestore.
    
    Key optimizations:
    - Parallel query execution
    - Cached topic extraction
    - Pre-computed relevance scores
    - Reduced memory allocations
    """
    
    # Pre-compiled regex patterns (class level for efficiency)
    MEMORY_PATTERNS = [
        re.compile(pattern, re.IGNORECASE) for pattern in [
            r'do you remember (when|what|how|where|why|who|if|that|about|our|my|the)',
            r'what did (i|we|you) (say|tell|ask|talk|mention) (about|regarding|concerning)',
            r'(what|when) did (i|we) (discuss|talk about|mention|say)',
            r'have (i|we) (talked|spoken|discussed|mentioned) (about|regarding)',
            r'(tell|remind) me (about|what|when|how|where|why) (i|we|you) (said|mentioned|talked about)',
            r'(recall|remember|recollect) (our|the|that|when|what|how|where|why|who)',
            r'what (did|do) you know about my',
            r'(last time|previously|earlier|before) (we|you|i) (talked|spoke|discussed|mentioned|said)',
            r'(in|during) (our|a) (previous|past|last|earlier|recent) (conversation|discussion|chat)',
        ]
    ]
    
    def __init__(self):
        """Initialize the optimized memory service."""
        self.firebase = OptimizedFirebaseService()
        self.topic_extractor = TopicExtractor()
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
    
    @lru_cache(maxsize=128)
    def is_memory_query(self, query: str) -> bool:
        """
        Cached detection of memory-related queries.
        
        Uses LRU cache to avoid re-processing common queries.
        """
        # Quick keyword check first
        query_lower = query.lower()
        memory_keywords = {"remember", "recall", "forget", "memory", "mentioned",
                          "told", "said", "talked about", "discussed", "conversation"}
        
        if any(keyword in query_lower for keyword in memory_keywords):
            return True
        
        # Pattern matching
        return any(pattern.search(query) for pattern in self.MEMORY_PATTERNS)
    
    @lru_cache(maxsize=64)
    def extract_topics_from_query(self, query: str, top_n: int = 3) -> List[str]:
        """
        Cached topic extraction from queries.
        
        LRU cache prevents re-extraction of common queries.
        """
        # Use the topic extractor
        extracted_topics = self.topic_extractor.extract_topics(query, top_n=top_n)
        
        if extracted_topics:
            return extracted_topics
        
        # Fallback to keyword matching if no topics extracted
        query_lower = query.lower()
        matched_topics = []
        
        # Use a more efficient keyword matching approach
        topic_keywords = {
            "family": {"family", "parent", "father", "mother", "dad", "mom", "brother", "sister"},
            "work": {"job", "work", "career", "company", "boss", "office", "colleague", "project"},
            "health": {"health", "sick", "illness", "doctor", "hospital", "pain", "exercise"},
            "hobbies": {"hobby", "game", "sport", "book", "movie", "music", "art", "travel"},
            "education": {"school", "college", "university", "degree", "class", "study", "student"},
            "location": {"home", "house", "apartment", "city", "town", "live", "living"}
        }
        
        # Split query into words for efficient matching
        query_words = set(query_lower.split())
        
        for topic, keywords in topic_keywords.items():
            if query_words & keywords:  # Set intersection
                matched_topics.append(topic)
                if len(matched_topics) >= top_n:
                    break
        
        return matched_topics[:top_n]
    
    def assemble_memory_context_optimized(self, user_id: str, query: str) -> Dict[str, Any]:
        """
        Assemble memory context with parallel execution and optimizations.
        
        Key improvements:
        - Parallel query execution
        - Early termination for non-memory queries
        - Optimized data structures
        """
        # Check if this is a memory query
        is_memory_query = self.is_memory_query(query)
        
        # Extract topics early for parallel processing
        query_topics = self.extract_topics_from_query(query, top_n=5)
        
        # Define parallel tasks
        def get_facts():
            if is_memory_query or query_topics:
                return self._get_relevant_user_facts(user_id, query, limit=5)
            return self.firebase.get_user_facts(user_id)[:3]  # Fewer facts for non-memory queries
        
        def get_recent():
            if is_memory_query:
                return self._get_recent_messages_optimized(user_id, limit=20, max_age_days=30)
            return self._get_recent_messages_optimized(user_id, limit=10, max_age_days=7)
        
        def get_topics():
            if query_topics:
                return self._get_topic_memories_optimized(user_id, query_topics, 
                                                         topic_limit=3, message_limit=3)
            return []
        
        # Execute queries in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_facts = executor.submit(get_facts)
            future_recent = executor.submit(get_recent)
            future_topics = executor.submit(get_topics)
            
            # Wait for results
            user_facts = future_facts.result()
            recent_memories = future_recent.result()
            topic_memories = future_topics.result()
        
        # Build memory context
        memory_context = {
            "user_facts": user_facts,
            "recent_memories": recent_memories,
            "topic_memories": topic_memories,
            "is_memory_query": is_memory_query,
            "query_topics": query_topics
        }
        
        # Add memory query classification if needed
        if is_memory_query:
            memory_context["memory_query_type"] = self._classify_memory_query_type(query)
        
        # Format the context
        formatted_context = self._format_memory_context_optimized(memory_context, query)
        memory_context["formatted_context"] = formatted_context
        
        return memory_context
    
    def _get_relevant_user_facts(self, user_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get user facts with optimized relevance scoring."""
        # Get all facts from optimized service (cached)
        all_facts = self.firebase.get_user_facts(user_id)
        
        if not query or not all_facts:
            return all_facts[:limit]
        
        # Score facts efficiently
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        scored_facts = []
        for fact in all_facts:
            fact_type = fact.get('type', '').lower()
            fact_value = fact.get('value', '').lower()
            fact_words = set(fact_value.split())
            
            # Calculate score based on word overlap
            score = 0.0
            
            # Direct substring match
            if query_lower in fact_value or fact_value in query_lower:
                score += 3.0
            
            # Word overlap
            overlap = len(query_words & fact_words)
            if overlap > 0:
                score += overlap * 1.0
            
            # Type relevance
            type_weights = {
                'job': 1.5, 'location': 1.3, 'family': 1.4,
                'interests': 1.2, 'preferences': 1.1
            }
            score *= type_weights.get(fact_type, 1.0)
            
            if score > 0:
                scored_facts.append((fact, score))
        
        # Sort and return top facts
        scored_facts.sort(key=lambda x: x[1], reverse=True)
        return [fact for fact, _ in scored_facts[:limit]]
    
    def _get_recent_messages_optimized(self, user_id: str, limit: int = 20, 
                                     max_age_days: int = 30) -> List[Dict[str, Any]]:
        """Get recent messages using optimized Firebase service."""
        messages = self.firebase.get_recent_messages_optimized(user_id, max_age_days, limit)
        
        # Format messages for memory context
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "content": msg.get("user", ""),  # Using 'user' field per structure
                "user_id": user_id,
                "timestamp": msg.get("timestamp", ""),
                "conversation_id": msg.get("conversation_id", "")
            })
        
        return formatted_messages
    
    def _get_topic_memories_optimized(self, user_id: str, query_topics: List[str], 
                                    topic_limit: int = 3, message_limit: int = 3) -> List[Dict[str, Any]]:
        """Get topic memories with optimized querying."""
        # Get all user topics
        all_topics = self.firebase.get_user_topics(user_id)
        
        if not all_topics:
            return []
        
        # Score topics based on query relevance
        scored_topics = []
        query_topics_lower = [t.lower() for t in query_topics]
        
        for topic in all_topics:
            topic_name = topic.get('name', '').lower()
            score = 0.5  # Base score
            
            # Direct match
            if topic_name in query_topics_lower:
                score += 3.0
            # Partial match
            elif any(qt in topic_name or topic_name in qt for qt in query_topics_lower):
                score += 1.5
            
            # Recency bonus
            if 'lastUsed' in topic:
                last_used = topic['lastUsed']
                if isinstance(last_used, datetime):
                    days_ago = (datetime.now(timezone.utc) - last_used).days
                    score += max(0, 0.5 - (days_ago * 0.05))
            
            if score > 0.5:
                topic['relevance_score'] = score
                scored_topics.append((topic, score))
        
        # Sort and get top topics
        scored_topics.sort(key=lambda x: x[1], reverse=True)
        top_topics = [topic for topic, _ in scored_topics[:topic_limit]]
        
        # Get messages for topics in parallel
        topic_memories = []
        topic_ids = [t.get('id') for t in top_topics if t.get('id')]
        
        if topic_ids:
            # Use optimized topic query
            messages = self.firebase.query_messages_by_topics(topic_ids, user_id, 
                                                            limit=message_limit * len(topic_ids))
            
            # Group messages by topic
            for topic in top_topics:
                topic_id = topic.get('id')
                topic_messages = [m for m in messages if topic_id in m.get('topicIds', [])][:message_limit]
                
                if topic_messages:
                    topic_memories.append({
                        'topic': {
                            'id': topic_id,
                            'name': topic.get('name', ''),
                            'relevance': min(100, int(topic.get('relevance_score', 0) * 100))
                        },
                        'messages': topic_messages
                    })
        
        return topic_memories
    
    def _classify_memory_query_type(self, query: str) -> str:
        """Classify memory query type with cached pattern matching."""
        query_lower = query.lower()
        
        # Use early returns for efficiency
        if "do you remember" in query_lower:
            return "recall_verification"
        elif re.search(r'what did (i|we|you) (say|tell|ask|talk|mention)', query_lower):
            return "content_recall"
        elif re.search(r'when did (i|we) (discuss|talk about|mention|say)', query_lower):
            return "temporal_recall"
        elif re.search(r'have (i|we) (talked|spoken|discussed|mentioned)', query_lower):
            return "existence_verification"
        elif "what do you know about my" in query_lower:
            return "knowledge_query"
        elif any(term in query_lower for term in ["last time", "previously", "earlier", "before"]):
            return "previous_conversation"
        else:
            return "general_memory_query"
    
    def _format_memory_context_optimized(self, memory_context: Dict[str, Any], query: str) -> str:
        """Format memory context with optimized string building."""
        # Use list for efficient string building
        context_parts = ["### Memory Context ###\n"]
        
        # Format user facts if available
        if memory_context["user_facts"]:
            context_parts.append("\n## User Facts\n")
            for fact in memory_context["user_facts"][:5]:  # Limit facts
                confidence = fact.get("confidence", 70)
                stars = "★" * (1 + min(4, confidence // 20))
                context_parts.append(f"- {fact['type'].capitalize()}: {fact['value']} {stars}\n")
        
        # Format based on query type
        is_memory_query = memory_context.get("is_memory_query", False)
        
        if is_memory_query:
            query_type = memory_context.get("memory_query_type", "general")
            
            # Add relevant memories based on query type
            if query_type in ["recall_verification", "content_recall"]:
                # Topic memories
                if memory_context["topic_memories"]:
                    context_parts.append("\n## Topic-Related Memories\n")
                    for tm in memory_context["topic_memories"][:3]:
                        topic_name = tm['topic']['name']
                        context_parts.append(f"### {topic_name}\n")
                        for msg in tm['messages'][:2]:
                            context_parts.append(f"- {msg.get('content', '')}\n")
                
                # Recent memories
                if memory_context["recent_memories"]:
                    context_parts.append("\n## Recent Conversation History\n")
                    for mem in memory_context["recent_memories"][:5]:
                        context_parts.append(f"- {mem.get('content', '')}\n")
            
            elif query_type == "knowledge_query":
                # Focus on facts
                context_parts.append("\n## Known Information\n")
                query_topics = memory_context.get("query_topics", [])
                
                # Filter facts by relevance
                for fact in memory_context["user_facts"]:
                    fact_type = fact.get("type", "").lower()
                    fact_value = fact.get("value", "").lower()
                    if any(topic.lower() in fact_type or topic.lower() in fact_value 
                          for topic in query_topics):
                        context_parts.append(f"- {fact['type']}: {fact['value']}\n")
        else:
            # Non-memory query - minimal context
            if memory_context["recent_memories"]:
                context_parts.append("\n## Recent Context\n")
                for mem in memory_context["recent_memories"][:3]:
                    context_parts.append(f"- {mem.get('content', '')}\n")
        
        # Join all parts efficiently
        return ''.join(context_parts)
    
    def __del__(self):
        """Cleanup thread pool on deletion."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)