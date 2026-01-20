#!/usr/bin/env python3
"""
Mac-friendly API key setter that handles copy/paste issues.
Based on the troubleshooting guide for macOS Terminal copy/paste problems.
"""

import os
import sys

def clean_api_key(key):
    """Clean API key using Mac solution for copy/paste issues."""
    if not key:
        return key
    
    # Remove Mac smart quotes and Unicode characters
    key = key.replace('\u2011', '-')  # non-breaking hyphen
    key = key.replace('\u2013', '-')  # en dash  
    key = key.replace('\u2014', '-')  # em dash
    key = key.replace('\u2010', '-')  # hyphen
    key = key.replace('\u00A0', ' ')  # non-breaking space
    key = key.replace('\u201C', '"')  # left double quotation
    key = key.replace('\u201D', '"')  # right double quotation
    key = key.replace('\u2018', "'")  # left single quotation
    key = key.replace('\u2019', "'")  # right single quotation
    
    # Strip whitespace (including carriage returns from rich-text)
    key = key.strip()
    
    return key

def set_api_key():
    """Interactive API key setter with Mac copy/paste fixes."""
    print("🔑 Housing Authority Assistant - API Key Setup")
    print("=" * 50)
    print()
    print("📋 Mac Copy/Paste Tips:")
    print("1. Copy from plain text source (not PDF/web with formatting)")
    print("2. Use TextEdit → Format → Make Plain Text")
    print("3. Paste here - the script will clean Unicode issues")
    print()
    
    # Get API key from user
    api_key = input("Paste your OpenAI API key: ").strip()
    
    if not api_key:
        print("❌ No API key provided")
        return False
    
    # Clean the key
    clean_key = clean_api_key(api_key)
    
    print(f"\n🧹 Cleaning results:")
    print(f"   Original length: {len(api_key)}")
    print(f"   Cleaned length: {len(clean_key)}")
    print(f"   Starts with 'sk-': {clean_key.startswith('sk-')}")
    
    # Validate key format
    if not clean_key.startswith('sk-'):
        print("⚠️  Warning: API key doesn't start with 'sk-'")
        print("   Make sure you copied the complete key from OpenAI")
        proceed = input("Continue anyway? (y/N): ").lower()
        if proceed != 'y':
            return False
    
    # Write to .env file
    env_content = f"""# OpenAI API Configuration
OPENAI_API_KEY={clean_key}

# Model Configuration
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.7

# Server Configuration
API_HOST=127.0.0.1
API_PORT=8000
LOG_LEVEL=INFO
ENVIRONMENT=development
"""
    
    env_path = "/Users/bychabuxton/housing-authority-assistant/.env"
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"✅ API key saved to {env_path}")
    print("\n🚀 Ready to test! Run: python test_api_key.py")
    return True

if __name__ == "__main__":
    try:
        set_api_key()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled")
        sys.exit(1)