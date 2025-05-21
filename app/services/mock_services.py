"""
mock_services.py - Mock implementations of services for testing and development.

This module provides mock implementations of the Firebase and OpenAI services
that can be used for development and testing without actual API calls.
"""

import logging
import uuid
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta

# Get logger
logger = logging.getLogger("freya")

class MockFirebaseService:
    """
    Mock implementation of Firebase service for testing and development.
    
    This class simulates Firebase functionality without making actual API calls.
    It stores data in memory for the duration of the application.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MockFirebaseService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized') or not self._initialized:
            # Initialize in-memory storage
            self._storage = {
                "users": {},
                "conversations": {},
                "user_facts": [],
                "topics": []
            }
            self._initialized = True
            logger.info("Initialized mock Firebase service")
    
    def get_document(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a document from the mock storage."""
        if collection not in self._storage:
            return None
        
        if isinstance(self._storage[collection], dict):
            return self._storage[collection].get(doc_id)
        
        # For collections stored as lists
        for doc in self._storage[collection]:
            if doc.get("id") == doc_id:
                return doc
        
        return None
    
    def add_document(self, collection: str, data: Dict[str, Any]) -> str:
        """Add a document to the mock storage."""
        if collection not in self._storage:
            self._storage[collection] = {}
        
        # Generate ID
        doc_id = f"mock_{uuid.uuid4().hex[:8]}"
        
        # Add timestamp
        if "createdAt" not in data:
            data["createdAt"] = datetime.now()
        
        # Store document
        if isinstance(self._storage[collection], dict):
            self._storage[collection][doc_id] = data
        else:
            data["id"] = doc_id
            self._storage[collection].append(data)
        
        return doc_id
    
    def set_document(self, collection: str, doc_id: str, data: Dict[str, Any], merge: bool = True) -> bool:
        """Set a document in the mock storage."""
        if collection not in self._storage:
            self._storage[collection] = {}
        
        # Initialize if needed
        if isinstance(self._storage[collection], dict) and doc_id not in self._storage[collection]:
            self._storage[collection][doc_id] = {}
        
        # Update
        if isinstance(self._storage[collection], dict):
            if merge:
                self._storage[collection][doc_id].update(data)
            else:
                self._storage[collection][doc_id] = data
        else:
            # For collections stored as lists
            for i, doc in enumerate(self._storage[collection]):
                if doc.get("id") == doc_id:
                    if merge:
                        self._storage[collection][i].update(data)
                    else:
                        self._storage[collection][i] = data
                    break
        
        return True
    
    def update_document(self, collection: str, doc_id: str, data: Dict[str, Any]) -> bool:
        """Update a document in the mock storage."""
        return self.set_document(collection, doc_id, data, merge=True)
    
    def delete_document(self, collection: str, doc_id: str) -> bool:
        """Delete a document from the mock storage."""
        if collection not in self._storage:
            return False
        
        if isinstance(self._storage[collection], dict):
            if doc_id in self._storage[collection]:
                del self._storage[collection][doc_id]
                return True
        else:
            # For collections stored as lists
            for i, doc in enumerate(self._storage[collection]):
                if doc.get("id") == doc_id:
                    del self._storage[collection][i]
                    return True
        
        return False
    
    def query_collection(self, collection: str, filters: List[Tuple[str, str, Any]], order_by: Optional[str] = None, 
                        desc: bool = False, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Query the mock storage."""
        if collection not in self._storage:
            return []
        
        # Get all documents
        if isinstance(self._storage[collection], dict):
            docs = [{"id": k, **v} for k, v in self._storage[collection].items()]
        else:
            docs = self._storage[collection]
        
        # Apply filters
        for field, op, value in filters:
            if op == "==":
                docs = [doc for doc in docs if field in doc and doc[field] == value]
            elif op == ">=":
                docs = [doc for doc in docs if field in doc and doc[field] >= value]
            elif op == "<=":
                docs = [doc for doc in docs if field in doc and doc[field] <= value]
            elif op == "array_contains":
                docs = [doc for doc in docs if field in doc and value in doc[field]]
        
        # Apply ordering
        if order_by:
            docs = sorted(docs, key=lambda x: x.get(order_by, ""), reverse=desc)
        
        # Apply limit
        if limit:
            docs = docs[:limit]
        
        return docs
    
    def subcollection_query(self, parent_collection: str, parent_id: str, sub_collection: str, 
                          filters: List[Tuple[str, str, Any]] = None, 
                          order_by: Optional[str] = None,
                          desc: bool = False,
                          limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Query a subcollection in the mock storage."""
        # For simplicity, we'll store messages in a flat structure with conversation_id field
        if sub_collection == "messages":
            all_messages = []
            
            # Get all messages from all conversations
            for conv_id, conv in self._storage.get("conversations", {}).items():
                if "messages" in conv:
                    for msg in conv["messages"]:
                        msg_copy = msg.copy()
                        msg_copy["conversation_id"] = conv_id
                        all_messages.append(msg_copy)
            
            # Filter by parent_id
            messages = [msg for msg in all_messages if msg.get("conversation_id") == parent_id]
            
            # Apply additional filters
            if filters:
                for field, op, value in filters:
                    if op == "==":
                        messages = [msg for msg in messages if field in msg and msg[field] == value]
            
            # Apply ordering
            if order_by:
                messages = sorted(messages, key=lambda x: x.get(order_by, ""), reverse=desc)
            
            # Apply limit
            if limit:
                messages = messages[:limit]
            
            return messages
        
        return []
    
    def add_to_subcollection(self, parent_collection: str, parent_id: str, 
                           sub_collection: str, data: Dict[str, Any]) -> str:
        """Add a document to a subcollection in the mock storage."""
        # For simplicity, we'll store messages directly in the conversation
        if parent_collection == "conversations" and sub_collection == "messages":
            # Make sure parent exists
            if parent_id not in self._storage.get("conversations", {}):
                self._storage["conversations"][parent_id] = {
                    "messages": []
                }
            
            # Make sure messages array exists
            if "messages" not in self._storage["conversations"][parent_id]:
                self._storage["conversations"][parent_id]["messages"] = []
            
            # Generate ID
            msg_id = f"mock_msg_{uuid.uuid4().hex[:8]}"
            
            # Add timestamp
            if "timestamp" not in data:
                data["timestamp"] = datetime.now()
            
            # Add ID to data
            data["id"] = msg_id
            
            # Store message
            self._storage["conversations"][parent_id]["messages"].append(data)
            
            return msg_id
        
        return f"mock_{uuid.uuid4().hex[:8]}"
    
    # Collection-specific methods
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a user by ID."""
        return self.get_document("users", user_id)
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get a conversation by ID."""
        return self.get_document("conversations", conversation_id)
    
    def get_user_conversations(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversations for a user."""
        convs = []
        
        # Get all conversations
        for conv_id, conv in self._storage.get("conversations", {}).items():
            if conv.get("userId") == user_id:
                conv_copy = conv.copy()
                conv_copy["id"] = conv_id
                convs.append(conv_copy)
        
        # Sort by updatedAt
        convs = sorted(convs, key=lambda x: x.get("updatedAt", datetime.now()), reverse=True)
        
        # Apply limit
        return convs[:limit]
    
    def get_conversation_messages(self, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get messages for a conversation."""
        # Get conversation
        conv = self.get_document("conversations", conversation_id)
        if not conv:
            return []
        
        # Get messages
        messages = conv.get("messages", [])
        
        # Sort by timestamp
        messages = sorted(messages, key=lambda x: x.get("timestamp", datetime.now()), reverse=True)
        
        # Apply limit
        return messages[:limit]
    
    def add_message(self, conversation_id: str, message_data: Dict[str, Any]) -> str:
        """Add a message to a conversation."""
        return self.add_to_subcollection("conversations", conversation_id, "messages", message_data)
    
    def get_user_facts(self, user_id: str) -> List[Dict[str, Any]]:
        """Get facts for a user."""
        return self.query_collection("user_facts", [("userId", "==", user_id)])
    
    def add_user_fact(self, fact_data: Dict[str, Any]) -> str:
        """Add a user fact."""
        return self.add_document("user_facts", fact_data)
    
    def get_user_topics(self, user_id: str) -> List[Dict[str, Any]]:
        """Get topics for a user."""
        return self.query_collection("topics", [("userId", "==", user_id)])

class MockMemoryService:
    """
    Mock implementation of the Firebase memory service.
    
    This class simulates the memory service without making actual API calls.
    """
    
    def __init__(self):
        self.firebase = MockFirebaseService()
    
    def is_memory_query(self, query: str) -> bool:
        """Simulate memory query detection."""
        memory_keywords = [
            "remember", "recall", "forget", "memory", "mentioned",
            "told", "said", "talked about", "discussed", "conversation"
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in memory_keywords)
    
    def extract_topics_from_query(self, query: str, top_n: int = 3) -> List[str]:
        """Simulate topic extraction."""
        query_lower = query.lower()
        
        # Simple keyword matching for demo
        topics = []
        if "work" in query_lower or "job" in query_lower:
            topics.append("work")
        if "family" in query_lower or "parent" in query_lower:
            topics.append("family")
        if "health" in query_lower or "sick" in query_lower:
            topics.append("health")
        if "hobby" in query_lower or "interest" in query_lower:
            topics.append("hobbies")
        
        # Default topic if none found
        if not topics:
            topics.append("general")
        
        return topics[:top_n]
    
    def assemble_memory_context(self, user_id: str, query: str) -> Dict[str, Any]:
        """Simulate assembling memory context."""
        # Check if this is a memory query
        is_memory_query = self.is_memory_query(query)
        
        # Extract topics
        topics = self.extract_topics_from_query(query)
        
        # Build mock memory context
        memory_context = {
            "user_facts": [
                {
                    "type": "location",
                    "value": "New York",
                    "confidence": 90
                },
                {
                    "type": "job",
                    "value": "software engineer",
                    "confidence": 85
                }
            ],
            "recent_memories": [
                {
                    "content": "User: I'm working on a new project using React and TypeScript.",
                    "user_id": user_id,
                    "timestamp": datetime.now() - timedelta(days=1)
                },
                {
                    "content": "Freya: That sounds exciting! What kind of project is it?",
                    "user_id": "assistant",
                    "timestamp": datetime.now() - timedelta(days=1)
                }
            ],
            "topic_memories": [
                {
                    "topic": {
                        "name": "work",
                        "relevance": 85
                    },
                    "messages": [
                        {
                            "content": "User: I'm working as a software engineer at a tech company.",
                            "user_id": user_id,
                            "timestamp": datetime.now() - timedelta(days=5)
                        }
                    ]
                }
            ],
            "is_memory_query": is_memory_query,
            "memory_query_topics": topics if is_memory_query else []
        }
        
        # Format context
        memory_context["formatted_context"] = self.format_memory_context(memory_context, query)
        
        return memory_context
    
    def format_memory_context(self, memory_context: Dict[str, Any], query: str = "") -> str:
        """Format memory context for OpenAI."""
        formatted_context = "### Memory Context ###\n\n"
        
        # Add user facts
        formatted_context += "## User Facts\n"
        for fact in memory_context["user_facts"]:
            confidence = fact.get("confidence", 0)
            confidence_indicator = "★" * (1 + min(4, int(confidence / 20)))
            formatted_context += f"- {fact['type'].capitalize()}: {fact['value']} {confidence_indicator}\n"
        
        formatted_context += "\n## Recent Conversation\n"
        for memory in memory_context["recent_memories"][:3]:
            content = memory.get("content", "")
            formatted_context += f"- {content}\n"
        
        return formatted_context

class MockOpenAIService:
    """
    Mock implementation of the OpenAI service.
    
    This class simulates the OpenAI service without making actual API calls.
    """
    
    def __init__(self):
        self.memory_service = MockMemoryService()
    
    async def create_freya_chat_completion(self, user_message: str, conversation_history=None, memory_context=None, 
                                          system_prompt=None, stream=False):
        """Simulate creating a chat completion."""
        # Generate a mock response based on the user's message
        response_content = self._generate_mock_response(user_message)
        
        # Wrap in a mock completion object
        mock_completion = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": response_content
                    }
                }
            ]
        }
        
        return mock_completion
    
    def get_message_content(self, completion):
        """Extract message content from a completion."""
        if not completion or "choices" not in completion:
            return "I'm sorry, I couldn't generate a response."
        
        return completion["choices"][0]["message"]["content"]
    
    def _generate_mock_response(self, message: str) -> str:
        """Generate a mock response based on the message."""
        message_lower = message.lower()
        
        # Check for greetings
        if any(greeting in message_lower for greeting in ["hello", "hi", "hey"]):
            return "Hi there! How are you feeling today?"
        
        # Check for questions about name
        if "name" in message_lower and any(q in message_lower for q in ["what", "your"]):
            return "I'm Freya, your personal AI companion. It's nice to chat with you!"
        
        # Check for questions about capabilities
        if any(cap in message_lower for cap in ["can you", "what can", "help me"]):
            return "I can chat with you, remember details about our conversations, and offer support. What would you like to talk about?"
        
        # Default responses
        import random
        default_responses = [
            "That's interesting! Tell me more about that.",
            "I'm here to listen and chat whenever you need me.",
            "I appreciate you sharing that with me. How does that make you feel?",
            "Thanks for telling me about that. What else is on your mind?",
            "I'm always here for you. What would you like to discuss next?"
        ]
        
        return random.choice(default_responses)