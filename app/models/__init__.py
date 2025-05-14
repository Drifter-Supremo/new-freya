from sqlalchemy.orm import declarative_base

Base = declarative_base()

from .user import User
from .conversation import Conversation
from .message import Message
from .userfact import UserFact
from .topic import Topic, MessageTopic
