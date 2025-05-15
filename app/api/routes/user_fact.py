"""
user_fact.py - API endpoints for retrieving user facts
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.db import get_db
from app.repository.userfact import UserFactRepository
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
