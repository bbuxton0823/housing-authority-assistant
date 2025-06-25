#!/usr/bin/env python3
"""
Script to easily update Housing Authority URLs in the navigation service
"""

import json
import re

def update_urls_from_config():
    """Update navigation service URLs from the JSON configuration."""
    
    # Load URL configuration
    try:
        with open('housing_authority_urls.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ housing_authority_urls.json not found")
        return False
    
    pages = config['housing_authority_urls']['pages']
    
    # Read current navigation service file
    nav_file = 'python-backend/playwright_navigation.py'
    try:
        with open(nav_file, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ {nav_file} not found")
        return False
    
    print("🔧 Updating navigation URLs...")
    
    # Update each URL in the site_map
    updates_made = 0
    for page_key, page_info in pages.items():
        new_url = page_info['url']
        
        # Find and replace the URL for this page
        pattern = f'"{page_key}": {{[^}}]*"url": "[^"]*"'
        
        def replace_url(match):
            nonlocal updates_made
            old_content = match.group(0)
            new_content = re.sub(r'"url": "[^"]*"', f'"url": "{new_url}"', old_content)
            if old_content != new_content:
                updates_made += 1
                print(f"   ✅ Updated {page_key}: {new_url}")
            return new_content
        
        content = re.sub(pattern, replace_url, content, flags=re.DOTALL)
    
    # Write updated content back
    if updates_made > 0:
        with open(nav_file, 'w') as f:
            f.write(content)
        
        print(f"\n🎉 Updated {updates_made} URLs in navigation service")
        print(f"   File: {nav_file}")
        return True
    else:
        print("ℹ️  No URL updates needed")
        return False

def show_current_urls():
    """Display current URLs in the navigation service."""
    print("\n📋 Current Navigation URLs:")
    print("=" * 50)
    
    try:
        with open('housing_authority_urls.json', 'r') as f:
            config = json.load(f)
            
        for page_key, page_info in config['housing_authority_urls']['pages'].items():
            print(f"{page_key:20} → {page_info['url']}")
            print(f"{'':20}   {page_info['description']}")
            print()
            
    except Exception as e:
        print(f"❌ Error reading URLs: {e}")

def interactive_url_update():
    """Interactive URL update process."""
    print("🏠 Housing Authority URL Configuration")
    print("=" * 50)
    
    try:
        with open('housing_authority_urls.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ Configuration file not found")
        return
    
    pages = config['housing_authority_urls']['pages']
    updated = False
    
    print("\nCurrent URLs (press Enter to keep current, or type new URL):")
    print("-" * 60)
    
    for page_key, page_info in pages.items():
        current_url = page_info['url']
        description = page_info['description']
        
        print(f"\n📄 {page_key.replace('_', ' ').title()}")
        print(f"   Description: {description}")
        print(f"   Current URL: {current_url}")
        
        new_url = input("   New URL (or press Enter to keep): ").strip()
        
        if new_url and new_url != current_url:
            pages[page_key]['url'] = new_url
            updated = True
            print(f"   ✅ Updated to: {new_url}")
    
    if updated:
        # Save updated configuration
        with open('housing_authority_urls.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        # Update navigation service
        update_urls_from_config()
        
        print("\n🎉 URLs updated successfully!")
        print("   Restart the backend to apply changes:")
        print("   cd python-backend && python -m uvicorn api:app --reload")
    else:
        print("\nℹ️  No changes made")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_url_update()
    elif len(sys.argv) > 1 and sys.argv[1] == "--show":
        show_current_urls()
    else:
        print("🔧 Quick URL Update")
        print("=" * 30)
        
        show_current_urls()
        
        print("\nOptions:")
        print("1. python update_navigation_urls.py --interactive  # Interactive update")
        print("2. python update_navigation_urls.py --show        # Show current URLs") 
        print("3. Edit housing_authority_urls.json manually, then run this script")
        
        response = input("\nUpdate URLs now? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            interactive_url_update()
        else:
            print("\nTo update later:")
            print("1. Edit the URLs in housing_authority_urls.json")
            print("2. Run: python update_navigation_urls.py")