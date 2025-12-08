# backend/app/core/database.py

"""Database connection and session handling.
Uses SQLModel (SQLAlchemy) with SQLite for development.
"""

from sqlmodel import SQLModel, create_engine, Session
from pathlib import Path
import os

# Base directory from settings
from .config import settings

# Database URL – use SQLite file in data directory
DB_PATH = settings.BASE_DIR / "data" / "hr_bot.db"
DB_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DB_URL, echo=False)

def init_db():
    """Create tables if they don't exist."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Provide a new DB session. Caller should close it when done."""
    with Session(engine) as session:
        yield session
