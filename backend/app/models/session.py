# backend/app/models/session.py

"""Chat session model linking a user to a series of messages."""

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List

class ChatSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    created_at: Optional[str] = Field(default_factory=lambda: "now()")
    last_active: Optional[str] = Field(default_factory=lambda: "now()")
    # Relationship to messages (not required for DB schema but useful)
    messages: List["ChatMessage"] = Relationship(back_populates="session")
