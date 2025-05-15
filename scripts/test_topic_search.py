"""
Test script for topic search functionality.

This script tests the TopicSearchService with real data in a PostgreSQL database.
It demonstrates:
1. Setting up the database and services
2. Creating test data
3. Tagging messages with topics
4. Searching for topics based on queries
5. Retrieving messages for specific topics
"""
import os
import sys
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
from app.services.topic_search import TopicSearchService

# Test messages with various topics
TEST_MESSAGES = [
    "I love programming in Python and JavaScript. It's my favorite hobby.",
    "My job as a software engineer at Google keeps me busy during the week.",
    "I've been feeling stressed about my health lately. I should see a doctor.",
    "Do you have any recommendations for good Italian restaurants in New York?",
    "I'm planning to buy a new laptop for programming and gaming.",
    "My family is coming to visit me next month and I'm excited to see them.",
    "I've been learning to play guitar in my free time. Music is relaxing.",
    "I'm saving money to buy a house next year. Real estate is expensive.",
    "I went hiking in the mountains last weekend. The views were amazing.",
    "I'm thinking about adopting a dog. Pets are great companions."
]

def main():
    # Get database URL from environment variable
    DB_URL = os.getenv("POSTGRES_URL").replace('postgresql+psycopg2://', 'postgresql://')
    if not DB_URL:
        print("Error: POSTGRES_URL environment variable not set")
        sys.exit(1)
    
    print(f"Connecting to database: {DB_URL}")
    
    # Create engine and session
    engine = create_engine(DB_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        print("Starting topic search tests...")
        
        # Create a test user
        username = f"testuser_{datetime.now(timezone.utc).timestamp()}"
        email = f"test_{datetime.now(timezone.utc).timestamp()}@example.com"
        
        user = User(
            username=username,
            email=email,
            hashed_password="hashed_password"
        )
        session.add(user)
        session.commit()
        print(f"Created test user: {username} (ID: {user.id})")
        
        # Create a conversation
        conversation = Conversation(user_id=user.id)
        session.add(conversation)
        session.commit()
        print(f"Created conversation with ID: {conversation.id}")
        
        # Create messages and tag them with topics
        topic_tagging_service = TopicTaggingService(session)
        
        print("\n=== Creating Test Messages and Tagging with Topics ===")
        for i, content in enumerate(TEST_MESSAGES):
            # Create message
            message = Message(
                content=content,
                user_id=user.id,
                conversation_id=conversation.id
            )
            session.add(message)
            session.commit()
            
            # Tag message with topics
            topics = topic_tagging_service.tag_message(message, top_n=3)
            
            print(f"Message {i+1}: \"{content[:50]}...\"")
            print(f"  Tagged with topics: {[t.name for t in topics]}")
        
        # Create the topic search service
        topic_search_service = TopicSearchService(session)
        
        # Test searching for topics
        print("\n=== Testing Topic Search ===")
        search_queries = ["programming", "health", "family", "food", "music"]
        
        for query in search_queries:
            print(f"\nSearching for topics related to '{query}':")
            results = topic_search_service.search_topics(user.id, query)
            
            if results:
                print(f"Found {len(results)} relevant topics:")
                for topic, score in results:
                    print(f"  - {topic.name} (Score: {score:.4f})")
                
                # Get messages for the top topic
                top_topic = results[0][0]
                print(f"\nMessages for top topic '{top_topic.name}':")
                messages = topic_search_service.get_messages_by_topic(user.id, top_topic.id, limit=3)
                
                for msg in messages:
                    preview = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
                    print(f"  - {preview}")
            else:
                print(f"No topics found for query '{query}'")
        
        # Test getting all topics for a user
        print("\n=== Testing Get User Topics ===")
        all_topics = topic_search_service.get_user_topics(user.id)
        
        print(f"All topics for user (total: {len(all_topics)}):")
        for topic in all_topics:
            print(f"  - {topic.name}")
        
        print("\nTopic search tests completed successfully!")
        
    except Exception as e:
        print(f"Error during topic search tests: {e}")
    finally:
        # Clean up
        try:
            # Delete all messages
            session.query(Message).filter(Message.user_id == user.id).delete()
            # Delete conversation
            session.query(Conversation).filter(Conversation.id == conversation.id).delete()
            # Delete user
            session.query(User).filter(User.id == user.id).delete()
            session.commit()
            print("\nTest data cleaned up successfully")
        except Exception as e:
            print(f"Error during cleanup: {e}")
        
        session.close()

if __name__ == "__main__":
    main()
