from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import ingest, chat, auth

# Import models so that SQLModel metadata knows about them
from .models import user, session, message

from .core.database import init_db

app = FastAPI(title="HR Assistant Bot API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    init_db()

app.include_router(ingest.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])

@app.get("/")
def root():
    return {"message": "HR Assistant Bot Backend is running"}
