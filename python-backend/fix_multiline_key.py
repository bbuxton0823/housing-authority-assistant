#!/usr/bin/env python3
"""Fix multiline API key issue from Mac Terminal wrapping."""

import os
import re

def fix_multiline_api_key():
    """Fix API key that may have been wrapped across multiple lines."""
    
    env_path = "/Users/bychabuxton/housing-authority-assistant/.env"
    
    # Read the current .env file
    with open(env_path, 'r') as f:
        content = f.read()
    
    print("🔧 Fixing potential multiline API key issue...")
    print(f"Original content length: {len(content)}")
    
    # Look for API key that might be split across lines
    # Pattern: OPENAI_API_KEY=sk-... (possibly followed by newlines and continuation)
    pattern = r'OPENAI_API_KEY=([^\n]+(?:\n[^#\n\r]+)*)'
    match = re.search(pattern, content)
    
    if match:
        api_key_section = match.group(1)
        print(f"Found API key section: {repr(api_key_section[:50])}...")
        
        # Remove any newlines and whitespace from the key
        cleaned_key = re.sub(r'\s+', '', api_key_section)
        print(f"Cleaned key length: {len(cleaned_key)}")
        print(f"Starts with sk-proj: {cleaned_key.startswith('sk-proj')}")
        
        # Replace the original key section with cleaned version
        new_content = content.replace(match.group(0), f'OPENAI_API_KEY={cleaned_key}')
        
        # Write back to file
        with open(env_path, 'w') as f:
            f.write(new_content)
        
        print("✅ Fixed API key and wrote to .env file")
        print(f"New key length: {len(cleaned_key)}")
        
        return cleaned_key
    else:
        print("❌ Could not find API key in .env file")
        return None

if __name__ == "__main__":
    fix_multiline_api_key()