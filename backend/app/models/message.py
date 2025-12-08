# backend/app/models/message.py

"""Chat message model linking a session to a user/assistant message."""

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional

class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="chatsession.id")
    role: str = Field(index=True)  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = Field(default_factory=lambda: "now()")
    # Relationship back to session
    session: "ChatSession" = Relationship(back_populates="messages")
