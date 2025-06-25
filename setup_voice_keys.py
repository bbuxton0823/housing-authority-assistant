#!/usr/bin/env python3
"""
Mac-friendly script to set up ElevenLabs API key safely
Avoids Unicode issues that can occur with Mac Terminal copy/paste
"""

import os
import re

def clean_api_key(key):
    """Clean API key of any Unicode characters that may have been introduced by Mac copy/paste."""
    if not key:
        return key
    
    # Remove common Unicode characters that get introduced on Mac
    replacements = {
        '\u2011': '-',    # non-breaking hyphen
        '\u2013': '-',    # en dash  
        '\u2014': '-',    # em dash
        '\u201c': '"',    # left double quote
        '\u201d': '"',    # right double quote
        '\u2018': "'",    # left single quote
        '\u2019': "'",    # right single quote
        '\u00a0': ' ',    # non-breaking space
    }
    
    for unicode_char, replacement in replacements.items():
        key = key.replace(unicode_char, replacement)
    
    # Remove any whitespace and newlines
    key = key.strip()
    
    # Remove any line breaks (common when pasting long keys)
    key = key.replace('\n', '').replace('\r', '')
    
    return key

def setup_elevenlabs_key():
    """Set up ElevenLabs API key in .env file."""
    print("🎤 ElevenLabs API Key Setup for Mac")
    print("=" * 50)
    
    # Get existing OpenAI key if present
    env_path = ".env"
    openai_key = ""
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            content = f.read()
            # Extract existing OpenAI key
            openai_match = re.search(r'OPENAI_API_KEY=(.+)', content)
            if openai_match:
                openai_key = openai_match.group(1).strip()
    
    print("\n📋 Instructions:")
    print("1. Go to https://elevenlabs.io")
    print("2. Sign up or log in")
    print("3. Go to Profile/Settings")
    print("4. Copy your API key")
    print("5. Paste it below (press Enter when done)")
    
    print("\n⚠️  Mac Users: If your API key appears on multiple lines after pasting,")
    print("   that's normal - this script will clean it up automatically!")
    
    print("\nPaste your ElevenLabs API key:")
    
    # Read API key (handle multi-line paste on Mac)
    key_lines = []
    while True:
        try:
            line = input()
            if line.strip() == "" and key_lines:
                break
            if line.strip():
                key_lines.append(line.strip())
        except EOFError:
            break
    
    # Join all lines and clean
    elevenlabs_key = "".join(key_lines)
    elevenlabs_key = clean_api_key(elevenlabs_key)
    
    print(f"\n🔧 Processing API key...")
    print(f"   Length: {len(elevenlabs_key)} characters")
    print(f"   Starts with: {elevenlabs_key[:10]}...")
    
    # Validate key format
    if not elevenlabs_key or len(elevenlabs_key) < 10:
        print("❌ Error: API key seems too short or empty")
        return False
    
    # Write to .env file
    env_content = f"""# OpenAI API Configuration
OPENAI_API_KEY={openai_key if openai_key else 'sk-your-openai-api-key-here'}

# ElevenLabs Voice Integration
ELEVENLABS_API_KEY={elevenlabs_key}
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM

# Optional: Set log level for debugging
# LOG_LEVEL=INFO

# Optional: Custom API host and port
# API_HOST=0.0.0.0
# API_PORT=8000

# Voice and Navigation Settings
ENABLE_VOICE_BY_DEFAULT=true
ENABLE_NAVIGATION_BY_DEFAULT=true
HOUSING_AUTHORITY_BASE_URL=https://smchousing.org

# Voice ID 21m00Tcm4TlvDq8ikWAM is "Rachel" - a professional, warm female voice
# You can find other voice IDs at: https://elevenlabs.io/voice-library
"""
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print("✅ API key saved successfully!")
    print(f"   Saved to: {os.path.abspath(env_path)}")
    
    # Also create backend-specific .env
    backend_env_path = "python-backend/.env"
    with open(backend_env_path, 'w') as f:
        f.write(env_content)
    
    print(f"   Also saved to: {os.path.abspath(backend_env_path)}")
    
    return True

def test_api_key():
    """Test the ElevenLabs API key."""
    print("\n🧪 Testing ElevenLabs API key...")
    
    try:
        # Import here to avoid issues if elevenlabs not installed
        from elevenlabs import set_api_key, generate
        import os
        from dotenv import load_dotenv
        
        # Load environment
        load_dotenv()
        
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            print("❌ No API key found in .env file")
            return False
        
        # Set API key
        set_api_key(api_key)
        
        # Test with a simple phrase
        print("   Generating test audio...")
        audio = generate(
            text="Hello! This is a test of the voice integration system.",
            voice="21m00Tcm4TlvDq8ikWAM",  # Rachel voice
            model="eleven_monolingual_v1"
        )
        
        print("✅ API key works! Voice service is ready.")
        print(f"   Generated {len(audio)} bytes of audio")
        return True
        
    except ImportError:
        print("⚠️  ElevenLabs package not found. Run: pip install elevenlabs")
        return False
    except Exception as e:
        print(f"❌ API key test failed: {e}")
        if "Unauthorized" in str(e):
            print("   💡 Check that your API key is correct")
        elif "quota" in str(e).lower():
            print("   💡 You may have exceeded your ElevenLabs quota")
        return False

if __name__ == "__main__":
    print("🏠 Housing Authority Assistant - Voice Setup")
    print("=" * 50)
    
    success = setup_elevenlabs_key()
    if success:
        test_api_key()
    
    print("\n🚀 Setup complete! You can now run the voice-enabled assistant.")
    print("\nNext steps:")
    print("1. cd python-backend")
    print("2. python -m uvicorn api:app --reload")
    print("3. cd ../ui && npm run dev")