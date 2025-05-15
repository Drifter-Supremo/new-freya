"""
user_fact_service.py - Service for extracting and storing user facts.
"""

from typing import List
from sqlalchemy.orm import Session
from utils.fact_patterns import USER_FACT_PATTERNS
from app.repository.userfact import UserFactRepository
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
