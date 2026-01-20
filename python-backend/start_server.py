#!/usr/bin/env python3
"""Start the Housing Authority Assistant server with clean environment."""

import os
import subprocess
import sys

def start_server():
    """Start the server with a clean API key environment."""

    # Load API key from environment variable
    api_key = os.environ.get('OPENAI_API_KEY', '')

    if not api_key:
        print("⚠️  Warning: OPENAI_API_KEY not set in environment")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
        print("   Or add it to your .env file")
        print()

    # Set environment variables
    env = os.environ.copy()
    env['OPENAI_MODEL'] = 'gpt-4-turbo-preview'
    env['OPENAI_MAX_TOKENS'] = '2000'
    env['OPENAI_TEMPERATURE'] = '0.7'
    env['API_HOST'] = '127.0.0.1'
    env['API_PORT'] = '8000'
    env['LOG_LEVEL'] = 'INFO'
    env['ENVIRONMENT'] = 'development'
    
    print("🚀 Starting Housing Authority Assistant server...")
    print(f"✅ API Key loaded: {len(api_key)} characters")
    print(f"✅ Server will run on: http://localhost:8000")
    print(f"✅ Frontend available at: http://localhost:3000")
    print()
    print("Press Ctrl+C to stop the server")
    
    try:
        # Start uvicorn with clean environment
        subprocess.run([
            'uvicorn', 'api:app', 
            '--reload', 
            '--host', '0.0.0.0', 
            '--port', '8000'
        ], env=env, check=True)
    except KeyboardInterrupt:
        print("\n✅ Server stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_server()