from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ..rag.chain import run_rag
# from app.rag.filter import is_noise_chunk  # NEW import (still unused)

from ..dependencies import get_current_user
from ..core.database import get_session
from ..models.session import ChatSession
from ..models.message import ChatMessage

router = APIRouter()


class ChatFeedbackRequest(BaseModel):
    session_id: int
    message_id: int
    feedback_type: str  # e.g., "thumbs_up", "thumbs_down"
    feedback_text: str | None = None


class ChatRequest(BaseModel):
    query: str
    k: int = 4
    chat_history: list = []  # List of {"role": "user"|"assistant", "content": "..."}
    session_id: int | None = None


class ChatMessageModel(BaseModel):
    role: str  # "user" or "assistant"
    content: str

@router.post("/chat")
def chat_endpoint(
    body: ChatRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_session),
):
    query = body.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # Retrieve or create chat session
    if body.session_id:
        session = db.get(ChatSession, body.session_id)
        if not session or session.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Chat session not found.")
    else:
        session = ChatSession(user_id=current_user.id)
        db.add(session)
        db.commit()
        db.refresh(session)

    # Store user message
    user_msg = ChatMessage(session_id=session.id, role="user", content=query)
    db.add(user_msg)
    db.commit()

    # Build chat history if not provided
    if not body.chat_history:
        from sqlmodel import select
        statement = select(ChatMessage).where(ChatMessage.session_id == session.id).order_by(ChatMessage.id.desc()).limit(10)
        msgs = db.exec(statement).all()
        history = [{"role": m.role, "content": m.content} for m in reversed(msgs)]
    else:
        history = body.chat_history

    try:
        result = run_rag(query, k=body.k, chat_history=history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Store assistant response
    assistant_msg = ChatMessage(session_id=session.id, role="assistant", content=result["answer"])
    db.add(assistant_msg)
    db.commit()

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
        "sources": clean_sources,
        "retrieved_chunks": len(clean_sources),
        "session_id": session.id,
    }
