from app.models.topic import Topic
from app.repository.base import BaseRepository

class TopicRepository(BaseRepository[Topic]):
    def __init__(self, db):
        super().__init__(db, Topic)
