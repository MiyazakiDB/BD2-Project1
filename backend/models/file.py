from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4

class FileBase(BaseModel):
    filename: str
    mime_type: str
    size: int

class FileCreate(FileBase):
    owner_id: UUID
    path: str

class FileInDB(FileCreate):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        orm_mode = True

class File(FileBase):
    id: UUID
    owner_id: UUID
    created_at: datetime

class FileList(BaseModel):
    files: list[File]
