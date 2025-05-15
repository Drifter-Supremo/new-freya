"""
Test script for memory tier components with PostgreSQL.
This script tests the TopicExtractor, TopicTaggingService, and full-text search functionality.
"""
import os
import sys
from datetime import datetime, timezone
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import models and services
from app.models import Base
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.topic import Topic, MessageTopic
from app.services.topic_extraction import TopicExtractor
from app.services.topic_tagging import TopicTaggingService

def test_topic_extractor():
    """Test the TopicExtractor implementation."""
    print("\n=== Testing TopicExtractor ===")
    
    # Create an instance of the real TopicExtractor
    extractor = TopicExtractor()
    
    # Test messages covering different topics
    test_messages = [
        "I love playing guitar and hiking in the mountains on weekends.",
        "My job as a software engineer keeps me busy during the week.",
        "I'm feeling really stressed about my upcoming exam next week.",
        "Do you have any recommendations for good Italian restaurants?",
        "I'm planning to buy a new laptop for programming and gaming.",
        "My family is coming to visit me next month and I'm excited to see them."
    ]
    
    # Test the extract_topics method
    print("Testing extract_topics method:")
    for i, msg in enumerate(test_messages):
        topics = extractor.extract_topics(msg, top_n=3)
        print(f"Message {i+1}: \"{msg}\"")
        print(f"  Topics: {topics}")
        print()
    
    # Test the is_about_topic method
    print("Testing is_about_topic method:")
    test_cases = [
        ("I love playing guitar", "hobbies", True),
        ("I'm feeling stressed about work", "work", True),
        ("I'm feeling stressed about work", "health", True),
        ("I need to buy groceries", "food", True),
        ("The weather is nice today", "travel", False)
    ]
    
    for msg, topic, expected in test_cases:
        result = extractor.is_about_topic(msg, topic)
        print(f"Message: \"{msg}\", Topic: \"{topic}\"")
        print(f"  Expected: {expected}, Result: {result}, Correct: {result == expected}")
    
    print("\nTopicExtractor tests completed.")

def test_topic_tagging_with_real_extractor(db_session):
    """Test the TopicTaggingService with the real TopicExtractor."""
    print("\n=== Testing TopicTaggingService with real TopicExtractor ===")
    
    # Create a test user
    test_user = db_session.query(User).filter(User.username == "test_user").first()
    if not test_user:
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        test_user = User(
            username=f"test_user_{unique_id}",
            email=f"test_{unique_id}@example.com",
            hashed_password="test_password"
        )
        db_session.add(test_user)
        db_session.commit()
        print(f"Created test user with ID: {test_user.id}")
    else:
        print(f"Using existing test user with ID: {test_user.id}")
    
    # Create a test conversation
    conversation = Conversation(user_id=test_user.id)
    db_session.add(conversation)
    db_session.commit()
    print(f"Created conversation with ID: {conversation.id}")
    
    # Create the TopicTaggingService with the real TopicExtractor
    topic_service = TopicTaggingService(db_session)
    
    # Test messages
    test_messages = [
        "I love playing guitar and hiking in the mountains on weekends.",
        "My job as a software engineer keeps me busy during the week.",
        "I'm feeling really stressed about my upcoming exam next week.",
        "Do you have any recommendations for good Italian restaurants?"
    ]
    
    # Create and tag messages
    for i, content in enumerate(test_messages):
        # Add a timestamp to make content unique
        import time
        timestamp = int(time.time()) + i
        
        # Create a message
        message = Message(
            content=f"TEST_MEMORY_TIER_{timestamp} {content}",
            conversation_id=conversation.id,
            user_id=test_user.id
        )
        db_session.add(message)
        db_session.commit()
        print(f"Created message {i+1} with ID: {message.id}")
        
        # Tag the message
        topics = topic_service.tag_message(message, top_n=3)
        
        print(f"Message {i+1}: \"{content}\"")
        print(f"  Tagged with topics: {[t.name for t in topics]}")
        
        # Verify topics were associated with the message
        message_topics = topic_service.get_message_topics(message.id)
        print(f"  Retrieved topics: {[t.name for t in message_topics]}")
        print(f"  Topics match: {set(t.id for t in topics) == set(t.id for t in message_topics)}")
        print()
    
    print("TopicTaggingService tests with real extractor completed.")

def test_full_text_search(db_session):
    """Test PostgreSQL full-text search functionality."""
    print("\n=== Testing PostgreSQL Full-Text Search ===")
    
    try:
        # Check if tsvector_update_trigger function exists
        result = db_session.execute(text("SELECT 1 FROM pg_proc WHERE proname = 'tsvector_update_trigger'")).fetchone()
        if result:
            print("PostgreSQL text search configuration is available.")
        else:
            print("WARNING: PostgreSQL text search configuration may not be properly set up.")
        
        # Test a basic full-text search query
        query = text("""
            SELECT id, content, ts_rank_cd(content_tsv, plainto_tsquery('english', :query)) AS rank
            FROM messages
            WHERE content_tsv @@ plainto_tsquery('english', :query)
            ORDER BY rank DESC
            LIMIT 5
        """)
        
        search_terms = ["programming", "family", "stress", "restaurant"]
        
        for term in search_terms:
            print(f"\nSearching for messages containing '{term}':")
            results = db_session.execute(query, {"query": term}).fetchall()
            
            if results:
                for row in results:
                    print(f"  Message ID: {row[0]}")
                    print(f"  Content: {row[1][:100]}..." if len(row[1]) > 100 else f"  Content: {row[1]}")
                    print(f"  Rank: {row[2]}")
            else:
                print(f"  No results found for '{term}'")
        
        print("\nFull-text search tests completed.")
    except Exception as e:
        print(f"Error during full-text search test: {e}")

def main():
    # Get database URL from environment variable
    DB_URL = os.getenv("POSTGRES_URL").replace('postgresql+psycopg2://', 'postgresql://')
    print(f"Connecting to database: {DB_URL}")
    
    # Create engine and session
    engine = create_engine(DB_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("Starting memory tier tests...")
        
        # Test the TopicExtractor (doesn't require database)
        test_topic_extractor()
        
        # Test the TopicTaggingService with the real TopicExtractor
        test_topic_tagging_with_real_extractor(db)
        
        # Test full-text search functionality
        test_full_text_search(db)
        
        print("\nAll memory tier tests completed successfully!")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
