import os
import sys
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import after setting up path
from app.models import Base
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.topic import Topic, MessageTopic

# Use the development database
DB_URL = os.getenv("POSTGRES_URL").replace('postgresql+psycopg2://', 'postgresql://')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=create_engine(DB_URL))

@pytest.fixture(scope="session")
def engine():
    """Create a database engine for testing."""
    engine = create_engine(DB_URL)
    # Create all tables if they don't exist
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture
def db_session(engine):
    """Create a database session for testing."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def topic_tagging_service(db_session):
    """Create a TopicTaggingService instance for testing."""
    from app.services.topic_tagging import TopicTaggingService
    return TopicTaggingService(db_session)

@pytest.fixture
def test_user(db_session: Session):
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashedpassword"
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def test_conversation(db_session: Session, test_user):
    """Create a test conversation."""
    conv = Conversation(user_id=test_user.id)
    db_session.add(conv)
    db_session.commit()
    return conv

@pytest.fixture
def test_message(db_session: Session, test_user, test_conversation):
    """Create a test message."""
    msg = Message(
        content="I love programming in Python and JavaScript!",
        user_id=test_user.id,
        conversation_id=test_conversation.id
    )
    db_session.add(msg)
    db_session.commit()
    return msg

@pytest.fixture
def topic_tagging_service(db_session: Session):
    """Create a TopicTaggingService instance for testing."""
    from app.services.topic_tagging import TopicTaggingService
    return TopicTaggingService(db_session)
