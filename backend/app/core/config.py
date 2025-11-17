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
    CHUNK_SIZE: int = 450
    CHUNK_OVERLAP: int = 50


settings = Settings()
