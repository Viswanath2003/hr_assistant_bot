#!/usr/bin/env python3
"""
Debug script to examine what chunks are being retrieved for specific queries.
"""
import sys
sys.path.insert(0, '/home/sigmoid/Desktop/hr_assistant_bot/backend')

from app.rag.vectorstore import get_retriever
from app.rag.chain import run_rag

# Test queries that are failing
test_queries = [
    "List all mandatory holidays",
    "List all optional holidays",
    "Which holiday is on 25th December 2025?",
    "Is Christmas a mandatory or optional holiday?",
]

def debug_retrieval(query: str, k: int = 4):
    """Show what chunks are retrieved for a query"""
    print(f"\n{'='*80}")
    print(f"QUERY: {query}")
    print(f"{'='*80}")
    
    retriever = get_retriever(k=k)
    docs = retriever.invoke(query)
    
    print(f"\nRetrieved {len(docs)} chunks:\n")
    
    for i, doc in enumerate(docs, 1):
        content = getattr(doc, "page_content", "")
        meta = getattr(doc, "metadata", {})
        
        print(f"\n--- CHUNK {i} ---")
        print(f"Source: {meta.get('source_file', 'unknown')}")
        print(f"Page: {meta.get('page_no', '?')}, Chunk: {meta.get('chunk_index', '?')}")
        print(f"Content length: {len(content)} chars")
        print(f"\nContent preview (first 500 chars):")
        print(content[:500])
        print(f"\n... (truncated)" if len(content) > 500 else "")

def test_rag_answer(query: str):
    """Test the full RAG pipeline"""
    print(f"\n{'='*80}")
    print(f"FULL RAG TEST: {query}")
    print(f"{'='*80}")
    
    result = run_rag(query, k=4)
    print(f"\nAnswer:\n{result['answer']}")
    print(f"\nSources: {result['retrieved_chunks']} chunks")

if __name__ == "__main__":
    # First, debug retrieval for each query
    for query in test_queries:
        debug_retrieval(query, k=10)
    
    # Then test full RAG
    print("\n\n" + "="*80)
    print("TESTING FULL RAG PIPELINE")
    print("="*80)
    
    for query in test_queries:
        test_rag_answer(query)
