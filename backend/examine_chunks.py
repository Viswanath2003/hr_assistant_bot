#!/usr/bin/env python3
"""
Examine the actual stored chunks to see how the Holiday Calendar is split.
"""
import sys
sys.path.insert(0, '/home/sigmoid/Desktop/hr_assistant_bot/backend')

from app.rag.vectorstore import get_chroma_client

def examine_holiday_chunks():
    """Get all chunks from Holiday Calendar and examine structure"""
    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name="hr_docs",
        metadata={"hnsw:space": "cosine"}
    )
    
    # Get all items
    all_items = collection.get()
    
    # Filter for Holiday Calendar
    holiday_chunks = []
    for i, meta in enumerate(all_items["metadatas"]):
        if "Holiday Calendar" in meta.get("source_file", ""):
            holiday_chunks.append({
                "id": all_items["ids"][i],
                "content": all_items["documents"][i],
                "metadata": meta
            })
    
    print(f"Found {len(holiday_chunks)} chunks from Holiday Calendar")
    print("\n" + "="*80)
    
    # Sort by page and chunk index
    holiday_chunks.sort(key=lambda x: (x["metadata"].get("page_no", 0), x["metadata"].get("chunk_index", 0)))
    
    # Show each chunk
    for chunk in holiday_chunks:
        print(f"\nChunk ID: {chunk['id']}")
        print(f"Page: {chunk['metadata'].get('page_no')}, Chunk Index: {chunk['metadata'].get('chunk_index')}")
        print(f"Length: {len(chunk['content'])} chars")
        print(f"\nContent:")
        print("-" * 80)
        print(chunk['content'])
        print("-" * 80)
    
    # Look for Christmas specifically
    print("\n\n" + "="*80)
    print("SEARCHING FOR CHRISTMAS")
    print("="*80)
    
    for chunk in holiday_chunks:
        if "christmas" in chunk['content'].lower():
            print(f"\nFound in Chunk {chunk['id']}:")
            print(f"Page: {chunk['metadata'].get('page_no')}, Chunk: {chunk['metadata'].get('chunk_index')}")
            print(chunk['content'])

if __name__ == "__main__":
    examine_holiday_chunks()
