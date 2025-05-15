"""
user_fact_service.py - Service for extracting and storing user facts.
"""

from typing import List, Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session
from utils.fact_patterns import USER_FACT_PATTERNS
from app.repository.userfact import UserFactRepository
from app.repository.memory import MemoryQueryRepository
from app.models.userfact import UserFact


def extract_and_store_user_facts(db: Session, user_id: int, message: str) -> List[UserFact]:
    """
    Extract user facts from a message and store new facts in the database.
    Returns list of stored UserFact objects.
    """
    repo = UserFactRepository(db)
    # Load existing facts for this user to avoid duplicates
    existing = { (fact.fact_type, fact.value) for fact in db.query(UserFact).filter(UserFact.user_id == user_id).all() }
    stored_facts: List[UserFact] = []

    for category, patterns in USER_FACT_PATTERNS.items():
        for pattern in patterns:
            for match in pattern.finditer(message):
                if not match:
                    continue
                # Determine captured values
                if match.lastindex and match.lastindex > 1:
                    values = match.groups()
                else:
                    values = (match.group(1),)
                for v in values:
                    # Clean and trim conjunctions (e.g. 'and') to capture single facts
                    v_clean = v.strip()
                    if ' and ' in v_clean:
                        v_clean = v_clean.split(' and ')[0].strip()
                    key = (category, v_clean)
                    if key in existing:
                        continue
                    obj = repo.create({"user_id": user_id, "fact_type": category, "value": v_clean})
                    stored_facts.append(obj)
                    existing.add(key)
    return stored_facts


def get_relevant_facts_for_context(db: Session, user_id: int, query: str, limit: int = 5) -> List[Tuple[UserFact, float]]:
    """
    Retrieve facts that are relevant to the given context/query for assembling memory context.
    
    Args:
        db: Database session
        user_id: User ID to retrieve facts for
        query: User query or context to match against
        limit: Maximum number of facts to return
        
    Returns:
        List of (UserFact, relevance_score) tuples, sorted by relevance
    """
    memory_repo = MemoryQueryRepository(db)
    return memory_repo.get_facts_with_relevance(user_id, query, limit)


def format_facts_for_context(facts_with_scores: List[Tuple[UserFact, float]]) -> List[Dict[str, Any]]:
    """
    Format user facts with their relevance scores for inclusion in the memory context.
    
    Args:
        facts_with_scores: List of (UserFact, score) tuples from get_relevant_facts_for_context
        
    Returns:
        List of formatted fact dictionaries with type, value, and confidence
    """
    if not facts_with_scores:
        return []
    
    # Normalize scores to 0-100 confidence range
    max_score = max(score for _, score in facts_with_scores)
    
    formatted_facts = []
    for fact, score in facts_with_scores:
        # Calculate a confidence score (0-100)
        confidence = min(100, int((score / max_score) * 100)) if max_score > 0 else 0
        
        formatted_facts.append({
            "type": fact.fact_type,
            "value": fact.value,
            "confidence": confidence
        })
    
    return formatted_facts
