"""
Test for user fact retrieval functionality
"""
import pytest
import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base
from app.models.user import User
from app.models.userfact import UserFact
from app.repository.userfact import UserFactRepository

@pytest.fixture
def db_session():
    # Create an in-memory SQLite database
    engine = create_engine('sqlite:///:memory:')
    # Create only the tables we need for this test
    Base.metadata.create_all(bind=engine, tables=[User.__table__, UserFact.__table__])
    
    # Create a session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Add test data
    user = User(id=1, username="test_user", email="test@example.com", hashed_password="password_hash")
    session.add(user)
    
    # Add some user facts
    facts = [
        UserFact(user_id=1, fact_type="location", value="Paris"),
        UserFact(user_id=1, fact_type="job", value="Engineer"),
        UserFact(user_id=1, fact_type="hobby", value="Reading"),
        # Add a fact for a different user to test filtering
        UserFact(user_id=2, fact_type="location", value="London")
    ]
    session.add_all(facts)
    session.commit()
    
    yield session
    
    # Clean up
    session.close()

def test_get_user_facts_by_user_id(db_session):
    # Create a repository with our test session
    repo = UserFactRepository(db_session)
    
    # Get all facts first
    all_facts = repo.get_all()
    assert len(all_facts) == 4  # We added 4 facts total
    
    # Filter manually by user_id=1 (what the API endpoint would do)
    user_facts = [f for f in all_facts if f.user_id == 1]
    assert len(user_facts) == 3  # 3 facts for user_id=1
    
    # Verify the facts have the expected values
    fact_types = [f.fact_type for f in user_facts]
    fact_values = [f.value for f in user_facts]
    
    assert "location" in fact_types
    assert "job" in fact_types
    assert "hobby" in fact_types
    
    assert "Paris" in fact_values
    assert "Engineer" in fact_values
    assert "Reading" in fact_values
    
    # Verify no facts for other users are included
    assert all(f.user_id == 1 for f in user_facts)
    assert "London" not in fact_values
