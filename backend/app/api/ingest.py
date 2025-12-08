from fastapi import APIRouter
from ..rag.ingest_pipeline import ingest_documents

router = APIRouter()

@router.post("/ingest", status_code=200)
def ingest():
    """Runs the ingestion pipeline:
    PDF -> text -> chunks -> embeddings -> ChromaDB.
    """
    result = ingest_documents()
    return result
