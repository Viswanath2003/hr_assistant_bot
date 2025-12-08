# backend/app/models/__init__.py

"""Expose model classes for import side effects.
Ensures SQLModel metadata includes all tables when init_db() is called.
"""

from .user import User
from .session import ChatSession
from .message import ChatMessage
