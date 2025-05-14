from contextlib import contextmanager
from sqlalchemy.orm import Session

@contextmanager
def transactional_session(db: Session):
    """
    Context manager for SQLAlchemy transaction management.
    Commits if no exception, rollbacks on exception.
    Usage:
        with transactional_session(db):
            ... # do work
    """
    try:
        yield
        db.commit()
    except Exception:
        db.rollback()
        raise
