"""Tests for the topic tagging service."""
import pytest
from sqlalchemy.orm import Session

from app.models.topic import Topic, MessageTopic
from app.models.message import Message
from app.models.conversation import Conversation
from app.models.user import User
from app.services.topic_tagging import TopicTaggingService

# Test data
test_messages = [
    "I love programming in Python and JavaScript!",
    "I enjoy hiking in the mountains and playing guitar in my free time.",
    "Working on a new web project using React and FastAPI. It's challenging but fun!"
]

@pytest.fixture(autouse=True)
def cleanup_db(db_session: Session):
    """Clean up test data before and after each test."""
    # Clean up before test
    db_session.query(MessageTopic).delete()
    db_session.query(Message).delete()
    db_session.query(Topic).delete()
    db_session.query(Conversation).delete()
    db_session.query(User).delete()
    db_session.commit()
    
    yield
    
    # Clean up after test
    db_session.query(MessageTopic).delete()
    db_session.query(Message).delete()
    db_session.query(Topic).delete()
    db_session.query(Conversation).delete()
    db_session.query(User).delete()
    db_session.commit()

@pytest.fixture
def test_user(db_session: Session, cleanup_db):
    """Create a test user."""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        username=f"testuser_{unique_id}",
        email=f"test_{unique_id}@example.com",
        hashed_password="hashed_test_password"  # This is just for testing
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def test_conversation(db_session: Session, test_user: User):
    """Create a test conversation."""
    conversation = Conversation(user_id=test_user.id)
    db_session.add(conversation)
    db_session.commit()
    return conversation

@pytest.fixture
def test_message(db_session: Session, test_user: User, test_conversation: Conversation):
    """Create a test message."""
    message = Message(
        content=test_messages[0],
        user_id=test_user.id,
        conversation_id=test_conversation.id
    )
    db_session.add(message)
    db_session.commit()
    return message

def test_tag_message(topic_tagging_service, test_message, cleanup_db):
    """Test that a message is correctly tagged with topics."""
    # Tag the message
    topics = topic_tagging_service.tag_message(test_message, top_n=2)
    
    # Verify topics were returned
    assert len(topics) > 0
    assert any(topic.name.lower() in ["programming", "python", "javascript"] for topic in topics)
    
    # Verify topics were associated with the message
    message_topics = topic_tagging_service.get_message_topics(test_message.id)
    assert len(message_topics) == len(topics)
    assert {t.id for t in topics} == {t.id for t in message_topics}

def test_tag_message_existing_topic(topic_tagging_service, test_message, db_session, cleanup_db):
    """Test that existing topics are reused."""
    # Create a topic that should match
    programming_topic = Topic(name="programming")
    db_session.add(programming_topic)
    db_session.flush()  # Flush to get the ID but don't commit yet
    
    # Tag the message
    topics = topic_tagging_service.tag_message(test_message)
    
    # Verify the existing topic was used
    assert any(t.id == programming_topic.id for t in topics)
    assert any(t.name == "programming" for t in topics)

def test_tag_messages_batch(topic_tagging_service, db_session, test_conversation, test_user, cleanup_db):
    """Test tagging multiple messages in a batch."""
    # Create test messages
    messages = [
        Message(
            content=msg,
            user_id=test_user.id,
            conversation_id=test_conversation.id
        )
        for msg in test_messages
    ]
    db_session.add_all(messages)
    db_session.flush()  # Flush to get IDs but don't commit yet
    
    # Tag all messages
    results = topic_tagging_service.tag_messages(messages)
    
    # Verify all messages were tagged
    assert len(results) == len(messages)
    for msg in messages:
        assert msg.id in results
        assert len(results[msg.id]) > 0

def test_get_topic_messages(topic_tagging_service, test_message, db_session):
    """Test retrieving messages by topic."""
    # Tag the message
    topics = topic_tagging_service.tag_message(test_message)
    assert len(topics) > 0
    
    # Get messages for the first topic
    topic_id = topics[0].id
    messages = topic_tagging_service.get_topic_messages(topic_id)
    
    # Verify the message is in the results
    assert any(msg.id == test_message.id for msg in messages)

def test_case_insensitive_topic_matching(topic_tagging_service, test_message, db_session):
    """Test that topic matching is case insensitive."""
    # Create a topic with different case
    programming_topic = Topic(name="PROGRAMMING")
    db_session.add(programming_topic)
    db_session.commit()
    
    # Tag the message
    topics = topic_tagging_service.tag_message(test_message)
    
    # Verify the existing topic was used (case insensitive match)
    assert any(t.name.lower() == "programming" for t in topics)
    assert any(t.id == programming_topic.id for t in topics)
