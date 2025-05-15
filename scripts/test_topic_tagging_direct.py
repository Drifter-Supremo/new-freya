"""
Simple direct test script for the topic tagging service.
This script tests the core functionality without complex test fixtures.
"""
import os
import sys
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import models and services
from app.models import Base
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.topic import Topic, MessageTopic
from app.services.topic_tagging import TopicTaggingService

def main():
    # Get database URL from environment variable
    DB_URL = os.getenv("POSTGRES_URL").replace('postgresql+psycopg2://', 'postgresql://')
    print(f"Connecting to database: {DB_URL}")
    
    # Create engine and session
    engine = create_engine(DB_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("Starting topic tagging test...")
        
        # Clean up any existing test data
        print("Cleaning up existing test data...")
        db.query(MessageTopic).filter(
            MessageTopic.message_id.in_(
                db.query(Message.id).filter(Message.content.like("%TEST_TOPIC_TAGGING%"))
            )
        ).delete(synchronize_session=False)
        
        db.query(Message).filter(Message.content.like("%TEST_TOPIC_TAGGING%")).delete()
        db.query(Topic).filter(Topic.name.like("test_%")).delete()
        db.commit()
        
        # Create a test user if it doesn't exist
        print("Setting up test user...")
        test_user = db.query(User).filter(User.username == "test_user").first()
        if not test_user:
            # Try with a different username if the first one exists
            import uuid
            unique_id = str(uuid.uuid4())[:8]
            test_user = User(
                username=f"test_user_{unique_id}",
                email=f"test_{unique_id}@example.com",
                hashed_password="test_password"
            )
            db.add(test_user)
            db.commit()
            print(f"Created test user with ID: {test_user.id}")
        else:
            print(f"Using existing test user with ID: {test_user.id}")
        
        # Create a test conversation
        print("Creating test conversation...")
        conversation = Conversation(user_id=test_user.id)
        db.add(conversation)
        db.commit()
        print(f"Created conversation with ID: {conversation.id}")
        
        # Create a test message with a timestamp to make it unique
        import time
        timestamp = int(time.time())
        print("Creating test message...")
        message = Message(
            content=f"TEST_TOPIC_TAGGING_{timestamp} I love programming in Python and JavaScript!",
            conversation_id=conversation.id,
            user_id=test_user.id
        )
        db.add(message)
        db.commit()
        print(f"Created message with ID: {message.id}")
        
        # Create the topic tagging service
        topic_service = TopicTaggingService(db)
        
        # Test tagging the message
        print("Tagging message with topics...")
        topics = topic_service.tag_message(message, top_n=3)
        
        print(f"Message tagged with {len(topics)} topics:")
        for topic in topics:
            print(f"  - {topic.name} (ID: {topic.id})")
        
        # Debug: Check if message-topic associations were created
        print("\nChecking message-topic associations directly in the database...")
        associations = db.query(MessageTopic).filter(MessageTopic.message_id == message.id).all()
        print(f"Found {len(associations)} associations in the database")
        for assoc in associations:
            topic = db.query(Topic).filter(Topic.id == assoc.topic_id).first()
            print(f"  - Message {assoc.message_id} is associated with topic '{topic.name}' (ID: {topic.id})")
        
        # Test retrieving topics for the message
        print("\nRetrieving topics for the message using the service...")
        message_topics = topic_service.get_message_topics(message.id)
        
        print(f"Retrieved {len(message_topics)} topics for message:")
        for topic in message_topics:
            print(f"  - {topic.name} (ID: {topic.id})")
            
        # Debug: Look at the implementation of get_message_topics
        print("\nDebugging get_message_topics implementation:")
        print("Method source code:")
        import inspect
        print(inspect.getsource(topic_service.get_message_topics))
        
        # Test with an existing topic
        print("\nTesting with an existing topic...")
        # Use a timestamp to make the topic name unique
        topic_name = f"test_programming_{timestamp}"
        existing_topic = Topic(name=topic_name)
        db.add(existing_topic)
        db.commit()
        print(f"Created existing topic '{topic_name}' with ID: {existing_topic.id}")
        
        # Debug: Add the topic directly to the message content to ensure it's extracted
        message2 = Message(
            content=f"TEST_TOPIC_TAGGING_{timestamp} Another message about {topic_name} programming and coding.",
            conversation_id=conversation.id,
            user_id=test_user.id
        )
        db.add(message2)
        db.commit()
        print(f"Created second message with ID: {message2.id}")
        
        # Debug: Look at the topic extraction process
        print("\nDebugging topic extraction for second message:")
        raw_topics = topic_service.topic_extractor.extract_topics(message2.content, top_n=5)
        print(f"Raw extracted topics: {raw_topics}")
        
        # Tag the message
        topics2 = topic_service.tag_message(message2, top_n=5)
        
        print(f"Second message tagged with {len(topics2)} topics:")
        for topic in topics2:
            print(f"  - {topic.name} (ID: {topic.id})")
        
        # Check if the existing topic was reused
        reused = any(t.id == existing_topic.id for t in topics2)
        print(f"Existing topic was reused: {reused}")
        
        # Debug: Check associations for the second message
        print("\nChecking message-topic associations for second message...")
        associations2 = db.query(MessageTopic).filter(MessageTopic.message_id == message2.id).all()
        print(f"Found {len(associations2)} associations in the database")
        for assoc in associations2:
            topic = db.query(Topic).filter(Topic.id == assoc.topic_id).first()
            print(f"  - Message {assoc.message_id} is associated with topic '{topic.name}' (ID: {topic.id})")
        
        print("\nTests completed successfully!")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
