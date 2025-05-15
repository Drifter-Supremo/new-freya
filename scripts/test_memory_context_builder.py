"""
test_memory_context_builder.py - Test script for the memory context builder

This script tests the memory context builder with a PostgreSQL database.
It verifies that memory query detection and topic extraction work correctly.
"""

import sys
from pathlib import Path
import os
import argparse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.memory_context_service import MemoryContextBuilder
from app.models import Base
from app.models.user import User
from app.models.message import Message
from app.models.topic import Topic, MessageTopic
from app.models.conversation import Conversation
from app.models.userfact import UserFact

# Test queries for memory detection
MEMORY_QUERIES = [
    "Do you remember what I told you about my job?",
    "What did I say about my family?",
    "Have we talked about my health before?",
    "Recall our conversation about movies.",
    "What do you know about my hobbies?",
    "Last time we discussed my vacation plans.",
    "Didn't I tell you about my new car?",
    "Am I right that we talked about my sister?"
]

# Non-memory queries
NON_MEMORY_QUERIES = [
    "What's the weather like today?",
    "Tell me a joke.",
    "How are you doing?",
    "What's your name?",
    "Can you help me with my homework?",
    "What time is it?",
    "I'm feeling sad today.",
    "Do you like pizza?"
]

# Topic-specific queries
TOPIC_QUERIES = [
    "Tell me about my family and my job.",
    "What do you know about my health and exercise routine?",
    "I'm interested in movies, books, and music.",
    "My education at university was challenging.",
    "I live in a house in the city with my family."
]


def create_test_data(db: Session, user_id: int = 1):
    """Create test data for the memory context builder."""
    print("Creating test data...")

    # Create a test user if it doesn't exist
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, name="Test User")
        db.add(user)
        db.commit()
        print(f"Created test user: {user.name} (ID: {user.id})")
    else:
        print(f"Using existing user: {user.name} (ID: {user.id})")

    # Create a test conversation if it doesn't exist
    conversation = db.query(Conversation).filter(Conversation.user_id == user_id).first()
    if not conversation:
        conversation = Conversation(user_id=user_id)
        db.add(conversation)
        db.commit()
        print(f"Created test conversation (ID: {conversation.id})")
    else:
        print(f"Using existing conversation (ID: {conversation.id})")

    # Create test user facts if they don't exist
    facts = db.query(UserFact).filter(UserFact.user_id == user_id).all()
    if not facts:
        test_facts = [
            UserFact(user_id=user_id, fact_type="job", value="Software Engineer at Google"),
            UserFact(user_id=user_id, fact_type="location", value="San Francisco"),
            UserFact(user_id=user_id, fact_type="family", value="Married with two kids"),
            UserFact(user_id=user_id, fact_type="hobby", value="Playing guitar and hiking"),
            UserFact(user_id=user_id, fact_type="education", value="Computer Science degree from Stanford")
        ]
        db.add_all(test_facts)
        db.commit()
        print(f"Created {len(test_facts)} test user facts")
    else:
        print(f"Using {len(facts)} existing user facts")

    # Create test messages and topics if they don't exist
    messages = db.query(Message).filter(Message.user_id == user_id).all()
    if not messages:
        # Create some topics
        topics = {
            "work": Topic(name="Work"),
            "family": Topic(name="Family"),
            "health": Topic(name="Health"),
            "hobbies": Topic(name="Hobbies"),
            "education": Topic(name="Education"),
            "location": Topic(name="Location")
        }

        for topic in topics.values():
            db.add(topic)
        db.commit()

        # Create some messages
        test_messages = [
            Message(conversation_id=conversation.id, user_id=user_id, content="I work as a Software Engineer at Google."),
            Message(conversation_id=conversation.id, user_id=user_id, content="My family includes my spouse and two children."),
            Message(conversation_id=conversation.id, user_id=user_id, content="I've been trying to improve my health by exercising more."),
            Message(conversation_id=conversation.id, user_id=user_id, content="I enjoy playing guitar and hiking on weekends."),
            Message(conversation_id=conversation.id, user_id=user_id, content="I studied Computer Science at Stanford University."),
            Message(conversation_id=conversation.id, user_id=user_id, content="I live in San Francisco, California.")
        ]

        db.add_all(test_messages)
        db.commit()

        # Associate messages with topics
        message_topics = [
            MessageTopic(message_id=test_messages[0].id, topic_id=topics["work"].id),
            MessageTopic(message_id=test_messages[1].id, topic_id=topics["family"].id),
            MessageTopic(message_id=test_messages[2].id, topic_id=topics["health"].id),
            MessageTopic(message_id=test_messages[3].id, topic_id=topics["hobbies"].id),
            MessageTopic(message_id=test_messages[4].id, topic_id=topics["education"].id),
            MessageTopic(message_id=test_messages[5].id, topic_id=topics["location"].id)
        ]

        db.add_all(message_topics)
        db.commit()

        print(f"Created {len(test_messages)} test messages with {len(message_topics)} topic associations")
    else:
        print(f"Using {len(messages)} existing messages")

    print("Test data creation complete.")


