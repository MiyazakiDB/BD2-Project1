from sqlalchemy.orm import Session
from uuid import UUID
import uuid

from backend.db.models import User as DBUser
from backend.models.user import UserCreate, User

class UserRepository:
    @staticmethod
    def create_user(db: Session, user_data: UserCreate, hashed_password: str) -> User:
        db_user = DBUser(
            id=str(uuid.uuid4()),
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            role="user"
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return User(
            id=UUID(db_user.id),
            username=db_user.username,
            email=db_user.email,
            role=db_user.role
        )
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> DBUser:
        return db.query(DBUser).filter(DBUser.email == email).first()
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> DBUser:
        return db.query(DBUser).filter(DBUser.id == user_id).first()
