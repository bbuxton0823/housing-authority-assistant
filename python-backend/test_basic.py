#!/usr/bin/env python3
"""
Very basic test server to verify setup
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Housing Authority Assistant API is running!"}

@app.get("/health")
async def health():
    return {"status": "ok", "message": "Basic API working"}

@app.post("/chat")
async def chat(request: dict):
    return {
        "conversation_id": "test-123",
        "current_agent": "Test Agent",
        "messages": [{"content": "Hello! I'm working correctly.", "agent": "Test Agent"}],
        "events": [],
        "context": {},
        "agents": [],
        "guardrails": []
    }

if __name__ == "__main__":
    print("🧪 Starting Basic Test Server")
    print("Backend: http://127.0.0.1:8000")
    print("Health: http://127.0.0.1:8000/health")
    
    uvicorn.run(app, host="127.0.0.1", port=8000)