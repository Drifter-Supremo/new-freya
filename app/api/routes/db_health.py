from fastapi import APIRouter, status
from sqlalchemy import text
from app.core.db import engine

router = APIRouter()

@router.get("/db-health", status_code=status.HTTP_200_OK)
def db_health_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "detail": "Database connection successful"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
