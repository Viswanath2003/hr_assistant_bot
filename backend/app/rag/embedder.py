from ..core.llm import get_embedding_model

def get_embedder():
    """
    Loads the Google embedding model.
    """
    return get_embedding_model()


def embed_text(chunks: list[str]):
    """
    Embeds a list of text chunks.
    Returns a list of embedding vectors.
    """
    embedder = get_embedder()
    embeddings = embedder.embed_documents(chunks)
    return embeddings


def embed_query(query: str):
    """
    Embeds a single query (for retrieval at runtime).
    """
    embedder = get_embedder()
    return embedder.embed_query(query)
