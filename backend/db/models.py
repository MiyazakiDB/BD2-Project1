from sqlalchemy import Column, String, DateTime, func, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid

from backend.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="user")
    created_at = Column(DateTime, default=func.now())

class File(Base):
    __tablename__ = "files"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String, ForeignKey("users.id"), index=True)
    filename = Column(String)
    path = Column(String)
    size = Column(Integer)
    mime_type = Column(String)
    created_at = Column(DateTime, default=func.now())
