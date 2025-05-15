"""
Topic Tagging Demo

This script demonstrates how to use the TopicTaggingService to tag messages with topics.
It shows:
1. Setting up the database and services
2. Creating test data
3. Tagging messages with topics
4. Querying messages by topic
"""
import sys
import os
from datetime import datetime, timezone

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.services.topic_tagging import TopicTaggingService

def setup_database():
    """Set up an in-memory SQLite database for the demo."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    return engine

def create_test_data(session):
    """Create test users, conversations, and messages."""
    # Create a test user
    user = User(
        username="demo_user",
        email="demo@example.com",
        hashed_password="hashed_password"
    )
    session.add(user)
    session.flush()
    
    # Create a test conversation
    conversation = Conversation(
        user_id=user.id,
        title="Test Conversation",
        created_at=datetime.now(timezone.utc)
    )
    session.add(conversation)
    session.flush()
    
    # Create some test messages
    messages = [
        {
            "content": "I love programming in Python and JavaScript. They're my favorite languages!",
            "user_id": user.id,
            "conversation_id": conversation.id,
            "timestamp": datetime.now(timezone.utc)
        },
        {
            "content": "I enjoy hiking in the mountains and playing guitar in my free time.",
            "user_id": user.id,
            "conversation_id": conversation.id,
            "timestamp": datetime.now(timezone.utc)
        },
        {
            "content": "Working on a new web project using React and FastAPI. It's challenging but fun!",
            "user_id": user.id,
            "conversation_id": conversation.id,
            "timestamp": datetime.now(timezone.utc)
        },
        {
            "content": "Just finished reading a great book about machine learning and AI.",
            "user_id": user.id,
            "conversation_id": conversation.id,
            "timestamp": datetime.now(timezone.utc)
        },
        {
            "content": "Planning a trip to Japan next year. Need to start learning some basic Japanese phrases.",
            "user_id": user.id,
            "conversation_id": conversation.id,
            "timestamp": datetime.now(timezone.utc)
        }
    ]
    
    # Add messages to the session
    for msg_data in messages:
        message = Message(**msg_data)
        session.add(message)
    
    session.commit()
    
    # Return the conversation and user for reference
    return {"user": user, "conversation": conversation}

def main():
    print("=== Topic Tagging Demo ===\n")
    
    # Set up the database and create a session
    engine = setup_database()
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Create test data
    print("Creating test data...")
    test_data = create_test_data(session)
    user = test_data["user"]
    conversation = test_data["conversation"]
    
    # Get all messages
    messages = session.query(Message).filter_by(conversation_id=conversation.id).all()
    print(f"Created {len(messages)} test messages.")
    
    # Initialize the topic tagging service
    tagging_service = TopicTaggingService(session)
    
    # Tag all messages
    print("\nTagging messages with topics...")
    results = tagging_service.tag_messages(messages)
    
    # Print the results
    print("\n=== Tagging Results ===")
    for msg in messages:
        topics = results[msg.id]
        topic_names = [t.name for t in topics]
        print(f"\nMessage: {msg.content[:60]}...")
        print(f"Topics: {', '.join(topic_names) if topic_names else 'None'}")
    
    # Show how to query messages by topic
    print("\n=== Querying Messages by Topic ===")
    
    # Get all topics
    topics = session.query(Topic).all()
    
    for topic in topics:
        topic_messages = tagging_service.get_topic_messages(topic.id)
        print(f"\nTopic: {topic.name} (ID: {topic.id})")
        print(f"Number of messages: {len(topic_messages)}")
        
        # Print a preview of messages for this topic
        for msg in topic_messages[:2]:  # Limit to 2 messages per topic for brevity
            preview = msg.content[:60] + ("..." if len(msg.content) > 60 else "")
            print(f"  - {preview}")
        if len(topic_messages) > 2:
            print(f"  - ... and {len(topic_messages) - 2} more")
    
    print("\n=== Demo Complete ===")
    session.close()

if __name__ == "__main__":
    main()
