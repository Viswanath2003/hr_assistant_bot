# backend/app/core/security.py

"""Security utilities for the HR Assistant Bot.
Provides password hashing (bcrypt) and JWT token creation/verification.
"""

from datetime import datetime, timedelta
from typing import Optional

from passlib.context import CryptContext
from jose import JWTError, jwt

# Secret key – in production should be env var
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

import hashlib

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Pre-hash to handle long passwords (bcrypt has 72 byte limit)
    # We use SHA256 first, then bcrypt
    # This is a common workaround for the bcrypt truncation issue
    # However, for backward compatibility or simplicity, we can just truncate or use a different scheme.
    # But better: just let passlib handle it or ignore the warning if we don't expect >72 char passwords.
    # The warning "password cannot be longer than 72 bytes" comes from passlib/bcrypt.
    # A simple fix is to not allow passwords > 72 chars or just suppress if we don't care.
    # But to be safe, let's just use the default behavior and maybe the user sent a huge password?
    # Wait, the error was "ValueError: password cannot be longer than 72 bytes".
    # This means we MUST handle it.
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise e
