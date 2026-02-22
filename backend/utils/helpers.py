"""
Utility helper functions
"""
import unicodedata
import html
import re
import logging

logger = logging.getLogger("server")

def normalize_text(text: str) -> str:
    """Remove accents and normalize text for matching"""
    normalized = unicodedata.normalize('NFD', text)
    return ''.join(c for c in normalized if not unicodedata.combining(c)).lower()

def decode_html_entities(text: str) -> str:
    """Decode HTML entities like &amp; &#8217; etc. to readable text"""
    if not text:
        return text
    decoded = html.unescape(text)
    decoded = decoded.replace('â€™', "'").replace('â€"', "—").replace('â€œ', '"').replace('â€', '"')
    return decoded

def sanitize_team_name(name: str, banned_words: list) -> tuple:
    """
    Check if team name contains banned words. Returns (is_valid, sanitized_name).
    """
    name_lower = name.lower()
    for word in banned_words:
        if word in name_lower:
            return False, None
    # Basic sanitization - remove excessive special chars
    sanitized = re.sub(r'[^\w\s\-\'\.]+', '', name)
    sanitized = ' '.join(sanitized.split())  # Normalize whitespace
    if len(sanitized) < 2:
        return False, None
    if len(sanitized) > 50:
        sanitized = sanitized[:50]
    return True, sanitized
