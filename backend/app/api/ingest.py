from fastapi import APIRouter
from app.rag.ingest_pipeline import ingest_documents

router = APIRouter()

@router.post("/ingest")
def ingest():
    """
    Runs the ingestion pipeline:
    PDF → text → chunks → embeddings → ChromaDB.
    """
    result = ingest_documents()
    return result
