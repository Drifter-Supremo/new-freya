"""
test_manual_relevance.py - Manual testing of fact relevance scoring

This script provides a direct way to test the relevance scoring functionality
without running a full pytest suite. It creates dummy data and directly
calls the repository methods to verify scoring works correctly.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.models.userfact import UserFact
from app.repository.memory import MemoryQueryRepository

# Create dummy facts
facts = [
    UserFact(id=1, user_id=1, fact_type="job", value="Software Engineer at Google"),
    UserFact(id=2, user_id=1, fact_type="location", value="San Francisco"),
    UserFact(id=3, user_id=1, fact_type="interests", value="playing guitar and hiking"),
    UserFact(id=4, user_id=1, fact_type="family", value="married to Sarah, two kids: Emma and Jake"),
    UserFact(id=5, user_id=1, fact_type="preferences", value="loves Italian food"),
    UserFact(id=6, user_id=1, fact_type="pets", value="has a dog named Max"),
]

# Mock DB session
class MockSession:
    def query(self, model):
        return self
    
    def filter(self, condition):
        return self
    
    def all(self):
        return facts

# Create repository with mock session
memory_repo = MemoryQueryRepository(MockSession())

def test_job_query():
    print("\n=== Testing job query ===")
    results = memory_repo.get_facts_with_relevance(1, "Tell me about your job at Google")
    
    print("Results for 'Tell me about your job at Google':")
    for fact, score in results:
        print(f"{fact.fact_type}: '{fact.value}' - Score: {score:.3f}")
    
    # Verify the top result is the job fact
    if results:
        top_fact, top_score = results[0]
        assert top_fact.fact_type == "job", f"Expected 'job' fact to be most relevant, got '{top_fact.fact_type}'"
        assert "Google" in top_fact.value, "Expected 'Google' to be in the top fact value"
        print("PASS: Job query test passed")

def test_family_query():
    print("\n=== Testing family query ===")
    results = memory_repo.get_facts_with_relevance(1, "who are your kids")
    
    print("Results for 'who are your kids':")
    for fact, score in results:
        print(f"{fact.fact_type}: '{fact.value}' - Score: {score:.3f}")
    
    # Verify the top result is the family fact
    if results:
        top_fact, top_score = results[0]
        assert top_fact.fact_type == "family", f"Expected 'family' fact to be most relevant, got '{top_fact.fact_type}'"
        assert "kids" in top_fact.value or "Emma" in top_fact.value, "Expected kids to be mentioned in the top fact value"
        print("PASS: Family query test passed")

def test_combined_query():
    print("\n=== Testing combined query ===")
    results = memory_repo.get_facts_with_relevance(1, "do you live in San Francisco and like Italian food")
    
    print("Results for 'do you live in San Francisco and like Italian food':")
    for fact, score in results:
        print(f"{fact.fact_type}: '{fact.value}' - Score: {score:.3f}")
    
    # Both location and preferences facts should have high scores
    fact_types = [fact.fact_type for fact, _ in results[:2]]
    assert "location" in fact_types, "Expected 'location' fact to be in top results"
    assert "preferences" in fact_types, "Expected 'preferences' fact to be in top results"
    print("PASS: Combined query test passed")

if __name__ == "__main__":
    # Run all tests
    try:
        test_job_query()
        test_family_query() 
        test_combined_query()
        print("\nAll tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
