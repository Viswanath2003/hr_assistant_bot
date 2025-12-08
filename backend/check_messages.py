from sqlmodel import Session, create_engine, select
from app.models.message import ChatMessage
from app.core.config import settings

DB_PATH = settings.BASE_DIR / "data" / "hr_bot.db"
DB_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DB_URL)

with Session(engine) as session:
    statement = select(ChatMessage).where(ChatMessage.session_id == 1).order_by(ChatMessage.id)
    results = session.exec(statement).all()
    print(f"Messages for session 1: {len(results)}")
    for msg in results:
        print(f"[{msg.role}] {msg.content}")
