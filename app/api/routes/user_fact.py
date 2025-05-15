"""
user_fact.py - API endpoints for retrieving user facts
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.core.db import get_db
from app.repository.userfact import UserFactRepository
from app.repository.memory import MemoryQueryRepository
from app.models.userfact import UserFact

router = APIRouter(prefix="/user-facts", tags=["user-facts"])

@router.get("/{user_id}", response_model=List[dict])
def get_user_facts(user_id: int, db: Session = Depends(get_db)):
    repo = UserFactRepository(db)
    facts = repo.get_all()
    # Filter by user_id
    user_facts = [f for f in facts if f.user_id == user_id]
    return [
        {"id": f.id, "fact_type": f.fact_type, "value": f.value}
        for f in user_facts
    ]

@router.get("/{user_id}/relevant", response_model=List[Dict[str, Any]])
def get_relevant_facts(
    user_id: int, 
    query: str = Query(..., description="Search query for relevance scoring"),
    limit: int = Query(10, description="Maximum number of facts to return"),
    db: Session = Depends(get_db)
):
    """
    Retrieve user facts with relevance scoring based on a search query.
    
    Facts are scored based on:
    - Text similarity between the query and fact value
    - Fact type priority (job, family, etc.)
    - Returns facts sorted by relevance (highest first)
    """
    memory_repo = MemoryQueryRepository(db)
    relevant_facts = memory_repo.get_facts_with_relevance(user_id, query, limit)
    
    if not relevant_facts:
        return []
    
    return [
        {
            "id": fact.id,
            "fact_type": fact.fact_type,
            "value": fact.value,
            "relevance_score": round(score, 3)
        }
        for fact, score in relevant_facts
    ]
