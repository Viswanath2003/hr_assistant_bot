from fastapi import FastAPI
from app.api import ingest, chat

app = FastAPI(title="HR Assistant Bot API")

app.include_router(ingest.router, prefix="/api")
app.include_router(chat.router, prefix="/api")

@app.get("/")
def root():
    return {"message": "HR Assistant Bot Backend is running"}
