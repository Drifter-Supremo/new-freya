from app.models.conversation import Conversation
from app.repository.base import BaseRepository

class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self, db):
        super().__init__(db, Conversation)
