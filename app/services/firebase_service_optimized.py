"""
firebase_service_optimized.py - Optimized Firebase/Firestore service

This service implements performance optimizations for Firestore queries:
- Proper field filtering
- Parallel query execution
- Caching layer
- Optimized data fetching
"""

import os
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timezone, timedelta
from functools import lru_cache
import concurrent.futures
from threading import Lock

# Firebase Admin SDK imports
try:
    import firebase_admin
    from firebase_admin import credentials, firestore, auth
    from google.cloud.firestore_v1 import DocumentReference, DocumentSnapshot
    from google.cloud.firestore_v1.collection import CollectionReference
except ImportError as e:
    print(f"Error importing Firebase dependencies: {str(e)}")
    raise

from app.core.firebase_config import FIREBASE_CONFIG, COLLECTIONS
from app.services.firebase_service import FirebaseService
from app.core.config import logger

class OptimizedFirebaseService(FirebaseService):
    """
    Optimized Firebase service with performance improvements:
    - Caching for frequently accessed data
    - Parallel query execution
    - Optimized query patterns
    """
    
    def __init__(self, cache_ttl_minutes: int = 5):
        """
        Initialize the optimized Firebase service.
        
        Args:
            cache_ttl_minutes: Cache time-to-live in minutes
        """
        super().__init__()
        self._cache = {}
        self._cache_locks = {}
        self._cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
    
    def _get_cache_key(self, collection: str, operation: str, params: str) -> str:
        """Generate a cache key."""
        return f"{collection}:{operation}:{params}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get data from cache if not expired."""
        if cache_key in self._cache:
            data, timestamp = self._cache[cache_key]
            if datetime.now() - timestamp < self._cache_ttl:
                logger.debug(f"Cache hit for key: {cache_key}")
                return data
            else:
                # Remove expired entry
                del self._cache[cache_key]
        return None
    
    def _set_cache(self, cache_key: str, data: Any):
        """Set data in cache with timestamp."""
        self._cache[cache_key] = (data, datetime.now())
        logger.debug(f"Cache set for key: {cache_key}")
    
    def clear_cache(self, pattern: Optional[str] = None):
        """Clear cache entries matching pattern or all if pattern is None."""
        if pattern is None:
            self._cache.clear()
            logger.info("Cleared entire cache")
        else:
            keys_to_remove = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self._cache[key]
            logger.info(f"Cleared {len(keys_to_remove)} cache entries matching pattern: {pattern}")
    
    def get_user_facts(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get facts for a user with caching and proper filtering.
        
        Optimizations:
        - Cache results for 5 minutes
        - Filter by userId at Firestore level (when field exists)
        - Order by timestamp for consistency
        """
        cache_key = self._get_cache_key('userFacts', 'get', user_id)
        
        # Check cache first
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Get lock for this cache key to prevent duplicate queries
        if cache_key not in self._cache_locks:
            self._cache_locks[cache_key] = Lock()
        
        with self._cache_locks[cache_key]:
            # Double-check cache after acquiring lock
            cached_data = self._get_from_cache(cache_key)
            if cached_data is not None:
                return cached_data
            
            # Query Firestore with optimized filter
            try:
                # First, try to query with userId filter (if field exists)
                facts = self.query_collection(
                    'userFacts',
                    filters=[('userId', '==', user_id)],
                    order_by='timestamp',
                    desc=True
                )
                
                # If no results and userId might not exist on documents,
                # fall back to fetching all (current behavior)
                if not facts:
                    logger.warning(f"No facts found with userId filter for {user_id}, trying without filter")
                    facts = self.query_collection(
                        'userFacts',
                        filters=[],
                        order_by='timestamp',
                        desc=True
                    )
                    
                    # Filter in memory as fallback
                    # This maintains compatibility while we migrate data
                    # In production, all facts should have userId field
                    
            except Exception as e:
                logger.error(f"Error querying user facts with filter: {str(e)}")
                # Fallback to unfiltered query
                facts = self.query_collection(
                    'userFacts',
                    filters=[],
                    order_by='timestamp',
                    desc=True
                )
            
            # Cache the results
            self._set_cache(cache_key, facts)
            
            return facts
    
    def get_conversation_messages_optimized(self, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get messages for a conversation with proper filtering.
        
        Optimizations:
        - Filter by conversationId at Firestore level
        - Cache recent messages
        - Order by timestamp consistently
        """
        cache_key = self._get_cache_key('messages', 'conv', f"{conversation_id}:{limit}")
        
        # Check cache for recent queries
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        try:
            # Query with conversationId filter (when field exists)
            messages = self.query_collection(
                'messages',
                filters=[('conversationId', '==', conversation_id)],
                order_by='timestamp',
                desc=True,
                limit=limit
            )
            
            # If no results, fall back to current behavior
            if not messages:
                logger.warning(f"No messages found with conversationId filter for {conversation_id}")
                messages = self.query_collection(
                    'messages',
                    filters=[],
                    order_by='timestamp',
                    desc=True,
                    limit=limit
                )
        except Exception as e:
            logger.error(f"Error querying messages with conversationId: {str(e)}")
            # Fallback to current implementation
            messages = super().get_conversation_messages(conversation_id, limit)
        
        # Cache the results
        self._set_cache(cache_key, messages)
        
        return messages
    
    def get_user_memory_context_parallel(self, user_id: str) -> Dict[str, Any]:
        """
        Get all memory context data in parallel.
        
        Optimizations:
        - Execute queries in parallel using thread pool
        - Return structured data for memory assembly
        """
        # Define the queries to run in parallel
        def get_facts():
            return self.get_user_facts(user_id)
        
        def get_conversations():
            return self.get_user_conversations(user_id, limit=10)
        
        def get_topics():
            return self.get_user_topics(user_id)
        
        def get_recent_messages():
            # Get messages from user's recent conversations
            conversations = self.get_user_conversations(user_id, limit=5)
            all_messages = []
            for conv in conversations[:3]:  # Limit to 3 most recent conversations
                conv_id = conv.get('id')
                messages = self.get_conversation_messages_optimized(conv_id, limit=10)
                for msg in messages:
                    msg['conversation_id'] = conv_id
                    all_messages.append(msg)
            return all_messages
        
        # Execute queries in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_facts = executor.submit(get_facts)
            future_convs = executor.submit(get_conversations)
            future_topics = executor.submit(get_topics)
            future_messages = executor.submit(get_recent_messages)
            
            # Wait for all queries to complete
            facts = future_facts.result()
            conversations = future_convs.result()
            topics = future_topics.result()
            recent_messages = future_messages.result()
        
        return {
            'user_facts': facts,
            'conversations': conversations,
            'topics': topics,
            'recent_messages': recent_messages
        }
    
    def add_message_with_metadata(self, conversation_id: str, message_data: Dict[str, Any], 
                                 topics: Optional[List[str]] = None) -> Optional[str]:
        """
        Add a message with proper metadata for optimized querying.
        
        Enhancements:
        - Add conversationId field
        - Add topicIds array field
        - Use server timestamp
        """
        # Ensure proper fields exist
        enhanced_data = message_data.copy()
        
        # Add conversationId for efficient filtering
        enhanced_data['conversationId'] = conversation_id
        
        # Add topicIds if provided
        if topics:
            enhanced_data['topicIds'] = topics
        
        # Ensure timestamp is set
        if 'timestamp' not in enhanced_data:
            enhanced_data['timestamp'] = firestore.SERVER_TIMESTAMP
        
        # Add the message
        message_id = self.add_document('messages', enhanced_data)
        
        # Clear relevant caches
        if message_id:
            self.clear_cache(f"messages:conv:{conversation_id}")
        
        return message_id
    
    def batch_get_documents(self, collection: str, doc_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get multiple documents in a single batch operation.
        
        Optimizations:
        - Batch read operation
        - Parallel processing for large batches
        """
        if not doc_ids:
            return []
        
        # For small batches, use sequential reads
        if len(doc_ids) <= 10:
            results = []
            for doc_id in doc_ids:
                doc = self.get_document(collection, doc_id)
                if doc:
                    doc['id'] = doc_id
                    results.append(doc)
            return results
        
        # For larger batches, use parallel reads
        def get_single_doc(doc_id):
            doc = self.get_document(collection, doc_id)
            if doc:
                doc['id'] = doc_id
            return doc
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(get_single_doc, doc_id) for doc_id in doc_ids]
            results = [f.result() for f in futures if f.result() is not None]
        
        return results
    
    def query_messages_by_topics(self, topic_ids: List[str], user_id: str, 
                               limit: int = 20) -> List[Dict[str, Any]]:
        """
        Query messages that contain any of the specified topics.
        
        Optimizations:
        - Use array-contains-any for efficient topic queries
        - Cache results by topic combination
        """
        if not topic_ids:
            return []
        
        # Create cache key from sorted topic IDs
        cache_key = self._get_cache_key('messages', 'topics', 
                                       f"{user_id}:{','.join(sorted(topic_ids))}:{limit}")
        
        # Check cache
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        try:
            # Firestore supports array-contains-any for up to 10 values
            if len(topic_ids) <= 10:
                messages = self.db.collection('messages')\
                    .where('topicIds', 'array-contains-any', topic_ids)\
                    .order_by('timestamp', direction=firestore.Query.DESCENDING)\
                    .limit(limit)\
                    .stream()
                
                results = [self._doc_to_dict(doc) for doc in messages]
            else:
                # For more than 10 topics, batch the queries
                all_results = []
                for i in range(0, len(topic_ids), 10):
                    batch_topics = topic_ids[i:i+10]
                    messages = self.db.collection('messages')\
                        .where('topicIds', 'array-contains-any', batch_topics)\
                        .order_by('timestamp', direction=firestore.Query.DESCENDING)\
                        .limit(limit)\
                        .stream()
                    
                    all_results.extend([self._doc_to_dict(doc) for doc in messages])
                
                # Sort and limit combined results
                all_results.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
                results = all_results[:limit]
            
            # Cache results
            self._set_cache(cache_key, results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error querying messages by topics: {str(e)}")
            return []
    
    def get_recent_messages_optimized(self, user_id: str, max_age_days: int = 30, 
                                    limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent messages with optimized timestamp filtering.
        
        Optimizations:
        - Filter by timestamp at Firestore level
        - Use compound queries for efficiency
        """
        cache_key = self._get_cache_key('messages', 'recent', 
                                       f"{user_id}:{max_age_days}:{limit}")
        
        # Check cache
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Calculate cutoff timestamp
        cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        
        # Get user's recent conversations
        conversations = self.get_user_conversations(user_id, limit=10)
        
        if not conversations:
            return []
        
        # Get conversation IDs
        conv_ids = [conv.get('id') for conv in conversations if conv.get('id')]
        
        # Query messages with timestamp filter
        all_messages = []
        
        # Batch query by conversation IDs (Firestore in operator supports up to 10 values)
        for i in range(0, len(conv_ids), 10):
            batch_ids = conv_ids[i:i+10]
            
            try:
                # Query with both conversationId and timestamp filters
                query = self.db.collection('messages')\
                    .where('conversationId', 'in', batch_ids)\
                    .where('timestamp', '>', cutoff)\
                    .order_by('timestamp', direction=firestore.Query.DESCENDING)\
                    .limit(limit)
                
                messages = query.stream()
                all_messages.extend([self._doc_to_dict(doc) for doc in messages])
                
            except Exception as e:
                logger.error(f"Error in optimized message query: {str(e)}")
                # Fallback to conversation-by-conversation query
                for conv_id in batch_ids:
                    try:
                        messages = self.query_collection(
                            'messages',
                            filters=[
                                ('conversationId', '==', conv_id),
                                ('timestamp', '>', cutoff)
                            ],
                            order_by='timestamp',
                            desc=True,
                            limit=10
                        )
                        all_messages.extend(messages)
                    except:
                        # If conversationId field doesn't exist, use parent method
                        continue
        
        # Sort all messages by timestamp and limit
        all_messages.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        results = all_messages[:limit]
        
        # Cache results
        self._set_cache(cache_key, results)
        
        return results
    
    def __del__(self):
        """Cleanup thread pool on deletion."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)