def test_memory_query_detection(builder: MemoryContextBuilder):
    """Test memory query detection."""
    print("\n=== Testing Memory Query Detection ===")

    print("\nMemory Queries:")
    for query in MEMORY_QUERIES:
        result = builder.is_memory_query(query)
        print(f"  '{query}' -> {'✓' if result else '✗'}")
        assert result, f"Failed to detect memory query: '{query}'"

    print("\nNon-Memory Queries:")
    for query in NON_MEMORY_QUERIES:
        result = builder.is_memory_query(query)
        print(f"  '{query}' -> {'✗' if not result else '✓'}")
        assert not result, f"Incorrectly detected as memory query: '{query}'"

    print("\nMemory query detection test passed.")


def test_topic_extraction(builder: MemoryContextBuilder):
    """Test topic extraction from queries."""
    print("\n=== Testing Topic Extraction ===")

    for query in TOPIC_QUERIES:
        topics = builder.extract_topics_from_query(query, top_n=5)
        print(f"\nQuery: '{query}'")
        print(f"Extracted topics: {topics}")
        assert topics, f"No topics extracted from query: '{query}'"

    print("\nTopic extraction test passed.")


def test_memory_context_assembly(builder: MemoryContextBuilder, user_id: int = 1):
    """Test memory context assembly."""
    print("\n=== Testing Memory Context Assembly ===")

    # Test with a memory query
    memory_query = "Do you remember what I told you about my job and family?"
    print(f"\nMemory Query: '{memory_query}'")

    memory_context = builder.assemble_memory_context(user_id, memory_query)

    print(f"Is Memory Query: {memory_context['is_memory_query']}")
    if "memory_query_topics" in memory_context:
        print(f"Memory Query Topics: {memory_context['memory_query_topics']}")

    print(f"User Facts: {len(memory_context['user_facts'])}")
    print(f"Recent Memories: {len(memory_context['recent_memories'])}")
    print(f"Topic Memories: {len(memory_context['topic_memories'])}")

    # Test with a non-memory query
    non_memory_query = "Tell me a joke about programming."
    print(f"\nNon-Memory Query: '{non_memory_query}'")

    non_memory_context = builder.assemble_memory_context(user_id, non_memory_query)

    print(f"Is Memory Query: {non_memory_context['is_memory_query']}")
    print(f"User Facts: {len(non_memory_context['user_facts'])}")
    print(f"Recent Memories: {len(non_memory_context['recent_memories'])}")
    print(f"Topic Memories: {len(non_memory_context['topic_memories'])}")

    print("\nMemory context assembly test passed.")


def main():
    """Main function to run the test script."""
    parser = argparse.ArgumentParser(description="Test the memory context builder")
    parser.add_argument("--db-url", help="Database URL (default: from environment variable)")
    parser.add_argument("--user-id", type=int, default=1, help="User ID to use for testing (default: 1)")
    parser.add_argument("--create-data", action="store_true", help="Create test data")
    args = parser.parse_args()

    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv()

    # Get database URL from environment variable, command line, or .env file
    db_url = args.db_url or os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
    if not db_url:
        print("Error: Database URL not provided. Use --db-url or set DATABASE_URL environment variable.")
        sys.exit(1)

    # Convert SQLAlchemy URL format to psycopg2 format if needed
    if db_url.startswith('postgresql+psycopg2://'):
        db_url = db_url.replace('postgresql+psycopg2://', 'postgresql://')

    # Create engine and session
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Create test data if requested
        if args.create_data:
            create_test_data(db, args.user_id)

        # Create memory context builder
        builder = MemoryContextBuilder(db)

        # Run tests
        test_memory_query_detection(builder)
        test_topic_extraction(builder)
        test_memory_context_assembly(builder, args.user_id)

        print("\nAll tests passed!")

    finally:
        db.close()


if __name__ == "__main__":
    main()
