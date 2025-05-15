"""
Test script for database integration with memory tier components.
"""
import os
import sys
import uuid
import time

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import database and model components
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

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
        print("Testing database integration...")
        
        # 1. Check if we can query the database
        print("\nQuerying existing topics:")
        topics = db.query(Topic).limit(5).all()
        if topics:
            print(f"Found {len(topics)} topics in database:")
            for topic in topics:
                print(f"  - {topic.name} (ID: {topic.id})")
        else:
            print("No topics found in database.")
        
        # 2. Create a test user with unique identifiers
        unique_id = str(uuid.uuid4())[:8]
        test_username = f"test_user_{unique_id}"
        test_email = f"test_{unique_id}@example.com"
        
        print(f"\nCreating test user: {test_username}")
        test_user = User(
            username=test_username,
            email=test_email,
            hashed_password="test_password"
        )
        db.add(test_user)
        db.commit()
        print(f"Created user with ID: {test_user.id}")
        
        # 3. Create a test conversation
        print("\nCreating test conversation")
        conversation = Conversation(user_id=test_user.id)
        db.add(conversation)
        db.commit()
        print(f"Created conversation with ID: {conversation.id}")
        
        # 4. Create a test message with a timestamp to make it unique
        timestamp = int(time.time())
        test_content = f"TEST_DB_INTEGRATION_{timestamp} I love programming in Python and playing guitar on weekends."
        
        print("\nCreating test message")
        message = Message(
            content=test_content,
            conversation_id=conversation.id,
            user_id=test_user.id
        )
        db.add(message)
        db.commit()
        print(f"Created message with ID: {message.id}")
        
        # 5. Test the TopicTaggingService
        print("\nTesting TopicTaggingService")
        topic_service = TopicTaggingService(db)
        
        # Tag the message
        topics = topic_service.tag_message(message, top_n=3)
        print(f"Tagged message with {len(topics)} topics:")
        for topic in topics:
            print(f"  - {topic.name} (ID: {topic.id})")
        
        # 6. Verify topics were associated with the message
        print("\nVerifying message-topic associations")
        message_topics = topic_service.get_message_topics(message.id)
        print(f"Retrieved {len(message_topics)} topics for message:")
        for topic in message_topics:
            print(f"  - {topic.name} (ID: {topic.id})")
        
        # Check if the topics match
        topics_match = set(t.id for t in topics) == set(t.id for t in message_topics)
        print(f"Topics match: {topics_match}")
        
        # 7. Test full-text search if available
        print("\nTesting full-text search")
        try:
            query = text("""
                SELECT id, content, ts_rank_cd(content_tsv, plainto_tsquery('english', :query)) AS rank
                FROM messages
                WHERE content_tsv @@ plainto_tsquery('english', :query)
                ORDER BY rank DESC
                LIMIT 5
            """)
            
            search_term = "programming"
            print(f"Searching for messages containing '{search_term}':")
            results = db.execute(query, {"query": search_term}).fetchall()
            
            if results:
                for row in results:
                    print(f"  Message ID: {row[0]}")
                    content_preview = row[1][:100] + "..." if len(row[1]) > 100 else row[1]
                    print(f"  Content: {content_preview}")
                    print(f"  Rank: {row[2]}")
            else:
                print(f"  No results found for '{search_term}'")
                
        except Exception as e:
            print(f"Full-text search test failed: {e}")
        
        print("\nDatabase integration tests completed successfully!")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        db.rollback()
    finally:
        # Clean up test data
        try:
            print("\nCleaning up test data...")
            db.query(MessageTopic).filter(MessageTopic.message_id == message.id).delete()
            db.query(Message).filter(Message.id == message.id).delete()
            db.query(Conversation).filter(Conversation.id == conversation.id).delete()
            db.query(User).filter(User.id == test_user.id).delete()
            db.commit()
            print("Test data cleaned up successfully.")
        except Exception as e:
            print(f"Error during cleanup: {e}")
            db.rollback()
        
        db.close()

if __name__ == "__main__":
    main()
