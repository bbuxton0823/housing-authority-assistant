#!/usr/bin/env python3
"""
Simple server starter that bypasses some initialization issues
"""

import uvicorn
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

if __name__ == "__main__":
    print("🏠 Starting Housing Authority Assistant (Voice + Navigation)")
    print("=" * 60)
    
    # Check API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
    
    print(f"✅ OpenAI API Key: {'Found' if openai_key else 'Missing'}")
    print(f"✅ ElevenLabs API Key: {'Found' if elevenlabs_key else 'Missing'}")
    
    print("\nStarting server on http://127.0.0.1:8000")
    print("Frontend should be at http://localhost:3000")
    print("=" * 60)
    
    # Start server
    uvicorn.run(
        "api:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )