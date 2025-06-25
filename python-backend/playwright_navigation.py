"""
Playwright-Based Web Navigation Service (Read-Only Guidance)
Provides voice-guided web navigation without form filling or data entry
"""

import os
import asyncio
import logging
from playwright.async_api import async_playwright, Browser, Page, Playwright
from typing import Dict, List, Optional, Any
import json

logger = logging.getLogger(__name__)

class PlaywrightNavigationService:
    def __init__(self):
        """Initialize Playwright navigation service."""
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.user_pages: Dict[str, Page] = {}  # user_id -> page mapping
        self.housing_authority_base = os.getenv("HOUSING_AUTHORITY_BASE_URL", "https://www.smcgov.org/housing")
        self.initialized = False
        
        # Site map for navigation - San Mateo County Housing Authority
        self.site_map = {
            "home": {
                "url": "https://www.smcgov.org/housing",
                "selectors": {
                    "main_content": "main, .content, .homepage",
                    "navigation": "nav, .navigation, .menu",
                    "services": ".services, .programs, h2, h3",
                    "contact": ".contact, .phone, .email"
                }
            },
            "inspection_requirements": {
                "url": "https://www.smcgov.org/housing/housing-choice-voucher-program",
                "selectors": {
                    "requirements_list": "main, .content, h2, h3, .inspection",
                    "checklist": ".checklist, h3, .requirements",
                    "documents": ".documents, .required, h3",
                    "contact": ".contact, .phone, .email"
                }
            },
            "inspection_scheduling": {
                "url": "https://www.smcgov.org/housing/housing-choice-voucher-program",
                "selectors": {
                    "schedule_form": "form, .contact, .schedule",
                    "contact_info": ".contact, .phone, .email",
                    "instructions": "main, .content, h3"
                }
            },
            "application": {
                "url": "https://www.smcgov.org/housing/housing-choice-voucher-program",
                "selectors": {
                    "application_info": "main, .content, .application",
                    "requirements": ".requirements, .eligibility, h3",
                    "waitlist": ".waitlist, .waiting, h3"
                }
            },
            "landlord_services": {
                "url": "https://www.smcgov.org/housing/landlords",
                "selectors": {
                    "landlord_info": "main, .content, h2, h3",
                    "payment_info": ".payment, .rent, h3",
                    "resources": ".resources, .forms, .documents"
                }
            },
            "contact": {
                "url": "https://www.smcgov.org/housing/contact-us",
                "selectors": {
                    "office_hours": ".hours, .office, h3",
                    "phone_numbers": ".phone, .contact, .number",
                    "locations": ".address, .location, .office",
                    "email": ".email, .contact"
                }
            },
            "home": {
                "url": "https://www.smcgov.org/housing",
                "selectors": {
                    "main_navigation": "nav, .navigation, .menu",
                    "services": ".services, .programs, h2",
                    "quick_links": ".quick-links, .shortcuts, .highlights"
                }
            },
            "rental_assistance": {
                "url": "https://www.smcgov.org/housing/rental-assistance",
                "selectors": {
                    "assistance_info": "main, .content, h2, h3",
                    "emergency_help": ".emergency, .assistance, .help",
                    "apply": ".apply, .application, form"
                }
            },
            "affordable_housing": {
                "url": "https://www.smcgov.org/housing/affordable-housing",
                "selectors": {
                    "housing_list": "main, .content, .housing",
                    "waitlist": ".waitlist, .waiting, .application",
                    "opportunities": ".opportunities, .available, h3"
                }
            },
            "project_sentinel": {
                "url": "https://www.smcgov.org/housing/project-sentinel-landlordtenant-questions-county-san-mateo",
                "selectors": {
                    "sentinel_info": "main, .content, h1, h2, h3",
                    "services": ".services, .mediation, .counseling",
                    "contact": ".contact, .phone, .email",
                    "resources": ".resources, .help, .assistance"
                }
            }
        }
    
    async def initialize(self):
        """Start Playwright browser instance."""
        if self.initialized:
            return
            
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,  # Run in background
                args=['--no-sandbox', '--disable-web-security', '--disable-features=VizDisplayCompositor']
            )
            self.initialized = True
            logger.info("Playwright navigation service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Playwright: {e}")
            self.initialized = False
    
    async def get_user_page(self, user_id: str) -> Optional[Page]:
        """Get or create a browser page for a user session."""
        if not self.initialized:
            await self.initialize()
            
        if not self.browser:
            logger.error("Browser not available")
            return None
            
        if user_id not in self.user_pages:
            try:
                page = await self.browser.new_page()
                # Set user agent
                await page.set_extra_http_headers({
                    'User-Agent': 'HousingAssistant-VoiceNavigation/1.0'
                })
                self.user_pages[user_id] = page
                logger.info(f"Created new page for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to create page for user {user_id}: {e}")
                return None
                
        return self.user_pages[user_id]
    
    async def navigate_to_page(self, user_id: str, page_key: str) -> Dict[str, Any]:
        """Navigate user's browser to a specific housing authority page."""
        page = await self.get_user_page(user_id)
        if not page:
            return {"success": False, "error": "Could not create browser page"}
        
        if page_key not in self.site_map:
            return {"success": False, "error": f"Unknown page: {page_key}"}
        
        url = self.site_map[page_key]["url"]
        
        try:
            logger.info(f"Navigating user {user_id} to {url}")
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for page to be fully loaded
            await page.wait_for_load_state('domcontentloaded')
            
            # Get page info for confirmation
            title = await page.title()
            current_url = page.url
            
            return {
                "success": True,
                "title": title,
                "url": current_url,
                "page_key": page_key,
                "message": f"Successfully navigated to {title}"
            }
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to navigate to {page_key}"
            }
    
    async def highlight_element(self, user_id: str, selector: str, duration: int = 5000) -> Dict[str, Any]:
        """Highlight a specific element on the page with visual emphasis."""
        page = await self.get_user_page(user_id)
        if not page:
            return {"success": False, "error": "No page available for user"}
        
        try:
            # Wait for element to be available
            await page.wait_for_selector(selector, timeout=5000)
            
            # Inject highlighting CSS and JavaScript
            highlight_script = f"""
            const elements = document.querySelectorAll('{selector}');
            if (elements.length > 0) {{
                const element = elements[0]; // Use first matching element
                
                // Create highlight overlay
                const overlay = document.createElement('div');
                overlay.id = 'voice-assistant-highlight-' + Date.now();
                overlay.className = 'voice-navigation-highlight';
                overlay.style.cssText = `
                    position: absolute;
                    background: rgba(255, 215, 0, 0.3);
                    border: 3px solid #FFD700;
                    border-radius: 8px;
                    z-index: 10000;
                    pointer-events: none;
                    animation: pulse 2s infinite;
                    box-shadow: 0 0 20px rgba(255, 215, 0, 0.5);
                    transition: all 0.3s ease;
                `;
                
                // Add pulse animation
                const style = document.createElement('style');
                style.textContent = `
                    @keyframes pulse {{
                        0% {{ transform: scale(1); opacity: 0.7; }}
                        50% {{ transform: scale(1.02); opacity: 1; }}
                        100% {{ transform: scale(1); opacity: 0.7; }}
                    }}
                `;
                document.head.appendChild(style);
                
                // Position overlay over element
                const rect = element.getBoundingClientRect();
                overlay.style.top = (rect.top + window.scrollY - 5) + 'px';
                overlay.style.left = (rect.left + window.scrollX - 5) + 'px';
                overlay.style.width = (rect.width + 10) + 'px';
                overlay.style.height = (rect.height + 10) + 'px';
                
                document.body.appendChild(overlay);
                
                // Scroll element into view smoothly
                element.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                
                // Remove highlight after duration
                setTimeout(() => {{
                    if (overlay.parentNode) {{
                        overlay.parentNode.removeChild(overlay);
                    }}
                    if (style.parentNode) {{
                        style.parentNode.removeChild(style);
                    }}
                }}, {duration});
                
                return {{
                    success: true,
                    elementText: element.textContent?.substring(0, 100) || '',
                    tagName: element.tagName
                }};
            }}
            return {{ success: false, reason: 'Element not found' }};
            """
            
            result = await page.evaluate(highlight_script)
            
            if result.get('success'):
                return {
                    "success": True,
                    "message": f"Highlighted element: {selector}",
                    "element_info": {
                        "text": result.get('elementText', ''),
                        "tag": result.get('tagName', '')
                    }
                }
            else:
                return {
                    "success": False,
                    "message": f"Element not found: {selector}",
                    "reason": result.get('reason', 'Unknown')
                }
                
        except Exception as e:
            logger.error(f"Failed to highlight element {selector}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to highlight element: {selector}"
            }
    
    async def show_guidance_overlay(self, user_id: str, selector: str, message: str, duration: int = 8000) -> Dict[str, Any]:
        """Show a guidance overlay with voice assistant instructions."""
        page = await self.get_user_page(user_id)
        if not page:
            return {"success": False, "error": "No page available for user"}
        
        try:
            await page.wait_for_selector(selector, timeout=5000)
            
            guidance_script = f"""
            const element = document.querySelector('{selector}');
            if (element) {{
                // Create guidance overlay
                const overlay = document.createElement('div');
                overlay.id = 'voice-guidance-overlay-' + Date.now();
                overlay.innerHTML = `
                    <div style="
                        background: linear-gradient(135deg, #2196F3, #1976D2);
                        color: white;
                        padding: 16px 20px;
                        border-radius: 12px;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                        font-size: 14px;
                        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                        max-width: 320px;
                        line-height: 1.5;
                        border: 1px solid rgba(255,255,255,0.2);
                    ">
                        <div style="display: flex; align-items: center; margin-bottom: 8px;">
                            <span style="font-size: 18px; margin-right: 8px;">🎤</span>
                            <strong>Voice Assistant</strong>
                        </div>
                        <div style="margin-bottom: 8px;">
                            {message}
                        </div>
                        <div style="
                            font-size: 12px;
                            opacity: 0.8;
                            font-style: italic;
                        ">
                            Tap anywhere to dismiss
                        </div>
                    </div>
                `;
                
                overlay.style.cssText = `
                    position: absolute;
                    z-index: 10001;
                    pointer-events: auto;
                    cursor: pointer;
                    animation: fadeInScale 0.3s ease-out;
                `;
                
                // Add animation styles
                const style = document.createElement('style');
                style.textContent = `
                    @keyframes fadeInScale {{
                        0% {{ opacity: 0; transform: scale(0.8) translateY(10px); }}
                        100% {{ opacity: 1; transform: scale(1) translateY(0); }}
                    }}
                `;
                document.head.appendChild(style);
                
                // Position near the target element
                const rect = element.getBoundingClientRect();
                const spaceBelow = window.innerHeight - rect.bottom;
                const spaceAbove = rect.top;
                
                if (spaceBelow > 150) {{
                    // Position below element
                    overlay.style.top = (rect.bottom + window.scrollY + 10) + 'px';
                }} else if (spaceAbove > 150) {{
                    // Position above element
                    overlay.style.top = (rect.top + window.scrollY - 120) + 'px';
                }} else {{
                    // Position to the side
                    overlay.style.top = (rect.top + window.scrollY) + 'px';
                }}
                
                overlay.style.left = Math.max(10, Math.min(
                    rect.left + window.scrollX,
                    window.innerWidth - 340
                )) + 'px';
                
                // Click to dismiss
                overlay.onclick = () => {{
                    overlay.remove();
                    style.remove();
                }};
                
                document.body.appendChild(overlay);
                
                // Auto-remove after duration
                setTimeout(() => {{
                    if (overlay.parentNode) {{
                        overlay.parentNode.removeChild(overlay);
                    }}
                    if (style.parentNode) {{
                        style.parentNode.removeChild(style);
                    }}
                }}, {duration});
                
                return true;
            }}
            return false;
            """
            
            success = await page.evaluate(guidance_script)
            
            return {
                "success": success,
                "message": f"Showed guidance for: {selector}" if success else f"Failed to show guidance for: {selector}"
            }
                
        except Exception as e:
            logger.error(f"Failed to show guidance overlay: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to show guidance: {selector}"
            }
    
    async def get_page_sections(self, user_id: str) -> Dict[str, Any]:
        """Get available sections on the current page for navigation guidance."""
        page = await self.get_user_page(user_id)
        if not page:
            return {"success": False, "error": "No page available for user"}
        
        try:
            title = await page.title()
            url = page.url
            
            # Get available sections for guidance
            sections = await page.evaluate("""
                Array.from(document.querySelectorAll('h1, h2, h3, h4, .section, .form-section, .requirements, .checklist, form')).map(el => ({
                    tag: el.tagName.toLowerCase(),
                    text: el.textContent?.trim().substring(0, 60) || '',
                    id: el.id || '',
                    className: el.className || '',
                    selector: el.id ? `#${el.id}` : (el.className ? `.${el.className.split(' ')[0]}` : null)
                })).filter(section => section.selector && section.text.length > 3);
            """)
            
            return {
                "success": True,
                "title": title,
                "url": url,
                "available_sections": sections[:10]  # Limit to first 10 sections
            }
        except Exception as e:
            logger.error(f"Failed to get page sections: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def close_user_session(self, user_id: str):
        """Clean up user's browser session."""
        if user_id in self.user_pages:
            try:
                await self.user_pages[user_id].close()
                del self.user_pages[user_id]
                logger.info(f"Closed browser session for user {user_id}")
            except Exception as e:
                logger.error(f"Error closing session for user {user_id}: {e}")
    
    async def cleanup(self):
        """Clean up all browser resources."""
        try:
            # Close all user pages
            for user_id in list(self.user_pages.keys()):
                await self.close_user_session(user_id)
            
            # Close browser
            if self.browser:
                await self.browser.close()
            
            # Stop playwright
            if self.playwright:
                await self.playwright.stop()
            
            self.initialized = False
            logger.info("Playwright navigation service cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

# Global navigation service instance
navigation_service = PlaywrightNavigationService()