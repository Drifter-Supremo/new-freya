from app.models.userfact import UserFact
from app.repository.base import BaseRepository

class UserFactRepository(BaseRepository[UserFact]):
    def __init__(self, db):
        super().__init__(db, UserFact)
