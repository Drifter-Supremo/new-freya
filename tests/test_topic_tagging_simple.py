"""Tests for the topic tagging service using PostgreSQL."""
import pytest
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import TSVECTOR
from datetime import datetime, timezone
import os

# Use the same models as in production
from app.models import Base
from app.models.message import Message
from app.models.topic import Topic, MessageTopic
from app.models.conversation import Conversation

# Get database URL from environment variable
DB_URL = os.getenv("POSTGRES_URL").replace('postgresql+psycopg2://', 'postgresql://')

# Create engine and session factory
engine = create_engine(DB_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables
Base.metadata.create_all(bind=engine)

# Import service after setting up models
from app.services.topic_tagging import TopicTaggingService
from tests.mocks.topic_extractor import MockTopicExtractor

@pytest.fixture(scope="function")
def db_session():
    """Create a clean database session for each test."""
    # Start a transaction
    connection = engine.connect()
    transaction = connection.begin()
    
    # Create a new session
    db = TestingSessionLocal(bind=connection)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Clean up any existing data
    db.query(MessageTopic).delete()
    db.query(Message).delete()
    db.query(Topic).delete()
    db.query(Conversation).delete()
    db.query(User).delete()
    db.commit()
    
    try:
        yield db
    finally:
        # Clean up by rolling back the transaction
        db.close()
        transaction.rollback()
        connection.close()

@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    from app.models.user import User
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password"
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def topic_tagging_service(db_session):
    """Create a TopicTaggingService instance for testing with a mock topic extractor."""
    service = TopicTaggingService(db_session)
    service.topic_extractor = MockTopicExtractor()
    return service

def test_tag_message_simple(topic_tagging_service, db_session, test_user):
    """Test that a message is correctly tagged with topics."""
    # Create a conversation first
    conversation = Conversation(user_id=test_user.id)
    db_session.add(conversation)
    db_session.commit()
    
    # Create a test message
    message = Message(
        content="I love programming in Python and JavaScript!",
        conversation_id=conversation.id,
        user_id=test_user.id
    )
    db_session.add(message)
    db_session.commit()
    
    # Tag the message
    topics = topic_tagging_service.tag_message(message, top_n=2)
    
    # Verify topics were returned
    assert len(topics) > 0
    assert any(topic.name.lower() in ["programming", "python", "javascript"] for topic in topics)
    
    # Verify topics were associated with the message
    message_topics = topic_tagging_service.get_message_topics(message.id)
    assert len(message_topics) == len(topics)
    assert {t.id for t in topics} == {t.id for t in message_topics}

def test_existing_topic_reuse(topic_tagging_service, db_session, test_user):
    """Test that existing topics are reused."""
    # Create a conversation first
    conversation = Conversation(user_id=test_user.id)
    db_session.add(conversation)
    db_session.commit()
    
    # Create a topic that should match
    programming_topic = Topic(name="programming")
    db_session.add(programming_topic)
    db_session.commit()
    
    # Create a test message
    message = Message(
        content="I love programming in Python!",
        conversation_id=conversation.id,
        user_id=test_user.id
    )
    db_session.add(message)
    db_session.commit()
    
    # Tag the message
    topics = topic_tagging_service.tag_message(message)
    
    # Verify the existing topic was used
    assert any(t.id == programming_topic.id for t in topics)
    assert any(t.name == "programming" for t in topics)
