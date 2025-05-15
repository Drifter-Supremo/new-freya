from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from app.models.topic import Topic, MessageTopic
from app.models.message import Message
from app.repository.topic import TopicRepository
from app.services.topic_extraction import TopicExtractor

class TopicTaggingService:
    """
    Service for tagging messages with relevant topics.
    
    This service handles the process of extracting topics from message content,
    creating new topics in the database as needed, and associating messages
    with their relevant topics.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the TopicTaggingService with a database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.topic_repo = TopicRepository(db)
        self.topic_extractor = TopicExtractor()
    
    def tag_message(self, message: Message, top_n: int = 3) -> List[Topic]:
        """
        Tag a message with relevant topics.
        
        Args:
            message: The message to tag
            top_n: Maximum number of topics to extract (default: 3)
            
        Returns:
            List of Topic objects that were associated with the message
        """
        # Extract topics from message content
        topic_names = self.topic_extractor.extract_topics(message.content, top_n=top_n)
        
        # Get or create topics
        topics = []
        for topic_name in topic_names:
            topic = self._get_or_create_topic(topic_name)
            if topic:
                topics.append(topic)
        
        # Create message-topic associations
        self._create_message_topic_associations(message, topics)
        
        return topics
    
    def tag_messages(self, messages: List[Message], top_n: int = 3) -> Dict[int, List[Topic]]:
        """
        Tag multiple messages with relevant topics in a batch.
        
        Args:
            messages: List of messages to tag
            top_n: Maximum number of topics to extract per message (default: 3)
            
        Returns:
            Dictionary mapping message IDs to their associated Topic objects
        """
        results = {}
        for message in messages:
            topics = self.tag_message(message, top_n)
            results[message.id] = topics
        return results
    
    def _get_or_create_topic(self, topic_name: str) -> Optional[Topic]:
        """
        Get an existing topic by name or create it if it doesn't exist.
        
        Args:
            topic_name: Name of the topic to get or create
            
        Returns:
            Topic object or None if creation failed
        """
        # Try to find existing topic (case-insensitive search)
        topic = self.db.query(Topic).filter(
            Topic.name.ilike(topic_name)
        ).first()
        
        # Create new topic if it doesn't exist
        if not topic:
            try:
                topic = self.topic_repo.create({"name": topic_name.lower()})
                self.db.flush()
            except Exception as e:
                # Log error and return None if topic creation fails
                print(f"Failed to create topic '{topic_name}': {e}")
                return None
                
        return topic
    
    def _create_message_topic_associations(self, message: Message, topics: List[Topic]) -> None:
        """
        Create associations between a message and its topics.
        
        Args:
            message: The message to associate with topics
            topics: List of Topic objects to associate with the message
        """
        # Skip if no topics to associate
        if not topics:
            return
            
        # Check for existing associations to avoid duplicates
        existing_topic_ids = {
            mt.topic_id for mt in message.message_topics
        }
        
        # Create new associations
        for topic in topics:
            if topic.id not in existing_topic_ids:
                message_topic = MessageTopic(
                    message_id=message.id,
                    topic_id=topic.id
                )
                self.db.add(message_topic)
        
        # Flush changes to the database
        self.db.flush()
    
    def get_message_topics(self, message_id: int) -> List[Topic]:
        """
        Get all topics associated with a message.

        Args:
            message_id: ID of the message

        Returns:
            List of Topic objects associated with the message
        """
        # Use filter instead of the deprecated get method
        message = self.db.query(Message).filter(Message.id == message_id).first()
        if not message:
            return []

        # Get topics directly from the database to avoid any ORM issues
        topic_ids = self.db.query(MessageTopic.topic_id).filter(MessageTopic.message_id == message_id).all()
        topic_ids = [t[0] for t in topic_ids]  # Extract IDs from result tuples
        
        if not topic_ids:
            return []
            
        topics = self.db.query(Topic).filter(Topic.id.in_(topic_ids)).all()
        return topics
    
    def get_topic_messages(self, topic_id: int) -> List[Message]:
        """
        Get all messages associated with a topic.
        
        Args:
            topic_id: ID of the topic
            
        Returns:
            List of Message objects associated with the topic
        """
        topic = self.db.query(Topic).get(topic_id)
        if not topic:
            return []
            
        return [mt.message for mt in topic.message_topics]
