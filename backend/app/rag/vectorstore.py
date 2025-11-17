import os
from pathlib import Path
from typing import List

from chromadb import PersistentClient
from langchain_community.vectorstores import Chroma

from app.core.config import settings
from app.rag.embedder import get_embedder


def get_chroma_client():
    """
    Returns a Persistent ChromaDB client using the new API (v1.3+).
    """
    persist_dir = Path(settings.CHROMA_DIR)
    persist_dir.mkdir(parents=True, exist_ok=True)

    client = PersistentClient(path=str(persist_dir))
    return client


def create_or_load_collection():
    """
    Create or load a collection named 'hr_docs'.
    """
    client = get_chroma_client()

    collection = client.get_or_create_collection(
        name="hr_docs",
        metadata={"hnsw:space": "cosine"}
    )
    return collection


def add_to_chroma(texts: List[str], metadatas: List[dict]):
    """
    Add documents + embeddings to ChromaDB (new API).
    """
    embedder = get_embedder()
    collection = create_or_load_collection()

    print("🔍 Generating embeddings...")
    embeddings = embedder.embed_documents(texts)

    # Build deterministic ids and deduplicate identical normalized texts before add
    def _normalize(s: str) -> str:
        return " ".join(s.strip().lower().split())

    seen = {}
    ids = []
    deduped_texts = []
    deduped_embeddings = []
    deduped_metas = []

    for i, (txt, emb, meta) in enumerate(zip(texts, embeddings, metadatas)):
        norm = _normalize(txt)
        if norm in seen:
            # skip exact duplicate chunk
            continue
        seen[norm] = True
        deduped_texts.append(txt)
        deduped_embeddings.append(emb)
        # reindex chunk index for storage (optional)
        m = dict(meta)
        m["chunk_index"] = len(deduped_texts) - 1
        deduped_metas.append(m)
        ids.append(f"{meta.get('source_file','doc')}_p{meta.get('page_no',0)}_c{m['chunk_index']}")

    print("📥 Adding chunks to ChromaDB...")

    collection.add(
        ids=ids,
        documents=deduped_texts,
        embeddings=deduped_embeddings,
        metadatas=deduped_metas,
    )

    print("✅ Documents stored successfully!")


def get_unique_documents_count() -> int:
    """
    Count the number of unique source documents in the collection.
    
    Returns:
        Number of unique document files (source_file values in metadata).
    """
    try:
        client = get_chroma_client()
        collection = client.get_or_create_collection(
            name="hr_docs",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Get all items in the collection to count unique sources
        all_items = collection.get()
        if not all_items or not all_items.get("metadatas"):
            return 0
        
        unique_sources = set()
        for meta in all_items["metadatas"]:
            source_file = meta.get("source_file", "unknown")
            unique_sources.add(source_file)
        
        return len(unique_sources)
    except Exception as e:
        print(f"⚠️ Error counting documents: {e}")
        return 0


def calculate_dynamic_k(base_k: int = 4, num_documents: int = None) -> int:
    """
    Calculate optimal k value based on the number of unique documents in the collection.
    
    Strategy:
    - For each unique document, retrieve at least 2-3 chunks on average
    - Ensure diversity: k >= num_documents * 3 (but at least base_k * 5)
    - This scales automatically as more documents are added
    
    Args:
        base_k: Default k value for single-document or simple queries (default=4)
        num_documents: Number of unique documents in collection. 
                      If None, queries the collection.
    
    Returns:
        Optimal k value for retrieval.
    
    Examples:
        - 1 document: k=4   (1 * 3 = 3, but min is 4)
        - 2 documents: k=6  (2 * 3 = 6)
        - 3 documents: k=9  (3 * 3 = 9)
        - 4 documents: k=12 (4 * 3 = 12)
    """
    if num_documents is None:
        num_documents = get_unique_documents_count()
    
    # Ensure each document gets at least 3 chunks on average
    optimal_k = max(base_k * 5, num_documents * 3)
    
    return optimal_k


def get_retriever(k: int = 4):
    """
    Loads the Chroma collection into a LangChain retriever.
    """
    embedder = get_embedder()

    vectorstore = Chroma(
        client=get_chroma_client(),
        collection_name="hr_docs",
        embedding_function=embedder
    )

    return vectorstore.as_retriever(
        search_kwargs={"k": k}
    )
