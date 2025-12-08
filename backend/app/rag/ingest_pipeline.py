# backend/app/rag/ingest_pipeline.py

from .loader import load_all_pdfs
from .splitter import split_text
from .vectorstore import add_to_chroma, clear_collection

def ingest_documents():
    print("📥 Starting ingestion pipeline...")
    
    # Clear existing collection to prevent duplicates
    clear_collection()

    docs = load_all_pdfs()
    if not docs:
        return {"status": "no documents found"}

    all_chunks = []
    all_metadata = []

    for doc in docs:
        chunks = split_text(doc["content"])
        for chunk in chunks:
            all_chunks.append(chunk)
            # Add metadata
            meta = {
                "source": doc["source"],
                "page": doc["page"]
            }
            all_metadata.append(meta)

    if not all_chunks:
        return {"status": "no chunks generated"}

    add_to_chroma(all_chunks, all_metadata)
    
    return {
        "status": "success", 
        "documents_processed": len(docs),
        "chunks_created": len(all_chunks)
    }
