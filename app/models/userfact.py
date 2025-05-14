from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship
from app.models import Base

class UserFact(Base):
    __tablename__ = "userfacts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    fact_type = Column(String(50), nullable=False)
    value = Column(String, nullable=False)

    user = relationship("User", back_populates="userfacts")
