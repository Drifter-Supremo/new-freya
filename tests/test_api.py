"""
test_api.py - Tests for the API endpoints
"""

import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

# Import app once the path is correctly set
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.main import app
from app.models.userfact import UserFact

# Create a test client
client = TestClient(app)

# Sample test data
TEST_FACTS = [
    {"id": 1, "user_id": 1, "fact_type": "job", "value": "Software Engineer at Google"},
    {"id": 2, "user_id": 1, "fact_type": "location", "value": "San Francisco"},
    {"id": 3, "user_id": 1, "fact_type": "interests", "value": "playing guitar and hiking"},
    {"id": 4, "user_id": 1, "fact_type": "family", "value": "married to Sarah, two kids: Emma and Jake"},
    {"id": 5, "user_id": 1, "fact_type": "preferences", "value": "loves Italian food"},
    {"id": 6, "user_id": 1, "fact_type": "pets", "value": "has a dog named Max"},
]

@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    with patch("app.core.db.get_db") as mock_get_db:
        # Skip the yield and dependency logic for testing
        yield mock_get_db

@pytest.fixture
def mock_user_facts_all():
    """Mock the UserFactRepository.get_all method"""
    with patch("app.repository.userfact.UserFactRepository.get_all") as mock_get_all:
        # Create UserFact objects for the mock response
        mock_facts = []
        for fact_data in TEST_FACTS:
            mock_fact = UserFact(
                id=fact_data["id"],
                user_id=fact_data["user_id"],
                fact_type=fact_data["fact_type"],
                value=fact_data["value"]
            )
            mock_facts.append(mock_fact)
        
        mock_get_all.return_value = mock_facts
        yield mock_get_all

@pytest.fixture
def mock_facts_with_relevance():
    """Mock the MemoryQueryRepository.get_facts_with_relevance method"""
    with patch("app.repository.memory.MemoryQueryRepository.get_facts_with_relevance") as mock_relevance:
        # Create a list of (UserFact, score) tuples for the mock response
        mock_result = []
        for fact_data in TEST_FACTS:
            # Assign different scores based on fact type
            score = 0.0
            if fact_data["fact_type"] == "job" and "Google" in fact_data["value"]:
                score = 3.0
            elif fact_data["fact_type"] == "family" and "kids" in fact_data["value"]:
                score = 2.5
            elif fact_data["fact_type"] == "location" and "San Francisco" in fact_data["value"]:
                score = 2.0
            elif fact_data["fact_type"] == "preferences" and "Italian" in fact_data["value"]:
                score = 1.8
            
            if score > 0:
                mock_fact = UserFact(
                    id=fact_data["id"],
                    user_id=fact_data["user_id"],
                    fact_type=fact_data["fact_type"],
                    value=fact_data["value"]
                )
                mock_result.append((mock_fact, score))
        
        # Sort by score
        mock_result.sort(key=lambda x: x[1], reverse=True)
        mock_relevance.return_value = mock_result
        yield mock_relevance

def test_get_user_facts(mock_db_session, mock_user_facts_all):
    """Test the /user-facts/{user_id} endpoint"""
    # Make a request to the endpoint
    response = client.get("/user-facts/1")
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == len([f for f in TEST_FACTS if f["user_id"] == 1])
    
    # Check that the response contains the expected facts
    for fact in data:
        assert "id" in fact
        assert "fact_type" in fact
        assert "value" in fact

def test_get_relevant_facts(mock_db_session, mock_facts_with_relevance):
    """Test the /user-facts/{user_id}/relevant endpoint"""
    # Make a request to the endpoint
    response = client.get("/user-facts/1/relevant?query=job+at+Google")
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # The first item should be the job fact with Google
    if data:
        assert data[0]["fact_type"] == "job"
        assert "Google" in data[0]["value"]
        assert "relevance_score" in data[0]
        assert data[0]["relevance_score"] > 0

    # Same test but with family query
    response = client.get("/user-facts/1/relevant?query=who+are+your+kids")
    assert response.status_code == 200
    data = response.json()
    
    # The first item should be the family fact with kids
    if data and len(data) > 0:
        assert data[0]["fact_type"] == "family"
        assert "kids" in data[0]["value"] or "Emma" in data[0]["value"]
        assert "relevance_score" in data[0]
        assert data[0]["relevance_score"] > 0

    # Test with combined query
    response = client.get("/user-facts/1/relevant?query=do+you+live+in+San+Francisco+and+like+Italian+food")
    assert response.status_code == 200
    data = response.json()
    
    # Should have both location and preferences facts
    if data and len(data) >= 2:
        fact_types = [f["fact_type"] for f in data[:2]]
        assert "location" in fact_types
        assert "preferences" in fact_types
