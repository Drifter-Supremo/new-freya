"""
Test script for topic memory retrieval.

This script demonstrates the topic memory retrieval functionality.
It creates test data with various topics and timestamps, then retrieves
memory context using different queries.
"""
import os
import sys
import json
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
from app.services.topic_memory_service import TopicMemoryService
from app.core.memory_context_service import assemble_memory_context

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

def pretty_print_json(data):
    """Print data as formatted JSON."""
    print(json.dumps(data, indent=2, default=str))

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
        print("Starting topic memory retrieval tests...")
        
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
        
        # Create the topic memory service
        topic_memory_service = TopicMemoryService(session)
        
        # Test memory context retrieval
        test_queries = [
            "Tell me about your work",
            "How is your health?",
            "Tell me about your family",
            "What are your hobbies?",
            "Do you have any health issues and what do you do for work?"
        ]
        
        print("\n=== Testing Topic Memory Retrieval ===")
        
        for query in test_queries:
            print(f"\nQuery: '{query}'")
            
            # Get topic memory context
            topic_context = topic_memory_service.get_memory_context_by_query(
                user_id=user.id,
                query=query,
                topic_limit=3,
                message_limit=2,
                use_advanced_scoring=True
            )
            
            print("\nTopic Memory Context:")
            if topic_context["topic_memories"]:
                for i, topic_memory in enumerate(topic_context["topic_memories"]):
                    print(f"  Topic {i+1}: {topic_memory['topic']['name']} (Relevance: {topic_memory['topic']['relevance']}%)")
                    print(f"  Messages ({topic_memory['message_count']}):")
                    for j, message in enumerate(topic_memory["messages"]):
                        print(f"    {j+1}. {message['content']}")
            else:
                print("  No topic memories found")
        
        # Test comprehensive memory context
        print("\n=== Testing Comprehensive Memory Context ===")
        
        comprehensive_query = "Tell me about your work, health, and hobbies"
        print(f"\nQuery: '{comprehensive_query}'")
        
        # Get comprehensive memory context
        memory_context = topic_memory_service.get_comprehensive_memory_context(
            user_id=user.id,
            query=comprehensive_query,
            topic_limit=5,
            message_limit=2,
            use_advanced_scoring=True
        )
        
        print("\nComprehensive Memory Context:")
        print(f"  Topic Memories: {len(memory_context['topic_memories'])}")
        print(f"  Recent Memories: {len(memory_context['recent_memories'])}")
        
        # Test memory context service
        print("\n=== Testing Memory Context Service ===")
        
        memory_context_query = "What do you do for work and how is your health?"
        print(f"\nQuery: '{memory_context_query}'")
        
        # Get memory context
        context = assemble_memory_context(
            db=session,
            user_id=user.id,
            query=memory_context_query,
            use_advanced_scoring=True
        )
        
        print("\nMemory Context:")
        print(f"  User Facts: {len(context['user_facts'])}")
        print(f"  Recent Memories: {len(context['recent_memories'])}")
        print(f"  Topic Memories: {len(context['topic_memories'])}")
        
        if context['topic_memories']:
            print("\nTop Topic Memories:")
            for i, topic_memory in enumerate(context['topic_memories'][:2]):
                print(f"  Topic {i+1}: {topic_memory['topic']['name']} (Relevance: {topic_memory['topic']['relevance']}%)")
                print(f"  Messages ({len(topic_memory['messages'])}):")
                for j, message in enumerate(topic_memory['messages'][:2]):
                    print(f"    {j+1}. {message['content']}")
        
        print("\nTopic memory retrieval tests completed successfully!")
        
    except Exception as e:
        print(f"Error during topic memory tests: {e}")
        import traceback
        traceback.print_exc()
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
