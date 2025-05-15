"""
Tests for the topic memory service.

These tests verify that the topic memory service works correctly.
"""
import pytest
import os
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.models import Base
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.topic import Topic, MessageTopic
from app.services.topic_memory_service import TopicMemoryService
from app.services.topic_tagging import TopicTaggingService

# Test data
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

@pytest.fixture
def db_session():
    """Create a test database session."""
    # Get database URL from environment variable
    DB_URL = os.getenv("POSTGRES_URL").replace('postgresql+psycopg2://', 'postgresql://')
    if not DB_URL:
        pytest.skip("POSTGRES_URL environment variable not set")
    
    # Create engine and session
    engine = create_engine(DB_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Return the session
    yield db
    
    # Close the session
    db.close()

@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        username=f"testuser_{datetime.now(timezone.utc).timestamp()}",
        email=f"test_{datetime.now(timezone.utc).timestamp()}@example.com",
        hashed_password="hashed_password"
    )
    db_session.add(user)
    db_session.commit()
    
    # Store the user ID for cleanup
    user_id = user.id
    
    yield user
    
    # Clean up - delete all related data first
    try:
        # Delete message_topics first
        db_session.execute(text(f"DELETE FROM messagetopics WHERE message_id IN (SELECT id FROM messages WHERE user_id = {user_id})"))
        # Delete messages
        db_session.execute(text(f"DELETE FROM messages WHERE user_id = {user_id}"))
        # Delete conversations
        db_session.execute(text(f"DELETE FROM conversations WHERE user_id = {user_id}"))
        # Delete user
        db_session.execute(text(f"DELETE FROM users WHERE id = {user_id}"))
        db_session.commit()
    except Exception as e:
        print(f"Error during cleanup: {e}")
        db_session.rollback()

@pytest.fixture
def test_data(db_session, test_user):
    """Create test data with messages and topics."""
    # Create a conversation
    conversation = Conversation(user_id=test_user.id)
    db_session.add(conversation)
    db_session.commit()
    
    # Create messages with different timestamps
    messages = []
    topic_service = TopicTaggingService(db_session)
    
    # Create messages with different timestamps (some recent, some older)
    now = datetime.now(timezone.utc)
    
    # Group 1: Recent work messages (last 2 days)
    for i, content in enumerate(TEST_MESSAGES[:3]):
        message = Message(
            content=content,
            user_id=test_user.id,
            conversation_id=conversation.id,
            timestamp=now - timedelta(days=i % 2)  # 0-1 days ago
        )
        db_session.add(message)
        db_session.commit()
        topic_service.tag_message(message)
        messages.append(message)
    
    # Group 2: Older health messages (3-5 days ago)
    for i, content in enumerate(TEST_MESSAGES[3:6]):
        message = Message(
            content=content,
            user_id=test_user.id,
            conversation_id=conversation.id,
            timestamp=now - timedelta(days=3 + i)  # 3-5 days ago
        )
        db_session.add(message)
        db_session.commit()
        topic_service.tag_message(message)
        messages.append(message)
    
    # Group 3: Very old family messages (10-12 days ago)
    for i, content in enumerate(TEST_MESSAGES[6:9]):
        message = Message(
            content=content,
            user_id=test_user.id,
            conversation_id=conversation.id,
            timestamp=now - timedelta(days=10 + i)  # 10-12 days ago
        )
        db_session.add(message)
        db_session.commit()
        topic_service.tag_message(message)
        messages.append(message)
    
    # Group 4: Mix of recent and old hobby messages
    message = Message(
        content=TEST_MESSAGES[9],  # Guitar (recent)
        user_id=test_user.id,
        conversation_id=conversation.id,
        timestamp=now - timedelta(days=1)  # 1 day ago
    )
    db_session.add(message)
    db_session.commit()
    topic_service.tag_message(message)
    messages.append(message)
    
    message = Message(
        content=TEST_MESSAGES[10],  # Hiking (older)
        user_id=test_user.id,
        conversation_id=conversation.id,
        timestamp=now - timedelta(days=7)  # 7 days ago
    )
    db_session.add(message)
    db_session.commit()
    topic_service.tag_message(message)
    messages.append(message)
    
    message = Message(
        content=TEST_MESSAGES[11],  # Cooking (recent)
        user_id=test_user.id,
        conversation_id=conversation.id,
        timestamp=now - timedelta(days=2)  # 2 days ago
    )
    db_session.add(message)
    db_session.commit()
    topic_service.tag_message(message)
    messages.append(message)
    
    yield test_user, messages

def test_get_topic_memory_context(db_session, test_data):
    """Test retrieving memory context for a specific topic."""
    user, _ = test_data
    service = TopicMemoryService(db_session)
    
    # Get all topics for the user
    topics = db_session.query(Topic).join(MessageTopic).join(Message).filter(Message.user_id == user.id).distinct().all()
    assert len(topics) > 0
    
    # Get memory context for the first topic
    topic_context = service.get_topic_memory_context(user.id, topics[0].id, message_limit=5)
    
    # Verify the context structure
    assert "topic" in topic_context
    assert "id" in topic_context["topic"]
    assert "name" in topic_context["topic"]
    assert "message_count" in topic_context
    assert "messages" in topic_context
    assert len(topic_context["messages"]) > 0
    
    # Verify message structure
    for message in topic_context["messages"]:
        assert "content" in message
        assert "user_id" in message
        assert "timestamp" in message

def test_get_memory_context_by_query(db_session, test_data):
    """Test retrieving memory context based on a query."""
    user, _ = test_data
    service = TopicMemoryService(db_session)
    
    # Get memory context for a work-related query
    topic_context = service.get_memory_context_by_query(
        user_id=user.id,
        query="work job project",
        topic_limit=3,
        message_limit=3,
        use_advanced_scoring=True
    )
    
    # Verify the context structure
    assert "topic_memories" in topic_context
    assert len(topic_context["topic_memories"]) > 0
    
    # Verify topic memory structure
    for topic_memory in topic_context["topic_memories"]:
        assert "topic" in topic_memory
        assert "id" in topic_memory["topic"]
        assert "name" in topic_memory["topic"]
        assert "relevance_score" in topic_memory["topic"]
        assert "relevance" in topic_memory["topic"]
        assert "message_count" in topic_memory
        assert "messages" in topic_memory
        assert len(topic_memory["messages"]) > 0
    
    # Verify that work-related topics are included
    topic_names = [tm["topic"]["name"].lower() for tm in topic_context["topic_memories"]]
    assert any(name in ["work", "job", "career"] for name in topic_names)

def test_get_comprehensive_memory_context(db_session, test_data):
    """Test retrieving comprehensive memory context."""
    user, _ = test_data
    service = TopicMemoryService(db_session)
    
    # Get comprehensive memory context
    memory_context = service.get_comprehensive_memory_context(
        user_id=user.id,
        query="work health family hobbies",
        topic_limit=5,
        message_limit=3,
        use_advanced_scoring=True
    )
    
    # Verify the context structure
    assert "topic_memories" in memory_context
    assert "recent_memories" in memory_context
    assert "user_facts" in memory_context
    
    # Verify topic memories
    assert len(memory_context["topic_memories"]) > 0
    
    # Verify recent memories
    assert len(memory_context["recent_memories"]) > 0
    
    # Verify that multiple topics are included
    topic_names = [tm["topic"]["name"].lower() for tm in memory_context["topic_memories"]]
    assert len(set(topic_names)) > 1  # Should have multiple unique topics
