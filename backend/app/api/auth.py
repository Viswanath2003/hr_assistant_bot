# backend/app/api/auth.py

"""Authentication routes for the HR Assistant Bot.
Provides:
- POST /register  (email, password)
- POST /login     (email, password) -> returns access & refresh tokens
- POST /refresh   (refresh token) -> new access token
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr

from ..core.security import get_password_hash, verify_password, create_access_token, create_refresh_token, decode_token
from ..core.database import get_session
from ..models.user import User

router = APIRouter()

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest, db = Depends(get_session)):
    from sqlmodel import select
    # Check if user exists
    statement = select(User).where(User.email == req.email)
    existing = db.exec(statement).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = get_password_hash(req.password)
    user = User(email=req.email, hashed_password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    access = create_access_token({"sub": str(user.id)})
    refresh = create_refresh_token({"sub": str(user.id)})
    return TokenResponse(access_token=access, refresh_token=refresh)

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db = Depends(get_session)):
    from sqlmodel import select
    statement = select(User).where(User.email == req.email)
    user = db.exec(statement).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access = create_access_token({"sub": str(user.id)})
    refresh = create_refresh_token({"sub": str(user.id)})
    return TokenResponse(access_token=access, refresh_token=refresh)

class RefreshRequest(BaseModel):
    refresh_token: str

@router.post("/refresh", response_model=TokenResponse)
def refresh(req: RefreshRequest):
    try:
        payload = decode_token(req.refresh_token)
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    access = create_access_token({"sub": user_id})
    refresh = create_refresh_token({"sub": user_id})
    return TokenResponse(access_token=access, refresh_token=refresh)
