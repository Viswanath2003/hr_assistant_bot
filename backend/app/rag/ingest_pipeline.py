# backend/app/rag/ingest_pipeline.py

from app.rag.loader import load_all_pdfs
from app.rag.splitter import split_text
from app.rag.vectorstore import add_to_chroma, clear_collection

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
        filename = doc["filename"]
        pages = doc["pages"]   # list of (page_text, page_no)

        for page_text, page_no in pages:
            if not page_text.strip():
                continue

            chunks = split_text(page_text)

            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                all_metadata.append({
                    "source_file": filename,
                    "page_no": page_no,
                    "chunk_index": i
                })

    if not all_chunks:
        return {"status": "no usable chunks"}

    add_to_chroma(all_chunks, all_metadata)

    return {
        "status": "success",
        "chunks_stored": len(all_chunks)
    }
