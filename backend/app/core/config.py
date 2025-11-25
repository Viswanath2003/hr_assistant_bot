import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

class Settings:
    # Google API Key
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")

    # Model names (Google Gemini)
    GOOGLE_LLM_MODEL: str = "models/gemini-2.5-flash-lite"
    GOOGLE_EMBEDDING_MODEL: str = "models/gemini-embedding-001"

    # Directory paths
    BASE_DIR = Path(__file__).resolve().parents[3]
    DATA_DIR = BASE_DIR / "data"

    RAW_DOCS_DIR = DATA_DIR / "raw_docs"
    PROCESSED_DIR = DATA_DIR / "processed"
    CHROMA_DIR = DATA_DIR / "chroma"

    # Chunking parameters
    CHUNK_SIZE: int = 1000  # Increased from 450 to preserve table structure
    CHUNK_OVERLAP: int = 150  # Increased from 50 for better context preservation


settings = Settings()
