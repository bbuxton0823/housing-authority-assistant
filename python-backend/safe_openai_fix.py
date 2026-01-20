#!/usr/bin/env python3
"""Safe OpenAI fix that doesn't break the SDK."""

import os
import sys
import locale
import inspect

def apply_safe_fix():
    """Apply safe Unicode fixes without breaking OpenAI SDK."""
    
    # 1. Set system locale and encoding
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, 'C.UTF-8')
        except locale.Error:
            pass
    
    # 2. Set environment variables
    os.environ['LANG'] = 'en_US.UTF-8'
    os.environ['LC_ALL'] = 'en_US.UTF-8'
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # 3. Ensure stdout/stderr use UTF-8
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    
    # 4. Safe httpx patching - only patch normalize function
    try:
        import httpx._models
        original_normalize = httpx._models._normalize_header_value
        
        def safe_normalize(value, encoding=None):
            """Safe normalize function with Unicode sanitization."""
            if isinstance(value, str):
                value = sanitize_unicode(value)
            try:
                return original_normalize(value, encoding or "utf-8")
            except UnicodeEncodeError:
                # If still fails, be more aggressive
                if isinstance(value, str):
                    value = value.encode('ascii', errors='replace').decode('ascii')
                return original_normalize(value, encoding or "utf-8")
        
        httpx._models._normalize_header_value = safe_normalize
        print("✓ Applied safe httpx Unicode fix")
        
    except Exception as e:
        print(f"! httpx patch failed: {e}")
    
    # 5. Patch agents SDK prompt
    try:
        import agents.extensions.handoff_prompt
        if hasattr(agents.extensions.handoff_prompt, 'RECOMMENDED_PROMPT_PREFIX'):
            original_prefix = agents.extensions.handoff_prompt.RECOMMENDED_PROMPT_PREFIX
            sanitized_prefix = sanitize_unicode(original_prefix)
            agents.extensions.handoff_prompt.RECOMMENDED_PROMPT_PREFIX = sanitized_prefix
            print("✓ Applied Agents SDK prompt Unicode fix")
    except Exception as e:
        print(f"! Agents SDK patch failed: {e}")
    
    # 6. Try to patch string encoding in the environment
    try:
        import codecs
        # Register a custom codec search function for ASCII encoding issues
        def custom_ascii_error_handler(error):
            """Custom error handler for ASCII encoding issues."""
            if isinstance(error, UnicodeEncodeError):
                # Replace problematic characters
                replacement = sanitize_unicode(error.object[error.start:error.end])
                return (replacement, error.end)
            return codecs.strict_errors(error)
        
        codecs.register_error('unicode_fix', custom_ascii_error_handler)
        print("✓ Registered custom Unicode error handler")
        
    except Exception as e:
        print(f"! Unicode handler registration failed: {e}")

def sanitize_unicode(text):
    """Replace problematic Unicode characters with ASCII equivalents."""
    if not isinstance(text, str):
        return text
    
    # Dictionary of Unicode replacements
    replacements = {
        '\u2011': '-',    # non-breaking hyphen (the main culprit!)
        '\u2013': '-',    # en dash
        '\u2014': '-',    # em dash
        '\u2010': '-',    # hyphen
        '\u00A0': ' ',    # non-breaking space
        '\u201C': '"',    # left double quotation mark
        '\u201D': '"',    # right double quotation mark
        '\u2018': "'",    # left single quotation mark
        '\u2019': "'",    # right single quotation mark
        '\u2026': '...',  # horizontal ellipsis
    }
    
    # Apply all replacements
    for unicode_char, replacement in replacements.items():
        text = text.replace(unicode_char, replacement)
    
    return text

if __name__ == "__main__":
    apply_safe_fix()