"""
test_fact_relevance.py - Tests for fact relevance scoring functionality
"""

import sys
from pathlib import Path
import pytest
from sqlalchemy.orm import Session

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.repository.memory import MemoryQueryRepository
from app.models.userfact import UserFact
from app.models.user import User

# Sample test data
TEST_USER = {"id": 1, "name": "Test User"}
TEST_FACTS = [
    {"id": 1, "user_id": 1, "fact_type": "job", "value": "Software Engineer at Google"},
    {"id": 2, "user_id": 1, "fact_type": "location", "value": "San Francisco"},
    {"id": 3, "user_id": 1, "fact_type": "interests", "value": "playing guitar and hiking"},
    {"id": 4, "user_id": 1, "fact_type": "family", "value": "married to Sarah, two kids: Emma and Jake"},
    {"id": 5, "user_id": 1, "fact_type": "preferences", "value": "loves Italian food"},
    {"id": 6, "user_id": 1, "fact_type": "pets", "value": "has a dog named Max"},
]

class TestFactRelevance:
    @pytest.fixture
    def db_session(self, mocker):
        """
        Create a mock DB session with pre-loaded test data.
        """
        mock_session = mocker.MagicMock(spec=Session)
        
        # Mock the query execution to return our test data
        facts = []
        for fact_data in TEST_FACTS:
            mock_fact = mocker.MagicMock(spec=UserFact)
            for k, v in fact_data.items():
                setattr(mock_fact, k, v)
            facts.append(mock_fact)
            
        # Set up the mocked query response
        mock_session.query.return_value.filter.return_value.all.return_value = facts
        
        return mock_session
    
    def test_fact_relevance_job_query(self, db_session):
        """Test relevance scoring for job-related query."""
        repo = MemoryQueryRepository(db_session)
        
        # Test with a job-related query
        results = repo.get_facts_with_relevance(1, "software engineering work Google")
        
        # Assertions
        assert len(results) > 0, "Should return at least one fact"
        
        # The job fact should be the most relevant
        top_fact, score = results[0]
        assert top_fact.fact_type == "job", f"Expected 'job' fact to be most relevant, got '{top_fact.fact_type}'"
        assert "Google" in top_fact.value, "Expected 'Google' to be in the top fact value"
        assert score > 0, "Score should be positive"
        
        # Print results for debugging
        print("\nResults for 'software engineering work Google':")
        for fact, score in results:
            print(f"{fact.fact_type}: '{fact.value}' - Score: {score:.3f}")
    
    def test_fact_relevance_family_query(self, db_session):
        """Test relevance scoring for family-related query."""
        repo = MemoryQueryRepository(db_session)
        
        # Test with a family-related query
        results = repo.get_facts_with_relevance(1, "who are your kids")
        
        # Assertions
        assert len(results) > 0, "Should return at least one fact"
        
        # The family fact should be the most relevant
        top_fact, score = results[0]
        assert top_fact.fact_type == "family", f"Expected 'family' fact to be most relevant, got '{top_fact.fact_type}'"
        assert "kids" in top_fact.value or "Emma" in top_fact.value, "Expected kids to be mentioned in the top fact value"
        assert score > 0, "Score should be positive"
        
        # Print results for debugging
        print("\nResults for 'who are your kids':")
        for fact, score in results:
            print(f"{fact.fact_type}: '{fact.value}' - Score: {score:.3f}")
    
    def test_fact_relevance_combined_query(self, db_session):
        """Test relevance scoring for query with multiple potential matches."""
        repo = MemoryQueryRepository(db_session)
        
        # Test with a combined query
        results = repo.get_facts_with_relevance(1, "do you live in San Francisco and like Italian food")
        
        # Assertions
        assert len(results) >= 2, "Should return at least two facts"
        
        # Both location and preferences facts should have high scores
        fact_types = [fact.fact_type for fact, _ in results[:2]]
        assert "location" in fact_types, "Expected 'location' fact to be in top results"
        assert "preferences" in fact_types, "Expected 'preferences' fact to be in top results"
        
        # Print results for debugging
        print("\nResults for 'do you live in San Francisco and like Italian food':")
        for fact, score in results:
            print(f"{fact.fact_type}: '{fact.value}' - Score: {score:.3f}")

if __name__ == "__main__":
    pytest.main(["-v", "test_fact_relevance.py"])
