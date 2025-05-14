from app.models.message import Message
from app.repository.base import BaseRepository

class MessageRepository(BaseRepository[Message]):
    def __init__(self, db):
        super().__init__(db, Message)
