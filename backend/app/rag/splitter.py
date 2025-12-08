from langchain_text_splitters import RecursiveCharacterTextSplitter
from ..core.config import settings

def get_text_splitter():
    """
    Returns a text splitter that breaks long text into
    overlapping chunks suitable for embedding.
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        # Prioritize larger breaks to preserve table structure
        separators=["\n\n\n", "\n\n", "\n", ". ", " ", ""]
    )


def split_text(text: str):
    """
    Splits input text into chunks using the default splitter.
    """
    splitter = get_text_splitter()
    chunks = splitter.split_text(text)
    return chunks
