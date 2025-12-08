# HR Assistant Bot Backend

## Overview
This is the backend for the HR Assistant Bot, built with FastAPI, LangChain, and SQLModel. It provides a RAG-based chat interface with persistent memory and user authentication.

## Features
- **RAG Pipeline**: Retrieves information from HR documents (PDFs) to answer user queries.
- **Chat Memory**: Stores conversation history in a SQLite database.
- **Authentication**: JWT-based authentication (Register, Login, Refresh).
- **Context-Awareness**: Uses chat history to provide context for follow-up questions.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Variables**:
    Create a `.env` file in `backend/` (or set env vars):
    ```
    GOOGLE_API_KEY=your_google_api_key
    JWT_SECRET_KEY=your_secret_key
    ```

3.  **Run the Server**:
    ```bash
    python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
    ```

## API Endpoints

### Authentication
- `POST /api/auth/register`: Register a new user.
  - Body: `{"email": "user@example.com", "password": "password"}`
- `POST /api/auth/login`: Login and get tokens.
  - Body: `{"email": "user@example.com", "password": "password"}`
- `POST /api/auth/refresh`: Refresh access token.
  - Body: `{"refresh_token": "..."}`

### Chat
- `POST /api/chat`: Send a message to the bot.
  - Header: `Authorization: Bearer <access_token>`
  - Body: `{"query": "What is the leave policy?", "session_id": 1 (optional), "chat_history": [...] (optional)}`

### Ingestion
- `POST /api/ingest`: Trigger document ingestion.

## Database
The application uses SQLite (`data/hr_bot.db`). Tables are automatically created on startup.
