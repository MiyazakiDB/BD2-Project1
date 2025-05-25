from sqlalchemy.orm import Session
from uuid import UUID
import uuid

from backend.db.models import User as DBUser, File as DBFile
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

class FileRepository:
    @staticmethod
    def create_file(db: Session, file_data):
        db_file = DBFile(
            id=str(file_data["id"]),
            owner_id=str(file_data["owner_id"]),
            filename=file_data["filename"],
            path=file_data["path"],
            size=file_data["size"],
            mime_type=file_data["mime_type"]
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        return db_file
    
    @staticmethod
    def get_files_by_owner(db: Session, owner_id: str):
        return db.query(DBFile).filter(DBFile.owner_id == str(owner_id)).all()
    
    @staticmethod
    def get_file_by_id(db: Session, file_id: str, owner_id: str):
        return db.query(DBFile).filter(DBFile.id == str(file_id), DBFile.owner_id == str(owner_id)).first()
    
    @staticmethod
    def delete_file(db: Session, file_id: str, owner_id: str):
        db_file = FileRepository.get_file_by_id(db, file_id, owner_id)
        if db_file:
            db.delete(db_file)
            db.commit()
            return True
        return False
