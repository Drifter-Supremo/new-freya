"""
Test script for topic relevance scoring.

This script demonstrates the advanced topic relevance scoring functionality.
It creates test data with various topics and timestamps, then compares
the results of basic and advanced topic search.
"""
import os
import sys
from datetime import datetime, timezone, timedelta

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.services.topic_tagging import TopicTaggingService
from app.services.topic_search import TopicSearchService

# Test messages with various topics
TEST_MESSAGES = [
    # Work-related messages
    "I love my job as a software engineer at Google.",
    "My work project deadline is next week.",
    "I had a meeting with my boss today.",
    
    # Health-related messages
    "I've been feeling stressed lately and should see a doctor.",
    "My health has improved since I started exercising regularly.",
    "I need to schedule a checkup with my doctor.",
    
    # Family-related messages
    "My family is coming to visit next month.",
    "I miss my parents and siblings who live far away.",
    "I'm planning a surprise party for my mom's birthday.",
    
    # Hobby-related messages
    "I love playing guitar in my free time.",
    "Hiking in the mountains is my favorite weekend activity.",
    "I'm learning to cook Italian food as a new hobby."
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
        print("Starting topic relevance scoring tests...")
        
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
        
        # Create messages with different timestamps
        topic_tagging_service = TopicTaggingService(session)
        now = datetime.now(timezone.utc)
        
        print("\n=== Creating Test Messages with Different Timestamps ===")
        
        # Group 1: Recent work messages (last 2 days)
        print("\nGroup 1: Recent work messages (0-1 days old)")
        for i, content in enumerate(TEST_MESSAGES[:3]):
            message = Message(
                content=content,
                user_id=user.id,
                conversation_id=conversation.id,
                timestamp=now - timedelta(days=i % 2)  # 0-1 days ago
            )
            session.add(message)
            session.commit()
            
            topics = topic_tagging_service.tag_message(message)
            print(f"Message: \"{content}\"")
            print(f"  Timestamp: {message.timestamp} ({i % 2} days ago)")
            print(f"  Tagged with: {[t.name for t in topics]}")
        
        # Group 2: Older health messages (3-5 days ago)
        print("\nGroup 2: Older health messages (3-5 days old)")
        for i, content in enumerate(TEST_MESSAGES[3:6]):
            message = Message(
                content=content,
                user_id=user.id,
                conversation_id=conversation.id,
                timestamp=now - timedelta(days=3 + i)  # 3-5 days ago
            )
            session.add(message)
            session.commit()
            
            topics = topic_tagging_service.tag_message(message)
            print(f"Message: \"{content}\"")
            print(f"  Timestamp: {message.timestamp} ({3 + i} days ago)")
            print(f"  Tagged with: {[t.name for t in topics]}")
        
        # Group 3: Very old family messages (10-12 days ago)
        print("\nGroup 3: Old family messages (10-12 days old)")
        for i, content in enumerate(TEST_MESSAGES[6:9]):
            message = Message(
                content=content,
                user_id=user.id,
                conversation_id=conversation.id,
                timestamp=now - timedelta(days=10 + i)  # 10-12 days ago
            )
            session.add(message)
            session.commit()
            
            topics = topic_tagging_service.tag_message(message)
            print(f"Message: \"{content}\"")
            print(f"  Timestamp: {message.timestamp} ({10 + i} days ago)")
            print(f"  Tagged with: {[t.name for t in topics]}")
        
        # Group 4: Mix of recent and old hobby messages
        print("\nGroup 4: Mixed hobby messages (various ages)")
        
        # Recent guitar message
        message = Message(
            content=TEST_MESSAGES[9],  # Guitar
            user_id=user.id,
            conversation_id=conversation.id,
            timestamp=now - timedelta(days=1)  # 1 day ago
        )
        session.add(message)
        session.commit()
        topics = topic_tagging_service.tag_message(message)
        print(f"Message: \"{TEST_MESSAGES[9]}\"")
        print(f"  Timestamp: {message.timestamp} (1 day ago)")
        print(f"  Tagged with: {[t.name for t in topics]}")
        
        # Older hiking message
        message = Message(
            content=TEST_MESSAGES[10],  # Hiking
            user_id=user.id,
            conversation_id=conversation.id,
            timestamp=now - timedelta(days=7)  # 7 days ago
        )
        session.add(message)
        session.commit()
        topics = topic_tagging_service.tag_message(message)
        print(f"Message: \"{TEST_MESSAGES[10]}\"")
        print(f"  Timestamp: {message.timestamp} (7 days ago)")
        print(f"  Tagged with: {[t.name for t in topics]}")
        
        # Recent cooking message
        message = Message(
            content=TEST_MESSAGES[11],  # Cooking
            user_id=user.id,
            conversation_id=conversation.id,
            timestamp=now - timedelta(days=2)  # 2 days ago
        )
        session.add(message)
        session.commit()
        topics = topic_tagging_service.tag_message(message)
        print(f"Message: \"{TEST_MESSAGES[11]}\"")
        print(f"  Timestamp: {message.timestamp} (2 days ago)")
        print(f"  Tagged with: {[t.name for t in topics]}")
        
        # Create the topic search service
        topic_search_service = TopicSearchService(session)
        
        # Test search queries
        search_queries = [
            "work job career",
            "health medical doctor",
            "family parents siblings",
            "hobbies leisure activities",
            "music guitar",
            "hiking outdoors",
            "cooking food"
        ]
        
        print("\n=== Comparing Basic vs Advanced Topic Search ===")
        
        for query in search_queries:
            print(f"\nQuery: '{query}'")
            
            # Basic search
            basic_results = topic_search_service.search_topics(user.id, query, limit=5)
            print("\nBasic Search Results:")
            if basic_results:
                for i, (topic, score) in enumerate(basic_results):
                    print(f"  {i+1}. {topic.name} (Score: {score:.4f})")
            else:
                print("  No results found")
            
            # Advanced search
            advanced_results = topic_search_service.search_topics_advanced(user.id, query, limit=5)
            print("\nAdvanced Search Results:")
            if advanced_results:
                for i, (topic, score) in enumerate(advanced_results):
                    print(f"  {i+1}. {topic.name} (Score: {score:.4f})")
            else:
                print("  No results found")
            
            # Compare results
            if basic_results and advanced_results:
                basic_top = basic_results[0][0].name
                advanced_top = advanced_results[0][0].name
                if basic_top != advanced_top:
                    print(f"\n  Difference in top result: Basic: '{basic_top}' vs Advanced: '{advanced_top}'")
                    
                    # Explain why the advanced result is different
                    if advanced_top.lower() in ["work", "job", "career"] and query.lower() != "work job career":
                        print("  Advanced search ranked work topics higher due to recency (0-1 days old)")
                    elif advanced_top.lower() in ["music", "guitar", "entertainment"] and query.lower() != "music guitar":
                        print("  Advanced search ranked music topics higher due to recency (1 day old)")
        
        print("\nTopic relevance scoring tests completed successfully!")
        
    except Exception as e:
        print(f"Error during topic relevance tests: {e}")
    finally:
        # Clean up
        try:
            # Delete all message_topics first
            session.execute(text(f"DELETE FROM messagetopics WHERE message_id IN (SELECT id FROM messages WHERE user_id = {user.id})"))
            # Delete messages
            session.execute(text(f"DELETE FROM messages WHERE user_id = {user.id}"))
            # Delete conversation
            session.execute(text(f"DELETE FROM conversations WHERE user_id = {user.id}"))
            # Delete user
            session.execute(text(f"DELETE FROM users WHERE id = {user.id}"))
            session.commit()
            print("\nTest data cleaned up successfully")
        except Exception as e:
            print(f"Error during cleanup: {e}")
        
        session.close()

if __name__ == "__main__":
    main()
