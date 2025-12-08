# backend/app/models/user.py

"""User model for authentication.
Uses SQLModel which integrates with SQLAlchemy.
"""

from sqlmodel import SQLModel, Field
from typing import Optional

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    created_at: Optional[str] = Field(default_factory=lambda: "now()")
