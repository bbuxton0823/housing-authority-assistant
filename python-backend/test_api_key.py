#!/usr/bin/env python3
"""Test if the API key is working correctly."""

import os
import asyncio
from dotenv import load_dotenv

def test_api_key_format():
    """Test API key format and loading."""
    load_dotenv()
    key = os.getenv('OPENAI_API_KEY')
    
    print("🔍 API Key Analysis:")
    print(f"   Loaded: {bool(key)}")
    print(f"   Length: {len(key) if key else 0}")
    print(f"   Starts with 'sk-': {key.startswith('sk-') if key else False}")
    
    if key:
        # Check for Unicode issues
        unicode_chars = []
        for i, char in enumerate(key):
            if ord(char) > 127:
                unicode_chars.append(f"position {i}: {repr(char)} (U+{ord(char):04X})")
        
        if unicode_chars:
            print(f"   ❌ Unicode issues found:")
            for issue in unicode_chars:
                print(f"      {issue}")
            return False
        else:
            print(f"   ✅ No Unicode issues")
    
    return bool(key) and key.startswith('sk-')

async def test_openai_connection():
    """Test actual OpenAI API connection."""
    try:
        from safe_openai_fix import apply_safe_fix
        apply_safe_fix()
        
        import openai
        client = openai.OpenAI()
        
        print("\n🌐 Testing OpenAI connection...")
        response = await client.chat.completions.acreate(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'API test successful'"}],
            max_tokens=10
        )
        
        print(f"   ✅ Success! Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"   ❌ Failed: {type(e).__name__}: {e}")
        return False

async def test_housing_assistant():
    """Test the Housing Authority Assistant agents."""
    try:
        from safe_openai_fix import apply_safe_fix
        apply_safe_fix()
        
        from main import triage_agent, create_initial_context
        from agents import Runner
        
        print("\n🏠 Testing Housing Authority Assistant...")
        
        ctx = create_initial_context()
        input_items = [{"content": "Hello, I need help with housing assistance", "role": "user"}]
        
        result = await Runner.run(triage_agent, input_items, context=ctx)
        
        print(f"   ✅ Success! Agent responded with {len(result.new_items)} items")
        return True
        
    except Exception as e:
        print(f"   ❌ Failed: {type(e).__name__}: {e}")
        return False

async def main():
    """Run all tests."""
    print("🧪 Housing Authority Assistant - API Key Test")
    print("=" * 50)
    
    # Test 1: API key format
    if not test_api_key_format():
        print("\n❌ API key format test failed")
        print("💡 Run: python set_api_key.py to fix this")
        return
    
    # Test 2: OpenAI connection
    if not await test_openai_connection():
        print("\n❌ OpenAI connection test failed")
        print("💡 Check your API key at https://platform.openai.com/api-keys")
        return
    
    # Test 3: Housing Assistant
    if not await test_housing_assistant():
        print("\n❌ Housing Assistant test failed")
        return
    
    print("\n🎉 All tests passed! Your Housing Authority Assistant is ready!")
    print("🚀 Start the server with: uvicorn api:app --reload --host 0.0.0.0 --port 8000")

if __name__ == "__main__":
    asyncio.run(main())