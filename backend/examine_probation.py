#!/usr/bin/env python3
"""
Check what chunks are stored from Probation Confirmation Policy
"""
import sys
sys.path.insert(0, '/home/sigmoid/Desktop/hr_assistant_bot/backend')

from app.rag.vectorstore import get_chroma_client

def examine_probation_chunks():
    """Get all chunks from Probation Policy"""
    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name="hr_docs",
        metadata={"hnsw:space": "cosine"}
    )
    
    # Get all items
    all_items = collection.get()
    
    # Filter for Probation Policy
    probation_chunks = []
    for i, meta in enumerate(all_items["metadatas"]):
        if "PROBATION" in meta.get("source_file", "").upper():
            probation_chunks.append({
                "id": all_items["ids"][i],
                "content": all_items["documents"][i],
                "metadata": meta
            })
    
    print(f"Found {len(probation_chunks)} chunks from Probation Policy")
    print("\n" + "="*80)
    
    # Sort by page and chunk index
    probation_chunks.sort(key=lambda x: (x["metadata"].get("page_no", 0), x["metadata"].get("chunk_index", 0)))
    
    # Show each chunk
    for chunk in probation_chunks:
        print(f"\nChunk ID: {chunk['id']}")
        print(f"Page: {chunk['metadata'].get('page_no')}, Chunk Index: {chunk['metadata'].get('chunk_index')}")
        print(f"Length: {len(chunk['content'])} chars")
        print(f"\nContent:")
        print("-" * 80)
        print(chunk['content'])
        print("-" * 80)

if __name__ == "__main__":
    examine_probation_chunks()
