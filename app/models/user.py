from sqlalchemy import Column, Integer, String
from app.models import Base

from sqlalchemy.orm import relationship
from .message import Message

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)

    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    userfacts = relationship("UserFact", back_populates="user", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")
