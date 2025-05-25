import aiosqlite
import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer
import os
from api.schemas import UserRegister, UserLogin, AuthResponse

security = HTTPBearer()

class AuthService:
    def __init__(self):
        self.db_path = "users.db"
        self.secret_key = os.getenv("JWT_SECRET_KEY")
        self.algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.access_token_expire_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    async def initialize(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.commit()
    
    def _hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def _create_access_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    async def register(self, user_data: UserRegister) -> AuthResponse:
        async with aiosqlite.connect(self.db_path) as db:
            # Check if user exists
            async with db.execute("SELECT id FROM users WHERE username = ? OR email = ?", 
                                (user_data.username, user_data.email)) as cursor:
                if await cursor.fetchone():
                    raise HTTPException(status_code=400, detail="User already exists")
            
            # Create user
            password_hash = self._hash_password(user_data.password)
            async with db.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (user_data.username, user_data.email, password_hash)
            ) as cursor:
                user_id = cursor.lastrowid
            await db.commit()
            
            # Create token
            access_token = self._create_access_token({"sub": str(user_id), "username": user_data.username})
            
            return AuthResponse(
                access_token=access_token,
                token_type="bearer",
                username=user_data.username
            )
    
    async def login(self, user_data: UserLogin) -> AuthResponse:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT id, username, password_hash FROM users WHERE username = ?",
                (user_data.username,)
            ) as cursor:
                user = await cursor.fetchone()
                
            if not user or not self._verify_password(user_data.password, user[2]):
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            access_token = self._create_access_token({"sub": str(user[0]), "username": user[1]})
            
            return AuthResponse(
                access_token=access_token,
                token_type="bearer",
                username=user[1]
            )
    
    async def get_current_user(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: str = payload.get("sub")
            username: str = payload.get("username")
            if user_id is None:
                raise HTTPException(status_code=401, detail="Invalid token")
            return {"user_id": int(user_id), "username": username}
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(token: str = Depends(security)) -> dict:
    auth_service = AuthService()
    return await auth_service.get_current_user(token.credentials)
