from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from app.core.config import settings


def get_llm():
    """
    Returns the Google Gemini LLM for generating responses.
    """
    return ChatGoogleGenerativeAI(
        model=settings.GOOGLE_LLM_MODEL,
        api_key=settings.GOOGLE_API_KEY,
        temperature=0.3   # safer for HR domain
    )


def get_embedding_model():
    """
    Returns the Google embedding model for vector database storage.
    """
    return GoogleGenerativeAIEmbeddings(
        model=settings.GOOGLE_EMBEDDING_MODEL,
        api_key=settings.GOOGLE_API_KEY
    )
