from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.models import Base

class Topic(Base):
    __tablename__ = "topics"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)

    message_topics = relationship("MessageTopic", back_populates="topic")

from sqlalchemy import ForeignKey

class MessageTopic(Base):
    __tablename__ = "messagetopics"
    message_id = Column(Integer, ForeignKey("messages.id"), primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), primary_key=True, index=True)

    message = relationship("Message", back_populates="message_topics")
    topic = relationship("Topic", back_populates="message_topics")
