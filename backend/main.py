import os
import httpx
import sqlite3
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Qwen Chat API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
OLLAMA_HOST = os.getenv("OLLAMA_BASE_URL") or os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen2.5:0.5b")
OLLAMA_TIMEOUT = 300
DB_PATH = "chat_history.db"

# Initialize database
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE,
            title TEXT,
            model TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            timestamp TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Message]] = []
    model: Optional[str] = None
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    model: str

@app.get("/api/health")
async def health_check():
    """Check API and Ollama connectivity"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "ok",
                    "ollama": "connected",
                    "models": len(data.get("models", []))
                }
    except Exception as e:
        logger.error(f"Ollama connection error: {e}")
        return {
            "status": "degraded",
            "ollama": "disconnected",
            "models": 0
        }

@app.get("/api/models")
async def get_models():
    """Get list of available models from Ollama"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [m.get("name") for m in data.get("models", [])]
                return {"models": models, "default": MODEL_NAME}
    except Exception as e:
        logger.error(f"Error fetching models: {e}")
        return {"models": [MODEL_NAME], "default": MODEL_NAME}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint - sends message to Ollama"""
    try:
        model = request.model or MODEL_NAME
        session_id = request.session_id
        
        # Save message to database if session_id provided
        if session_id:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute(
                'INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)',
                (session_id, 'user', request.message, datetime.now())
            )
            conn.commit()
            conn.close()
        
        # Build prompt from history
        prompt_text = ""
        if request.history:
            for msg in request.history:
                role = msg.role.upper()
                prompt_text += f"{role}: {msg.content}\n"
        
        prompt_text += f"USER: {request.message}\nASSISTANT:"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt_text,
                    "stream": False,
                    "context_length": 2048,
                },
                timeout=OLLAMA_TIMEOUT
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama error: {response.text}")
                raise HTTPException(status_code=500, detail="Ollama API error")
            
            data = response.json()
            assistant_response = data.get("response", "").strip()
            
            # Save assistant response to database if session_id provided
            if session_id:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute(
                    'INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)',
                    (session_id, 'assistant', assistant_response, datetime.now())
                )
                c.execute(
                    'UPDATE sessions SET updated_at = ? WHERE session_id = ?',
                    (datetime.now(), session_id)
                )
                conn.commit()
                conn.close()
            
            return ChatResponse(
                response=assistant_response,
                model=model
            )

    except httpx.ConnectError:
        logger.error("Cannot connect to Ollama server")
        raise HTTPException(
            status_code=503,
            detail="Cannot connect to Ollama server. Ensure Ollama is running on " + OLLAMA_HOST
        )
    except httpx.TimeoutException:
        logger.error("Ollama request timeout")
        raise HTTPException(
            status_code=504,
            detail="Ollama request timeout. Model may be too large or busy."
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/sessions")
async def create_session(title: str = "New Chat"):
    """Create a new chat session"""
    try:
        import uuid
        session_id = str(uuid.uuid4())
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            'INSERT INTO sessions (session_id, title, model, created_at, updated_at) VALUES (?, ?, ?, ?, ?)',
            (session_id, title, MODEL_NAME, datetime.now(), datetime.now())
        )
        conn.commit()
        conn.close()
        return {"session_id": session_id, "title": title}
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail="Error creating session")

@app.get("/api/sessions")
async def get_sessions():
    """Get all chat sessions"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT session_id, title, model, created_at, updated_at FROM sessions ORDER BY updated_at DESC')
        sessions = [dict(row) for row in c.fetchall()]
        conn.close()
        return {"sessions": sessions}
    except Exception as e:
        logger.error(f"Error fetching sessions: {e}")
        raise HTTPException(status_code=500, detail="Error fetching sessions")

@app.get("/api/sessions/{session_id}")
async def get_session_messages(session_id: str):
    """Get all messages in a session"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT role, content, timestamp FROM messages WHERE session_id = ? ORDER BY timestamp', (session_id,))
        messages = [dict(row) for row in c.fetchall()]
        conn.close()
        return {"messages": messages}
    except Exception as e:
        logger.error(f"Error fetching messages: {e}")
        raise HTTPException(status_code=500, detail="Error fetching messages")

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a chat session"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('DELETE FROM messages WHERE session_id = ?', (session_id,))
        c.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
        conn.commit()
        conn.close()
        return {"status": "deleted"}
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail="Error deleting session")

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Qwen Chat API", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
