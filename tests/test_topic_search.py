"""
Tests for the topic search service.

These tests verify that the topic search functionality works correctly with PostgreSQL.
"""
import pytest
import os
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

from app.models import Base
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.topic import Topic, MessageTopic
from app.services.topic_search import TopicSearchService
from app.services.topic_tagging import TopicTaggingService

# Test data
TEST_MESSAGES = [
    "I love programming in Python and JavaScript!",
    "My job as a software engineer keeps me busy during the week.",
    "I'm feeling stressed about my upcoming exam next week.",
    "Do you have any recommendations for good Italian restaurants?",
    "I'm planning to buy a new laptop for programming and gaming.",
    "My family is coming to visit me next month and I'm excited to see them."
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
def test_conversation(db_session, test_user):
    """Create a test conversation."""
    conversation = Conversation(user_id=test_user.id)
    db_session.add(conversation)
    db_session.commit()

    yield conversation

    # Cleanup is handled by test_user fixture

@pytest.fixture
def test_messages(db_session, test_user, test_conversation):
    """Create test messages with topics."""
    messages = []

    # Create messages
    for content in TEST_MESSAGES:
        message = Message(
            content=content,
            user_id=test_user.id,
            conversation_id=test_conversation.id
        )
        db_session.add(message)

    db_session.commit()

    # Tag messages with topics
    topic_service = TopicTaggingService(db_session)
    for message in db_session.query(Message).filter(Message.user_id == test_user.id).all():
        topic_service.tag_message(message, top_n=3)

    # Get all messages
    messages = db_session.query(Message).filter(Message.user_id == test_user.id).all()

    yield messages

    # Clean up is handled by test_conversation fixture

def test_search_topics(db_session, test_user, test_messages):
    """Test searching for topics based on a query."""
    # Create the service
    service = TopicSearchService(db_session)

    # Search for programming-related topics
    results = service.search_topics(test_user.id, "programming", limit=5)

    # Verify results
    assert len(results) > 0
    # Check that each result is a tuple of (Topic, score)
    for result in results:
        assert isinstance(result[0], Topic)
        assert isinstance(result[1], float)

    # Format the results
    formatted = service.format_topic_search_results(results)

    # Verify formatted results
    assert len(formatted) > 0
    for item in formatted:
        assert "id" in item
        assert "name" in item
        assert "relevance_score" in item
        assert isinstance(item["relevance_score"], float)

def test_get_messages_by_topic(db_session, test_user, test_messages):
    """Test retrieving messages for a specific topic."""
    # Create the service
    service = TopicSearchService(db_session)

    # Get all topics for the user
    topics = service.get_user_topics(test_user.id)
    assert len(topics) > 0

    # Get messages for the first topic
    messages = service.get_messages_by_topic(test_user.id, topics[0].id, limit=10)

    # Verify results
    assert len(messages) > 0
    for message in messages:
        assert isinstance(message, Message)

    # Format the messages
    formatted = service.format_topic_messages(messages)

    # Verify formatted results
    assert len(formatted) > 0
    for item in formatted:
        assert "id" in item
        assert "content" in item
        assert "timestamp" in item
        assert "conversation_id" in item

def test_get_user_topics(db_session, test_user, test_messages):
    """Test retrieving all topics for a user."""
    # Create the service
    service = TopicSearchService(db_session)

    # Get all topics for the user
    topics = service.get_user_topics(test_user.id)

    # Verify results
    assert len(topics) > 0
    for topic in topics:
        assert isinstance(topic, Topic)
        assert topic.name is not None
