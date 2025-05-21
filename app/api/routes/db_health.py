import os
from fastapi import APIRouter, status
from sqlalchemy import text
from app.core.db import engine, USING_FIREBASE

# Try to import Firebase
try:
    import firebase_admin
    from firebase_admin import firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

router = APIRouter()

@router.get("/db-health", status_code=status.HTTP_200_OK)
def db_health_check():
    # Firebase mode
    if USING_FIREBASE:
        if not FIREBASE_AVAILABLE:
            return {
                "status": "warning", 
                "detail": "Firebase mode enabled, but Firebase Admin SDK not installed. Run: pip install firebase-admin"
            }
        
        try:
            # Check Firebase connection
            db = firestore.client()
            # Try to list collections (doesn't matter if there are any)
            collections = db.collections()
            collection_list = [c.id for c in collections]
            return {
                "status": "ok", 
                "detail": f"Firebase connection successful. Found {len(collection_list)} collections.",
                "mode": "firebase"
            }
        except Exception as e:
            return {"status": "error", "detail": f"Firebase connection error: {str(e)}", "mode": "firebase"}
    
    # PostgreSQL mode
    else:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return {"status": "ok", "detail": "PostgreSQL connection successful", "mode": "postgresql"}
        except Exception as e:
            return {"status": "error", "detail": f"PostgreSQL error: {str(e)}", "mode": "postgresql"}
