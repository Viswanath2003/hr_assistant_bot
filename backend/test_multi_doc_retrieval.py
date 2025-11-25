#!/usr/bin/env python3
"""
Test what chunks are retrieved for the probation/notice period query
"""
import sys
sys.path.insert(0, '/home/sigmoid/Desktop/hr_assistant_bot/backend')

from app.rag.vectorstore import get_retriever

query = "if i have joined this org in nov 2025, what would be my notice period if i resign on november 30 and is accepted on the same day"

print(f"Query: {query}\n")
print("="*80)

# Test with different k values
for k in [4, 8, 12]:
    print(f"\n\nTesting with k={k}")
    print("-"*80)
    
    retriever = get_retriever(k=k)
    docs = retriever.invoke(query)
    
    print(f"Retrieved {len(docs)} chunks:\n")
    
    sources = {}
    for i, doc in enumerate(docs, 1):
        content = getattr(doc, "page_content", "")
        meta = getattr(doc, "metadata", {})
        
        source_file = meta.get("source_file", "unknown")
        if source_file not in sources:
            sources[source_file] = 0
        sources[source_file] += 1
        
        print(f"{i}. {source_file} (page {meta.get('page_no')}, chunk {meta.get('chunk_index')})")
        if "probation" in content.lower() or "6 month" in content.lower():
            print(f"   ⭐ Contains probation info!")
    
    print(f"\nSource distribution:")
    for source, count in sources.items():
        print(f"  - {source}: {count} chunks")
