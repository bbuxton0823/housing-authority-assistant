#!/usr/bin/env python3
"""
Test script to verify voice and navigation setup
"""

import os
import sys
from dotenv import load_dotenv

def test_environment():
    """Test environment variables are set up correctly."""
    print("🔧 Testing Environment Setup...")
    
    load_dotenv()
    
    openai_key = os.getenv("OPENAI_API_KEY")
    elevenlabs_key = os.getenv("ELEVENLABS_API_KEY") 
    voice_id = os.getenv("ELEVENLABS_VOICE_ID")
    
    issues = []
    
    if not openai_key or openai_key == "sk-your-openai-api-key-here":
        issues.append("❌ OpenAI API key not set")
    else:
        print(f"✅ OpenAI API key found: {openai_key[:10]}...")
    
    if not elevenlabs_key or elevenlabs_key == "your-elevenlabs-api-key-here":
        issues.append("❌ ElevenLabs API key not set")
    else:
        print(f"✅ ElevenLabs API key found: {elevenlabs_key[:10]}...")
    
    if voice_id:
        print(f"✅ Voice ID set: {voice_id}")
    
    return len(issues) == 0, issues

def test_dependencies():
    """Test required packages are installed."""
    print("\n📦 Testing Dependencies...")
    
    required_packages = [
        ("elevenlabs", "ElevenLabs SDK"),
        ("playwright", "Playwright"),
        ("fastapi", "FastAPI"),
        ("pydantic", "Pydantic"),
        ("uvicorn", "Uvicorn")
    ]
    
    missing = []
    
    for package, name in required_packages:
        try:
            __import__(package)
            print(f"✅ {name} installed")
        except ImportError:
            missing.append(package)
            print(f"❌ {name} missing")
    
    return len(missing) == 0, missing

def test_voice_service():
    """Test voice service initialization."""
    print("\n🎤 Testing Voice Service...")
    
    try:
        sys.path.append('python-backend')
        from voice_service import voice_service
        
        info = voice_service.get_voice_info()
        if info.get("enabled"):
            print("✅ Voice service enabled")
            print(f"   Voice ID: {info.get('voice_id')}")
            print(f"   Supported agents: {len(info.get('supported_agents', []))}")
            return True
        else:
            print("❌ Voice service disabled")
            return False
            
    except Exception as e:
        print(f"❌ Voice service error: {e}")
        return False

def test_navigation_service():
    """Test navigation service initialization."""
    print("\n🧭 Testing Navigation Service...")
    
    try:
        sys.path.append('python-backend')
        from playwright_navigation import navigation_service
        
        print("✅ Navigation service imported")
        print(f"   Site map has {len(navigation_service.site_map)} pages")
        
        # List available pages
        for page_key in navigation_service.site_map.keys():
            print(f"   - {page_key}")
        
        return True
        
    except Exception as e:
        print(f"❌ Navigation service error: {e}")
        return False

def main():
    print("🏠 Housing Authority Assistant - Voice Setup Test")
    print("=" * 60)
    
    # Test environment
    env_ok, env_issues = test_environment()
    
    # Test dependencies  
    deps_ok, missing_deps = test_dependencies()
    
    # Test services (only if env and deps are ok)
    voice_ok = False
    nav_ok = False
    
    if env_ok and deps_ok:
        voice_ok = test_voice_service()
        nav_ok = test_navigation_service()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SETUP SUMMARY")
    print("=" * 60)
    
    if env_ok and deps_ok and voice_ok and nav_ok:
        print("🎉 ALL TESTS PASSED! Voice integration is ready.")
        print("\nNext steps:")
        print("1. cd python-backend")
        print("2. python -m uvicorn api:app --reload")
        print("3. cd ../ui && npm run dev")
        print("4. Visit http://localhost:3000")
    else:
        print("⚠️  Issues found:")
        
        if not env_ok:
            for issue in env_issues:
                print(f"   {issue}")
            print("   Fix: Update your .env file with real API keys")
        
        if not deps_ok:
            print(f"   Missing packages: {', '.join(missing_deps)}")
            print("   Fix: pip install -r python-backend/requirements.txt")
        
        if env_ok and deps_ok and not voice_ok:
            print("   Voice service issues - check ElevenLabs API key")
        
        if env_ok and deps_ok and not nav_ok:
            print("   Navigation service issues - check Playwright installation")

if __name__ == "__main__":
    main()