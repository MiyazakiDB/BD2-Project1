from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from uuid import UUID, uuid4

from backend.models.user import User, UserCreate, Token, TokenPayload
from backend.core.auth.jwt import get_password_hash, verify_password, create_tokens, get_current_user, oauth2_scheme
from backend.settings import SECRET_KEY, ALGORITHM

router = APIRouter()

# In-memory user store (replace with database in production)
users_db = {}

@router.post("/register", response_model=User)
async def register_user(user_data: UserCreate):
    if user_data.email in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user with hashed password
    user_id = uuid4()
    hashed_password = get_password_hash(user_data.password)
    
    # Store the user in our "database"
    users_db[user_data.email] = {
        "id": user_id,
        "username": user_data.username,
        "email": user_data.email,
        "hashed_password": hashed_password,
        "role": "user"
    }
    
    # Return the user without the password
    return User(
        id=user_id,
        username=user_data.username,
        email=user_data.email,
        role="user"
    )

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Check if user exists
    user = users_db.get(form_data.username)  # Using username field for email
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token, refresh_token = create_tokens(user["id"], user["role"])
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token
    )

@router.post("/refresh", response_model=Token)
async def refresh_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)
        
        # Check if it's a refresh token
        if token_data.type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create new tokens
        access_token, refresh_token = create_tokens(UUID(token_data.sub), token_data.role)
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
