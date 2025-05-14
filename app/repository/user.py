from app.models.user import User
from app.repository.base import BaseRepository

class UserRepository(BaseRepository[User]):
    def __init__(self, db):
        super().__init__(db, User)
