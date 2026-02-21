"""Utility functions for Celebrity Buzz Index"""
import re
import html
from datetime import datetime, timezone
from typing import Optional
from config.settings import TIER_CONFIG, BANNED_WORDS

def get_week_number() -> str:
    """Get current ISO week number as string for transfer window tracking"""
    now = datetime.now(timezone.utc)
    return f"{now.year}-W{now.isocalendar()[1]:02d}"

def get_dynamic_price(tier: str, buzz_score: float, name: str = "") -> float:
    """Calculate dynamic price based on tier, buzz score and news premium"""
    config = TIER_CONFIG.get(tier, TIER_CONFIG["D"])
    base = config["base_price"]
    min_price = config["min_price"]
    max_price = config["max_price"]
    
    # Apply buzz adjustment
    adjusted_buzz = buzz_score + config["buzz_adjustment"]
    
    # Calculate price based on buzz (normalized 0-100)
    buzz_factor = min(100, max(0, adjusted_buzz)) / 100
    price_range = max_price - min_price
    price = min_price + (price_range * buzz_factor)
    
    # News premium for hot celebs
    name_lower = name.lower() if name else ""
    news_boost = get_news_premium_boost(name_lower)
    price = price + news_boost
    
    # Ensure within bounds
    price = round(min(max_price + news_boost, max(min_price, price)), 1)
    
    return price

def get_news_premium_boost(name_lower: str) -> float:
    """Get news premium boost for trending celebrities"""
    # Hot celebs get a price boost
    HOT_CELEB_BOOSTS = {
        "taylor swift": 2.0,
        "kanye west": 1.5,
        "ye": 1.5,
        "elon musk": 1.5,
        "kim kardashian": 1.5,
        "meghan markle": 1.5,
        "harry": 1.0,
        "beyoncé": 1.0,
        "beyonce": 1.0,
        "trump": 1.5,
        "drake": 1.0,
        "rihanna": 1.0,
    }
    
    for celeb, boost in HOT_CELEB_BOOSTS.items():
        if celeb in name_lower:
            return boost
    return 0

def get_brown_bread_risk(age: int) -> str:
    """Calculate risk level for Brown Bread Watch based on age"""
    if age >= 90:
        return "critical"
    elif age >= 85:
        return "high"
    elif age >= 80:
        return "elevated"
    elif age >= 70:
        return "moderate"
    else:
        return "low"

def contains_banned_words(text: str) -> bool:
    """Check if text contains any banned/profane words"""
    if not text:
        return False
    
    text_lower = text.lower()
    # Remove spaces and common substitutions
    text_clean = text_lower.replace(" ", "").replace(".", "").replace("_", "").replace("-", "")
    
    # Also check with numbers -> letters (l33t speak)
    text_leet = text_clean.replace("0", "o").replace("1", "i").replace("3", "e").replace("4", "a").replace("5", "s").replace("7", "t")
    
    for word in BANNED_WORDS:
        word_clean = word.replace(" ", "")
        if word_clean in text_clean or word_clean in text_leet:
            return True
        # Also check original with spaces
        if word in text_lower:
            return True
    
    return False

def decode_html_entities(text: str) -> str:
    """Decode HTML entities like &amp; &quot; etc"""
    if not text:
        return text
    return html.unescape(text)

# Celebrity name aliases for duplicate detection
CELEBRITY_ALIASES = {
    # Royals
    "catherine, princess of wales": ["kate middleton", "catherine middleton", "duchess of cambridge", "princess kate"],
    "william, prince of wales": ["prince william", "duke of cambridge", "prince william windsor"],
    "charles iii": ["king charles", "prince charles", "king charles iii"],
    "camilla, queen consort": ["queen camilla", "camilla parker bowles", "duchess of cornwall"],
    "prince harry, duke of sussex": ["prince harry", "harry windsor", "duke of sussex"],
    "meghan, duchess of sussex": ["meghan markle", "duchess of sussex"],
    "prince george of wales": ["prince george"],
    "princess charlotte of wales": ["princess charlotte"],
    "prince louis of wales": ["prince louis"],
    "prince archie of sussex": ["archie mountbatten-windsor", "archie harrison"],
    "princess lilibet of sussex": ["lilibet mountbatten-windsor", "lilibet diana"],
    
    # Other common aliases
    "kanye west": ["ye", "kanye"],
    "sean combs": ["diddy", "puff daddy", "p. diddy"],
    "dwayne johnson": ["the rock"],
    "stefani germanotta": ["lady gaga"],
    "robyn fenty": ["rihanna"],
    "beyoncé knowles": ["beyonce", "beyoncé"],
}

def normalize_celebrity_name(name: str) -> str:
    """Normalize a celebrity name for comparison"""
    return name.lower().strip()

def are_same_celebrity(name1: str, name2: str) -> bool:
    """Check if two names refer to the same celebrity"""
    n1 = normalize_celebrity_name(name1)
    n2 = normalize_celebrity_name(name2)
    
    # Direct match
    if n1 == n2:
        return True
    
    # Check aliases
    for canonical, aliases in CELEBRITY_ALIASES.items():
        all_names = [canonical.lower()] + [a.lower() for a in aliases]
        if n1 in all_names and n2 in all_names:
            return True
    
    return False

def get_canonical_name(name: str) -> Optional[str]:
    """Get the canonical (official) name for a celebrity"""
    name_lower = normalize_celebrity_name(name)
    
    for canonical, aliases in CELEBRITY_ALIASES.items():
        all_names = [canonical.lower()] + [a.lower() for a in aliases]
        if name_lower in all_names:
            return canonical.title()
    
    return None
