"""
firebase_service.py - Service for Firebase/Firestore integration

This service provides a connection to Firebase and methods for interacting with Firestore.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timezone

# Firebase Admin SDK imports
try:
    import firebase_admin
    from firebase_admin import credentials, firestore, auth
    from google.cloud.firestore_v1 import DocumentReference, DocumentSnapshot
    from google.cloud.firestore_v1.collection import CollectionReference
except ImportError as e:
    # Provide a helpful error message if dependencies are missing
    print(f"Error importing Firebase dependencies: {str(e)}. Please run: pip install firebase-admin google-cloud-firestore")
    raise

from app.core.firebase_config import FIREBASE_CONFIG, COLLECTIONS, get_service_account_credentials
from app.core.config import logger

class FirebaseService:
    """
    Service for interacting with Firebase and Firestore.
    
    This service provides methods for:
    - Connecting to Firebase
    - Authenticating users
    - CRUD operations for Firestore documents
    - Retrieving memory context from Firestore
    """
    
    _instance = None
    
    def __new__(cls):
        """
        Implement singleton pattern to ensure only one Firebase connection.
        """
        if cls._instance is None:
            cls._instance = super(FirebaseService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """
        Initialize the Firebase service if not already initialized.
        """
        if not self._initialized:
            self._init_firebase()
            self._initialized = True
    
    def _init_firebase(self):
        """
        Initialize Firebase with admin credentials.
        """
        try:
            # Check if Firebase Admin SDK is already initialized
            if not firebase_admin._apps:
                # Use the direct path to the service account JSON file
                service_account_path = "/Users/blackcanopy/Documents/Projects/new-freya-who-this/freya-ai-chat-firebase-adminsdk-fbsvc-0af7f65b8e.json"
                
                if os.path.exists(service_account_path):
                    # Initialize Firebase Admin SDK with the JSON file directly
                    cred = credentials.Certificate(service_account_path)
                    self.app = firebase_admin.initialize_app(cred, {
                        'projectId': FIREBASE_CONFIG['projectId'],
                        'storageBucket': FIREBASE_CONFIG['storageBucket']
                    })
                    logger.info("Firebase initialized with service account credentials file")
                else:
                    # If the file doesn't exist, try getting credentials from our function
                    creds = get_service_account_credentials()
                    if creds:
                        cred = credentials.Certificate(creds)
                        self.app = firebase_admin.initialize_app(cred, {
                            'projectId': FIREBASE_CONFIG['projectId'],
                            'storageBucket': FIREBASE_CONFIG['storageBucket']
                        })
                        logger.info("Firebase initialized with service account credentials from function")
                    else:
                        # If no credentials are available, raise an error
                        logger.error("No Firebase service account credentials found")
                        raise ValueError("Firebase service account credentials are required")
                
                # Get Firestore client
                self.db = firestore.client()
                logger.info("Firestore client initialized")
            else:
                # Get existing app
                self.app = firebase_admin.get_app()
                self.db = firestore.client()
                logger.info("Using existing Firebase app")
                
        except Exception as e:
            logger.error(f"Error initializing Firebase: {str(e)}")
            logger.error("Make sure firebase-admin and google-cloud-firestore are installed")
            logger.error("Run: pip install firebase-admin google-cloud-firestore")
            raise
    
    def verify_auth_token(self, id_token: str) -> Dict[str, Any]:
        """
        Verify a Firebase authentication token.
        
        Args:
            id_token: Firebase ID token
            
        Returns:
            Dictionary with user claims
            
        Raises:
            firebase_admin.auth.InvalidIdTokenError: If the token is invalid
        """
        try:
            return auth.verify_id_token(id_token)
        except Exception as e:
            logger.error(f"Error verifying auth token: {str(e)}")
            raise
    
    def get_document(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document from Firestore.
        
        Args:
            collection: Collection name
            doc_id: Document ID
            
        Returns:
            Document data as a dictionary, or None if not found
        """
        try:
            doc_ref = self.db.collection(collection).document(doc_id)
            doc = doc_ref.get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            logger.error(f"Error getting document {collection}/{doc_id}: {str(e)}")
            return None
    
    def add_document(self, collection: str, data: Dict[str, Any]) -> Optional[str]:
        """
        Add a new document to Firestore with auto-generated ID.
        
        Args:
            collection: Collection name
            data: Document data
            
        Returns:
            New document ID if successful, None otherwise
        """
        try:
            doc_ref = self.db.collection(collection).add(data)[1]
            return doc_ref.id
        except Exception as e:
            logger.error(f"Error adding document to {collection}: {str(e)}")
            return None
    
    def set_document(self, collection: str, doc_id: str, data: Dict[str, Any], merge: bool = True) -> bool:
        """
        Set or update a document in Firestore with a specified ID.
        
        Args:
            collection: Collection name
            doc_id: Document ID
            data: Document data
            merge: Whether to merge with existing data (default: True)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            doc_ref = self.db.collection(collection).document(doc_id)
            doc_ref.set(data, merge=merge)
            return True
        except Exception as e:
            logger.error(f"Error setting document {collection}/{doc_id}: {str(e)}")
            return False
    
    def update_document(self, collection: str, doc_id: str, data: Dict[str, Any]) -> bool:
        """
        Update specific fields in a document.
        
        Args:
            collection: Collection name
            doc_id: Document ID
            data: Field updates
            
        Returns:
            True if successful, False otherwise
        """
        try:
            doc_ref = self.db.collection(collection).document(doc_id)
            doc_ref.update(data)
            return True
        except Exception as e:
            logger.error(f"Error updating document {collection}/{doc_id}: {str(e)}")
            return False
    
    def delete_document(self, collection: str, doc_id: str) -> bool:
        """
        Delete a document from Firestore.
        
        Args:
            collection: Collection name
            doc_id: Document ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            doc_ref = self.db.collection(collection).document(doc_id)
            doc_ref.delete()
            return True
        except Exception as e:
            logger.error(f"Error deleting document {collection}/{doc_id}: {str(e)}")
            return False
    
    def query_collection(self, collection: str, filters: List[Tuple[str, str, Any]], order_by: Optional[str] = None, 
                        desc: bool = False, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Query a collection with filters.
        
        Args:
            collection: Collection name
            filters: List of filter tuples (field, operator, value)
            order_by: Field to order by (optional)
            desc: Whether to order in descending order (default: False)
            limit: Maximum number of results (optional)
            
        Returns:
            List of document dictionaries
        """
        try:
            # Start with collection reference
            query = self.db.collection(collection)
            
            # Apply filters
            for field, op, value in filters:
                query = query.where(field, op, value)
            
            # Apply ordering
            if order_by:
                direction = firestore.Query.DESCENDING if desc else firestore.Query.ASCENDING
                query = query.order_by(order_by, direction=direction)
            
            # Apply limit
            if limit is not None:
                query = query.limit(limit)
            
            # Execute query
            docs = query.stream()
            return [self._doc_to_dict(doc) for doc in docs]
        except Exception as e:
            logger.error(f"Error querying collection {collection}: {str(e)}")
            return []
    
    def _doc_to_dict(self, doc: DocumentSnapshot) -> Dict[str, Any]:
        """
        Convert a Firestore DocumentSnapshot to a dictionary, adding the ID.
        
        Args:
            doc: Firestore DocumentSnapshot
            
        Returns:
            Document data with ID
        """
        data = doc.to_dict()
        if data is None:
            data = {}
        data['id'] = doc.id
        return data
    
    def subcollection_query(self, parent_collection: str, parent_id: str, sub_collection: str, 
                          filters: List[Tuple[str, str, Any]] = None, 
                          order_by: Optional[str] = None,
                          desc: bool = False,
                          limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Query a subcollection.
        
        Args:
            parent_collection: Parent collection name
            parent_id: Parent document ID
            sub_collection: Subcollection name
            filters: List of filter tuples (field, operator, value)
            order_by: Field to order by (optional)
            desc: Whether to order in descending order (default: False)
            limit: Maximum number of results (optional)
            
        Returns:
            List of document dictionaries
        """
        try:
            # Start with subcollection reference
            query = self.db.collection(parent_collection).document(parent_id).collection(sub_collection)
            
            # Apply filters
            if filters:
                for field, op, value in filters:
                    query = query.where(field, op, value)
            
            # Apply ordering
            if order_by:
                direction = firestore.Query.DESCENDING if desc else firestore.Query.ASCENDING
                query = query.order_by(order_by, direction=direction)
            
            # Apply limit
            if limit is not None:
                query = query.limit(limit)
            
            # Execute query
            docs = query.stream()
            return [self._doc_to_dict(doc) for doc in docs]
        except Exception as e:
            logger.error(f"Error querying subcollection {parent_collection}/{parent_id}/{sub_collection}: {str(e)}")
            return []
    
    def add_to_subcollection(self, parent_collection: str, parent_id: str, 
                           sub_collection: str, data: Dict[str, Any]) -> Optional[str]:
        """
        Add a document to a subcollection.
        
        Args:
            parent_collection: Parent collection name
            parent_id: Parent document ID
            sub_collection: Subcollection name
            data: Document data
            
        Returns:
            New document ID if successful, None otherwise
        """
        try:
            subcol_ref = self.db.collection(parent_collection).document(parent_id).collection(sub_collection)
            doc_ref = subcol_ref.add(data)[1]
            return doc_ref.id
        except Exception as e:
            logger.error(f"Error adding to subcollection {parent_collection}/{parent_id}/{sub_collection}: {str(e)}")
            return None
            
    # Collection-specific methods for improved readability and convenience
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User data as a dictionary, or None if not found
        """
        return self.get_document(COLLECTIONS['users'], user_id)
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a conversation by ID.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Conversation data as a dictionary, or None if not found
        """
        return self.get_document(COLLECTIONS['conversations'], conversation_id)
    
    def get_user_conversations(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get conversations for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversation dictionaries
        """
        return self.query_collection(
            COLLECTIONS['conversations'],
            filters=[('userId', '==', user_id)],
            order_by='updatedAt',
            desc=True,
            limit=limit
        )
    
    def get_conversation_messages(self, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get messages for a conversation.
        
        Based on your Firestore structure, messages are independent documents without 
        conversationId references. This method returns recent messages from the messages collection.
        
        Args:
            conversation_id: Conversation ID (not used in filtering since messages don't have conversationId)
            limit: Maximum number of messages to return
            
        Returns:
            List of message dictionaries
        """
        # Query the messages collection directly since messages don't have conversationId in your structure
        try:
            return self.query_collection(
                'messages',
                filters=[],  # No conversationId filtering available
                order_by='timestamp',
                desc=True,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error getting messages: {str(e)}")
            return []
    
    def add_message(self, conversation_id: str, message_data: Dict[str, Any]) -> Optional[str]:
        """
        Add a message to the messages collection.
        
        Based on your Firestore structure, messages are independent documents.
        
        Args:
            conversation_id: Conversation ID (for reference, but not stored in message)
            message_data: Message data (should contain 'user' field with message content)
            
        Returns:
            New message ID if successful, None otherwise
        """
        # Ensure timestamp is set
        if 'timestamp' not in message_data:
            message_data['timestamp'] = firestore.SERVER_TIMESTAMP
        
        # Add directly to messages collection (not as subcollection)
        return self.add_document('messages', message_data)
    
    def get_user_facts(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get facts for a user.
        
        Based on your Firestore structure, userFacts has fields:
        - timestamp: date
        - type: string (e.g., "interests")  
        - value: string (e.g., "it!")
        
        Args:
            user_id: User ID (e.g., "Sencere")
            
        Returns:
            List of fact dictionaries
        """
        # Since we don't see a userId field in userFacts documents in your structure,
        # we'll return all userFacts for now. You may need to add userId filtering
        # if your structure includes that field
        try:
            return self.query_collection(
                'userFacts',
                filters=[],  # No userId filter since it's not visible in your structure
                order_by='timestamp',
                desc=True
            )
        except Exception as e:
            logger.error(f"Error getting user facts: {str(e)}")
            return []
    
    def add_user_fact(self, fact_data: Dict[str, Any]) -> Optional[str]:
        """
        Add a user fact.
        
        Args:
            fact_data: Fact data
            
        Returns:
            New fact ID if successful, None otherwise
        """
        # Ensure timestamps are set
        if 'createdAt' not in fact_data:
            fact_data['createdAt'] = firestore.SERVER_TIMESTAMP
        
        return self.add_document(COLLECTIONS['user_facts'], fact_data)
    
    def get_user_topics(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get topics for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of topic dictionaries
        """
        return self.query_collection(
            COLLECTIONS['topics'],
            filters=[('userId', '==', user_id)]
        )