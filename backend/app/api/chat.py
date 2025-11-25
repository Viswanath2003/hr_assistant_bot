# backend/app/api/chat.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.rag.chain import run_rag
#from app.rag.filter import is_noise_chunk  # NEW import

router = APIRouter()


class ChatRequest(BaseModel):
    query: str
    k: int = 4
    chat_history: list = []  # List of {"role": "user"|"assistant", "content": "..."}


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


@router.post("/chat")
def chat_endpoint(body: ChatRequest):
    query = body.query.strip()

    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        result = run_rag(query, k=body.k, chat_history=body.chat_history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # -----------------------------
    # Defensive filtering (IMPORTANT)
    # -----------------------------
    # clean_sources = []
    # for src in result["sources"]:
    #     text = src.get("text", "")
    #     if not is_noise_chunk(text):
    #         clean_sources.append(src)
    clean_sources = result["sources"]  # SKIP filtering for now
    return {
        "response": result["answer"],
        "sources": clean_sources,  # replace noisy ones
        "retrieved_chunks": len(clean_sources),
    }
