import os
from pathlib import Path
from typing import List

from chromadb import PersistentClient
from langchain_community.vectorstores import Chroma

from ..core.config import settings
from .embedder import get_embedder


def get_chroma_client():
    """
    Returns a Persistent ChromaDB client using the new API (v1.3+).
    """
    persist_dir = Path(settings.CHROMA_DIR)
    persist_dir.mkdir(parents=True, exist_ok=True)

    client = PersistentClient(path=str(persist_dir))
    return client


def get_vectorstore():
    """
    Returns the Chroma vector store.
    """
    client = get_chroma_client()
    embedding_function = get_embedder()

    vectorstore = Chroma(
        client=client,
        collection_name="hr_docs",
        embedding_function=embedding_function,
    )
    return vectorstore


def add_to_chroma(chunks: List[str], metadata: List[dict]):
    """
    Adds chunks to the Chroma vector store.
    """
    vectorstore = get_vectorstore()
    vectorstore.add_texts(texts=chunks, metadatas=metadata)
    print(f"✅ Added {len(chunks)} chunks to ChromaDB.")


def get_retriever(k: int = 4):
    """
    Returns a retriever object.
    """
    vectorstore = get_vectorstore()
    return vectorstore.as_retriever(search_kwargs={"k": k})


def calculate_dynamic_k(question: str, base_k: int = 4) -> int:
    """
    Dynamically adjusts k based on query complexity.
    """
    # Simple heuristic: if query is long or contains "and", increase k
    if len(question.split()) > 10 or "and" in question.lower():
        return base_k + 2
    return base_k

def clear_collection():
    """
    Deletes the existing 'hr_docs' collection in ChromaDB.
    """
    client = get_chroma_client()
    try:
        client.delete_collection("hr_docs")
        print("🗑️ Deleted existing 'hr_docs' collection.")
    except Exception:
        print("⚠️ Collection 'hr_docs' not found, nothing to delete.")

def get_unique_documents_count() -> int:
    """
    Returns the number of unique documents in the vector store.
    """
    client = get_chroma_client()
    try:
        collection = client.get_collection("hr_docs")
        # Get all metadata
        result = collection.get(include=["metadatas"])
        metadatas = result["metadatas"]
        if not metadatas:
            return 0
        
        # Count unique 'source' values
        unique_docs = set()
        for meta in metadatas:
            if meta and "source" in meta:
                unique_docs.add(meta["source"])
        
        return len(unique_docs)
    except Exception as e:
        print(f"Error counting documents: {e}")
        return 0
