from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import httpx
import json
import re
import unicodedata
import html
import random
from emergentintegrations.llm.chat import LlmChat, UserMessage

def normalize_text(text: str) -> str:
    """Remove accents and normalize text for matching"""
    # Normalize to decomposed form (separate base characters from accents)
    normalized = unicodedata.normalize('NFD', text)
    # Remove combining characters (accents)
    return ''.join(c for c in normalized if not unicodedata.combining(c)).lower()

def decode_html_entities(text: str) -> str:
    """Decode HTML entities like &amp; &#8217; etc. to readable text"""
    if not text:
        return text
    # Decode HTML entities
    decoded = html.unescape(text)
    # Clean up any remaining issues
    decoded = decoded.replace('â€™', "'").replace('â€"', "—").replace('â€œ', '"').replace('â€', '"')
    return decoded

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# LLM API Key
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Banned words for team names (racist, offensive)
BANNED_WORDS = [
    "nigger", "nigga", "faggot", "fag", "retard", "spic", "chink", "gook", 
    "kike", "wetback", "beaner", "coon", "darkie", "paki", "raghead", 
    "cracker", "honky", "nazi", "hitler", "kkk", "n1gger", "n1gga",
    "racist", "racism", "white power", "white supremacy", "heil", 
    "jew", "jews", "holocaust", "aryan", "fuhrer", "reich",
    "slave", "slavery", "lynch", "lynching", "genocide"
]

# High-profile celebrities with boosted base prices (controversial/newsworthy)
CONTROVERSIAL_CELEBS = {
    "prince andrew": 12,  # Always in news
    "meghan markle": 10,
    "prince harry": 10,
    "katie price": 8,
    "kanye west": 12,
    "elon musk": 15,
    "donald trump": 15,
    "boris johnson": 10,
}

# ==================== MODELS ====================

class Celebrity(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    bio: str = ""
    image: str = ""
    category: str = ""
    wiki_url: str = ""
    buzz_score: float = 0.0
    price: int = 5
    tier: str = "D"  # A, B, C, or D list
    news: List[dict] = []
    page_views: int = 0
    is_deceased: bool = False  # For brown bread bonus
    birth_year: int = 0  # For brown bread watch
    age: int = 0  # Calculated age
    times_picked: int = 0  # Track popularity
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CelebritySearch(BaseModel):
    name: str

class TeamCelebrity(BaseModel):
    celebrity_id: str
    name: str
    image: str
    category: str
    price: int
    buzz_score: float
    tier: str = "D"
    added_at: str = ""

# Team customization options
TEAM_COLORS = [
    {"id": "pink", "name": "Hot Pink", "hex": "#FF0099"},
    {"id": "cyan", "name": "Electric Blue", "hex": "#00F0FF"},
    {"id": "gold", "name": "Gold", "hex": "#FFD700"},
    {"id": "purple", "name": "Royal Purple", "hex": "#8B5CF6"},
    {"id": "red", "name": "Fire Red", "hex": "#EF4444"},
    {"id": "green", "name": "Emerald", "hex": "#10B981"},
    {"id": "orange", "name": "Sunset Orange", "hex": "#F97316"},
    {"id": "white", "name": "Classic White", "hex": "#FFFFFF"},
]

TEAM_ICONS = [
    {"id": "star", "name": "Star", "emoji": "⭐"},
    {"id": "crown", "name": "Crown", "emoji": "👑"},
    {"id": "fire", "name": "Fire", "emoji": "🔥"},
    {"id": "lightning", "name": "Lightning", "emoji": "⚡"},
    {"id": "rocket", "name": "Rocket", "emoji": "🚀"},
    {"id": "diamond", "name": "Diamond", "emoji": "💎"},
    {"id": "skull", "name": "Skull", "emoji": "💀"},
    {"id": "ghost", "name": "Ghost", "emoji": "👻"},
    {"id": "alien", "name": "Alien", "emoji": "👽"},
    {"id": "robot", "name": "Robot", "emoji": "🤖"},
    {"id": "unicorn", "name": "Unicorn", "emoji": "🦄"},
    {"id": "dragon", "name": "Dragon", "emoji": "🐉"},
]

class UserTeam(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    team_name: str = "My Team"
    team_color: str = "pink"  # Default color
    team_icon: str = "star"   # Default icon
    budget_remaining: int = 50
    total_points: float = 0.0
    brown_bread_bonus: float = 0.0  # Points from deceased celebs
    celebrities: List[TeamCelebrity] = []
    transfers_this_week: int = 0
    last_transfer_reset: str = ""
    badges: List[dict] = []  # Earned badges
    weekly_wins: int = 0  # Number of weekly wins
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TeamCreate(BaseModel):
    team_name: str = "My Team"

class TeamCustomize(BaseModel):
    team_id: str
    team_name: str = None
    team_color: str = None
    team_icon: str = None

class AddToTeam(BaseModel):
    team_id: str
    celebrity_id: str

class TransferRequest(BaseModel):
    team_id: str
    sell_celebrity_id: str
    buy_celebrity_id: str

class LeaderboardEntry(BaseModel):
    team_id: str
    team_name: str
    total_points: float
    celebrity_count: int
    brown_bread_bonus: float = 0.0

class AutocompleteResult(BaseModel):
    name: str
    description: str
    image: str
    estimated_tier: str
    estimated_price: int

# ==================== LEAGUE MODELS ====================

def generate_league_code() -> str:
    """Generate a 6-character league invite code"""
    import random
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

class League(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    code: str = Field(default_factory=generate_league_code)
    owner_team_id: str  # Team that created the league
    team_ids: List[str] = []  # Teams in this league
    max_teams: int = 20
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LeagueCreate(BaseModel):
    name: str
    team_id: str  # The creating team

class LeagueJoin(BaseModel):
    code: str
    team_id: str

# ==================== BADGE SYSTEM ====================

# Available badges
BADGES = {
    "weekly_winner": {
        "id": "weekly_winner",
        "name": "Weekly Champion",
        "icon": "🏆",
        "description": "Won a weekly league competition",
        "color": "#FFD700"
    },
    "first_pick": {
        "id": "first_pick",
        "name": "Trendsetter",
        "icon": "⚡",
        "description": "First to pick a celebrity who then went viral",
        "color": "#FF0099"
    },
    "brown_bread": {
        "id": "brown_bread",
        "name": "Grim Reaper",
        "icon": "💀",
        "description": "Earned the Brown Bread Bonus",
        "color": "#8B5CF6"
    },
    "controversy_king": {
        "id": "controversy_king",
        "name": "Controversy King",
        "icon": "🔥",
        "description": "Picked 3+ controversial celebrities",
        "color": "#EF4444"
    },
    "a_lister": {
        "id": "a_lister",
        "name": "A-List Club",
        "icon": "⭐",
        "description": "Full team of A-list celebrities",
        "color": "#00F0FF"
    },
    "league_champion": {
        "id": "league_champion",
        "name": "League Legend",
        "icon": "👑",
        "description": "Won 3+ weeks in your league",
        "color": "#FFD700"
    }
}

class Badge(BaseModel):
    id: str
    earned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    league_id: str = ""  # Optional - which league it was earned in

# ==================== HELPER FUNCTIONS ====================

def contains_banned_words(text: str) -> bool:
    """Check if text contains banned/offensive words"""
    text_lower = text.lower()
    # Remove spaces and special chars for checking
    text_clean = re.sub(r'[^a-z0-9]', '', text_lower)
    
    for word in BANNED_WORDS:
        if word in text_lower or word in text_clean:
            return True
    return False

def get_week_number() -> str:
    """Get current week identifier for transfer window"""
    now = datetime.now(timezone.utc)
    return f"{now.year}-W{now.isocalendar()[1]}"

def is_transfer_window_open() -> dict:
    """Check if transfer window is open (Saturday 12pm GMT for 24 hours)"""
    now = datetime.now(timezone.utc)
    
    # Transfer window opens Saturday 12:00 GMT
    # Find this Saturday's window
    days_since_saturday = (now.weekday() - 5) % 7  # Saturday is 5
    
    # Calculate when the current/next window starts
    if now.weekday() == 5:  # It's Saturday
        window_start = now.replace(hour=12, minute=0, second=0, microsecond=0)
        if now < window_start:
            # Before 12pm Saturday, use last Saturday
            window_start = window_start - timedelta(days=7)
    elif now.weekday() == 6:  # Sunday
        # Window started yesterday at 12pm
        window_start = (now - timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0)
    else:
        # Window was last Saturday at 12pm
        window_start = (now - timedelta(days=days_since_saturday)).replace(hour=12, minute=0, second=0, microsecond=0)
    
    window_end = window_start + timedelta(hours=24)
    
    is_open = window_start <= now < window_end
    
    # Calculate next window
    if is_open:
        next_window = window_start + timedelta(days=7)
        time_remaining = window_end - now
        hours_remaining = int(time_remaining.total_seconds() // 3600)
        mins_remaining = int((time_remaining.total_seconds() % 3600) // 60)
        status_text = f"OPEN - {hours_remaining}h {mins_remaining}m left"
    else:
        # Calculate time until next Saturday 12pm
        days_until_saturday = (5 - now.weekday()) % 7
        if days_until_saturday == 0 and now.hour >= 12:
            days_until_saturday = 7
        next_window = (now + timedelta(days=days_until_saturday)).replace(hour=12, minute=0, second=0, microsecond=0)
        time_until = next_window - now
        days_until = time_until.days
        hours_until = int((time_until.total_seconds() % 86400) // 3600)
        if days_until > 0:
            status_text = f"Opens in {days_until}d {hours_until}h"
        else:
            status_text = f"Opens in {hours_until}h"
    
    return {
        "is_open": is_open,
        "status": status_text,
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
        "next_window": next_window.isoformat() if not is_open else None
    }

def get_controversial_price_boost(name: str) -> int:
    """Get price boost for controversial/newsworthy celebs"""
    name_lower = name.lower()
    for celeb, boost in CONTROVERSIAL_CELEBS.items():
        if celeb in name_lower:
            return boost
    return 0

def extract_birth_year_from_bio(bio: str) -> int:
    """Extract birth year from Wikipedia bio text"""
    if not bio:
        return 0
    
    # Common patterns: "born January 15, 1945", "born 1945", "(born 1945)", "b. 1945"
    patterns = [
        r'\(born\s+(?:\w+\s+\d{1,2},?\s+)?(\d{4})\)',  # (born January 15, 1945)
        r'born\s+(?:\w+\s+\d{1,2},?\s+)?(\d{4})',       # born January 15, 1945
        r'\(b\.\s*(\d{4})\)',                            # (b. 1945)
        r'\((\d{4})\s*[-–]\s*\)',                        # (1945 - ) for living people
        r'\((\d{4})\s*[-–]',                             # (1945– for living people
    ]
    
    for pattern in patterns:
        match = re.search(pattern, bio, re.IGNORECASE)
        if match:
            year = int(match.group(1))
            # Sanity check - birth year should be reasonable
            if 1900 <= year <= 2010:
                return year
    
    return 0

def calculate_age(birth_year: int) -> int:
    """Calculate age from birth year"""
    if birth_year == 0:
        return 0
    current_year = datetime.now(timezone.utc).year
    return current_year - birth_year

def get_brown_bread_risk(age: int) -> str:
    """Get risk level based on age"""
    if age >= 90:
        return "critical"  # 🔴
    elif age >= 80:
        return "high"      # 🟠
    elif age >= 70:
        return "elevated"  # 🟡
    elif age >= 60:
        return "moderate"  # 🟢
    return "low"

# ==================== CELEBRITY CATEGORIES ====================
CATEGORIES = [
    {"id": "movie_stars", "name": "Movie Stars", "icon": "film"},
    {"id": "tv_actors", "name": "TV Actors", "icon": "tv"},
    {"id": "musicians", "name": "Musicians", "icon": "music"},
    {"id": "athletes", "name": "Athletes", "icon": "trophy"},
    {"id": "royals", "name": "Royals", "icon": "crown"},
    {"id": "reality_tv", "name": "Reality TV", "icon": "star"},
    {"id": "other", "name": "Other", "icon": "users"},
]

# Pre-defined trending celebrities per category (UK & International mix)
TRENDING_CELEBRITIES = {
    "movie_stars": ["Tom Holland", "Florence Pugh", "Idris Elba", "Emily Blunt", "Dev Patel"],
    "tv_actors": ["Jenna Coleman", "Jodie Comer", "Richard Madden", "Ncuti Gatwa", "Olivia Colman"],
    "musicians": ["Dua Lipa", "Ed Sheeran", "Adele", "Harry Styles", "Stormzy"],
    "athletes": ["Harry Kane", "Marcus Rashford", "Emma Raducanu", "Lewis Hamilton", "Raheem Sterling"],
    "royals": ["Prince William", "Kate Middleton", "Prince Harry", "Meghan Markle", "Prince Andrew"],
    "reality_tv": ["Katie Price", "Gemma Collins", "Pete Wicks", "Joey Essex", "Sam Faiers"],
    "other": ["David Beckham", "Gordon Ramsay", "Bear Grylls", "Jeremy Clarkson", "James Corden"],
}

# HOT CELEBS POOL - Large pool to randomly select from on each refresh
HOT_CELEBS_POOL = [
    # Royals
    {"name": "Prince Andrew", "reason": "Royal scandal & legal battles", "tier": "A", "category": "royals"},
    {"name": "Meghan Markle", "reason": "Netflix & Royal drama", "tier": "A", "category": "royals"},
    {"name": "Prince Harry", "reason": "Spare memoir revelations", "tier": "A", "category": "royals"},
    {"name": "Kate Middleton", "reason": "Royal duties & fashion", "tier": "A", "category": "royals"},
    {"name": "King Charles III", "reason": "Royal family head", "tier": "A", "category": "royals"},
    # Musicians
    {"name": "Kanye West", "reason": "Controversy & headlines", "tier": "A", "category": "musicians"},
    {"name": "Taylor Swift", "reason": "Eras Tour & awards", "tier": "A", "category": "musicians"},
    {"name": "Beyoncé", "reason": "Renaissance & Grammys", "tier": "A", "category": "musicians"},
    {"name": "Drake", "reason": "Music & feuds", "tier": "A", "category": "musicians"},
    {"name": "Rihanna", "reason": "Fenty & fashion empire", "tier": "A", "category": "musicians"},
    {"name": "Ed Sheeran", "reason": "Tours & legal battles", "tier": "A", "category": "musicians"},
    {"name": "Adele", "reason": "Vegas residency", "tier": "A", "category": "musicians"},
    # Tech/Business
    {"name": "Elon Musk", "reason": "Tech & politics headlines", "tier": "A", "category": "other"},
    {"name": "Mark Zuckerberg", "reason": "Meta & AI news", "tier": "A", "category": "other"},
    {"name": "Jeff Bezos", "reason": "Space & business", "tier": "A", "category": "other"},
    # Politicians
    {"name": "Donald Trump", "reason": "Political & legal news", "tier": "A", "category": "other"},
    {"name": "Joe Biden", "reason": "Political headlines", "tier": "A", "category": "other"},
    # Reality TV/UK
    {"name": "Katie Price", "reason": "Tabloid regular", "tier": "B", "category": "reality_tv"},
    {"name": "Holly Willoughby", "reason": "TV drama", "tier": "B", "category": "tv_actors"},
    {"name": "Phillip Schofield", "reason": "TV scandal", "tier": "B", "category": "tv_actors"},
    {"name": "Gemma Collins", "reason": "Reality star antics", "tier": "C", "category": "reality_tv"},
    {"name": "Kerry Katona", "reason": "Tabloid stories", "tier": "C", "category": "reality_tv"},
    # Actors
    {"name": "Tom Cruise", "reason": "Mission Impossible & stunts", "tier": "A", "category": "movie_stars"},
    {"name": "Leonardo DiCaprio", "reason": "Film & dating life", "tier": "A", "category": "movie_stars"},
    {"name": "Jennifer Lawrence", "reason": "Film & fashion", "tier": "A", "category": "movie_stars"},
    {"name": "Brad Pitt", "reason": "Films & personal life", "tier": "A", "category": "movie_stars"},
    {"name": "Angelina Jolie", "reason": "Humanitarian & acting", "tier": "A", "category": "movie_stars"},
    # Sports
    {"name": "Cristiano Ronaldo", "reason": "Football & brand deals", "tier": "A", "category": "athletes"},
    {"name": "David Beckham", "reason": "Business & family", "tier": "A", "category": "athletes"},
    {"name": "Lewis Hamilton", "reason": "F1 & fashion", "tier": "A", "category": "athletes"},
]

def get_random_hot_celebs(count: int = 8) -> list:
    """Get a random selection of hot celebs from the pool"""
    # Ensure we have a good mix of tiers
    a_list = [c for c in HOT_CELEBS_POOL if c["tier"] == "A"]
    b_list = [c for c in HOT_CELEBS_POOL if c["tier"] in ["B", "C"]]
    
    # Pick mostly A-list with some B/C list
    selected = random.sample(a_list, min(6, len(a_list)))
    if b_list:
        selected += random.sample(b_list, min(2, len(b_list)))
    
    random.shuffle(selected)
    return selected[:count]

# A-list indicators (keywords that suggest high fame)
A_LIST_INDICATORS = ["oscar", "grammy", "emmy", "golden globe", "bafta", "world cup winner", 
                      "billion", "legendary", "iconic", "superstar", "megastar", "one of the most",
                      "best-selling", "highest-paid", "most famous", "world record"]
B_LIST_INDICATORS = ["award-winning", "acclaimed", "successful", "popular", "well-known", 
                      "million", "chart-topping", "hit", "starring", "lead role"]
C_LIST_INDICATORS = ["known for", "appeared in", "featured", "contestant", "participant"]

# ==================== HELPER FUNCTIONS ====================

async def fetch_wikipedia_autocomplete(query: str) -> List[dict]:
    """Search Wikipedia for celebrity suggestions - returns ONE result per person only"""
    try:
        headers = {"User-Agent": "CelebrityBuzzIndex/1.0 (contact@example.com)"}
        query_lower = query.lower().strip()
        query_parts = query_lower.split()  # Split query into words for matching
        
        logger.info(f"Autocomplete search for: {query}, parts: {query_parts}")
        
        async with httpx.AsyncClient() as client:
            # Use Wikipedia search API for better results with descriptions
            url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&srlimit=25&format=json"
            response = await client.get(url, timeout=5.0, headers=headers)
            if response.status_code == 200:
                data = response.json()
                search_results = data.get("query", {}).get("search", [])
                
                # Keywords that indicate this is NOT a person - FILTER OUT from title
                non_person_title_keywords = [
                    "filmography", "discography", "bibliography", "awards", "album", 
                    "song", "band", "tv series", "television series", "movie", "film",
                    "list of", "category:", "template:", "wikipedia:", "soundtrack",
                    "video game", "book", "novel", "tour", "concert", "episode",
                    "podcast", "show", "series", "programme", "program", "season",
                    "city", "town", "village", "municipality", "district", "commune",
                    "company", "single", "ep", "videography", "christmas special",
                    "fc", "cf", "afc", "united", "club", "team", "stadium", "records",
                    "child", "montana", "potter", "etc", "good girl", "sasha fierce",
                    "cowboy carter", "future nostalgia", "radical optimism", "gimme more",
                    "jean", "is paris", "this is", "agreement", "métro", "metro",
                    "race", "marathon", "rally", "championship", "cup", "trophy",
                    "brest", "event", "cycling", "festival", "award", "prize",
                    "airport", "station", "hotel", "resort", "beach", "island",
                    "mountain", "river", "park", "museum", "gallery", "cathedral",
                    "church", "school", "university", "college", "hospital",
                    "haunted", "haunt", "ghost", "location", "place", "site",
                    "capital", "county", "region", "province", "state", "country",
                    # Movies and TV shows
                    "cop", "90210", "hills", "housewives", "real housewives",
                    "ninja", "turtles", "wars", "trek", "rings", "thrones",
                    # Places - more comprehensive
                    "beverly hills", "hollywood", "manhattan", "brooklyn",
                    "heights", "township", "valley", "street", "road", "avenue",
                    "neighborhood", "neighbourhood", "suburb", "area", "territory",
                    "border", "crossing", "harbor", "harbour", "bay", "lake",
                    "forest", "wood", "woods", "gardens", "square", "plaza"
                ]
                
                # Known location/city names to always filter out
                known_locations = [
                    # European cities
                    "mariehamn", "helsinki", "stockholm", "oslo", "copenhagen",
                    "london", "paris", "berlin", "rome", "madrid", "amsterdam",
                    "dublin", "lisbon", "vienna", "prague", "warsaw", "brussels",
                    "zurich", "geneva", "manchester", "birmingham", "glasgow",
                    "edinburgh", "liverpool", "leeds", "cardiff", "belfast",
                    # US cities
                    "new york", "los angeles", "chicago", "houston", "phoenix",
                    "beverly hills", "hollywood", "malibu", "miami", "las vegas",
                    "san francisco", "seattle", "boston", "atlanta", "dallas",
                    "denver", "detroit", "philadelphia", "san diego", "portland",
                    # Areas/neighborhoods that match common names
                    "leonard", "florence", "georgia", "victoria", "regina",
                    "charlotte", "austin", "jackson", "lincoln", "madison",
                    "hamilton", "nelson", "clinton", "jefferson", "washington",
                    "kennedy", "roosevelt", "harrison", "taylor", "grant",
                    # Countries
                    "france", "germany", "italy", "spain", "portugal", "greece",
                    "poland", "russia", "china", "japan", "india", "brazil",
                    "canada", "australia", "mexico", "argentina", "chile"
                ]
                
                # Known team/club patterns
                team_patterns = ["ifk", "afc", "bfc", "cfc", "dfc", "fc ", " fc", "united", "city", "rovers", "athletic"]
                
                results = []
                seen_base_names = set()
                
                pass  # Results received
                
                for item in search_results:
                    title = item.get("title", "")
                    snippet = item.get("snippet", "").lower()
                    title_lower = title.lower()
                    title_normalized = normalize_text(title)  # Remove accents for matching
                    
                    # CRITICAL: The search query must appear in the person's actual NAME
                    # This prevents returning people who are just associated with the query
                    title_words = title_normalized.split()
                    query_in_name = any(
                        qpart in title_normalized or 
                        any(qpart in word for word in title_words)
                        for qpart in query_parts
                    )
                    if not query_in_name:
                        continue
                    
                    # Skip known location names
                    if title_lower in known_locations:
                        continue
                    
                    # Skip sports teams/clubs
                    if any(pattern in title_lower for pattern in team_patterns):
                        continue
                    
                    # Skip if title contains non-person keywords
                    if any(kw in title_lower for kw in non_person_title_keywords):
                        continue
                    
                    # Skip if title has dashes with location patterns (Paris–Brest–Paris)
                    if "–" in title or "—" in title:
                        continue
                    
                    # Skip if title has parentheses UNLESS it's a role descriptor like (musician), (actor)
                    if "(" in title:
                        # Allow if parentheses contain role descriptors
                        paren_content = title.split("(")[1].split(")")[0].lower() if ")" in title else ""
                        allowed_roles = ["musician", "actor", "actress", "singer", "rapper", "footballer",
                                        "politician", "presenter", "comedian", "director", "writer",
                                        "athlete", "businessman", "model", "chef", "host", "dancer",
                                        "duke", "duchess", "prince", "princess", "royal", "queen", "king"]
                        if not any(role in paren_content for role in allowed_roles):
                            continue
                    
                    # Skip titles with colons (usually shows, specials, etc.)
                    if ":" in title:
                        pass  # Filtered out
                        continue
                    
                    # Skip titles with commas (usually "Place, Place" patterns)
                    if "," in title:
                        pass  # Filtered out
                        continue
                    
                    # Skip titles with ampersands (usually TV shows like "Ginny & Georgia")
                    if "&" in title or " and " in title_lower:
                        pass  # Filtered out
                        continue
                    
                    # Skip titles starting with "The" (usually shows, bands, etc.)
                    if title_lower.startswith("the "):
                        pass  # Filtered out
                        continue
                    
                    # Skip titles starting with "For " (usually songs, albums)
                    if title_lower.startswith("for "):
                        pass  # Filtered out
                        continue
                    
                    # Skip plurals that are likely nationalities/groups (Georgians, Americans, etc.)
                    if len(title.split()) == 1 and title_lower.endswith("ians"):
                        pass  # Filtered out
                        continue
                    
                    # Skip if same word repeated (like "Paris Paris", "Simon Simon")
                    words = title.split()
                    if len(words) >= 2 and words[0].lower() == words[1].lower():
                        pass  # Filtered out
                        continue
                    
                    # Skip single word or too many words
                    if len(words) < 1 or len(words) > 4:
                        pass  # Filtered out
                        continue
                    
                    # Allow single-word names if they have accents (like Beyoncé, Rihanna)
                    # For multi-word names, check capitalization
                    if len(words) > 1:
                        # Name should look like a proper name (each word capitalized)
                        if not all(word[0].isupper() for word in words if word and word[0].isalpha()):
                            pass  # Filtered out
                            continue
                    
                    # Check for duplicates - use first two words as base name
                    words = title.split()
                    base_name = " ".join(words[:2]).lower() if len(words) >= 2 else title.lower()
                    if base_name in seen_base_names:
                        pass  # Filtered out
                        continue
                    seen_base_names.add(base_name)
                    
                    pass  # Fetching
                    
                    # Get full page summary for this person
                    try:
                        summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}"
                        summary_response = await client.get(summary_url, timeout=3.0, headers=headers)
                        pass  # Got summary
                        if summary_response.status_code == 200:
                            summary_data = summary_response.json()
                            desc = summary_data.get("extract", "")
                            image = summary_data.get("thumbnail", {}).get("source", "")
                            page_type = summary_data.get("type", "")
                            pass  # Page type check
                            
                            # Skip if not a standard article (could be disambiguation)
                            if page_type != "standard":
                                continue
                            
                            # Check description for person keywords
                            desc_lower = desc.lower()
                            
                            # Skip if description STARTS with non-person phrases (albums, films, etc.)
                            skip_start_phrases = [
                                "is a fictional character", "is a character in",
                                "is an album", "is the album", "is a studio album",
                                "is the debut", "is the second", "is the third", "is the fourth",
                                "is the fifth", "is the sixth", "is the seventh", "is the eighth",
                                "is the ninth", "is the tenth", "is the eleventh", "is the twelfth",
                                "is a single", "is a song", "is an ep",
                                "is a soundtrack", "is an ost",
                                "is a television series", "is a tv series", "is a sitcom",
                                "is a drama series", "is a reality", "is an american television",
                                "is a video game", "is a film", "is a movie",
                                "is a novel", "is a book", "is a band", "is a musical group",
                                "is a rock band", "is a pop group", "is a hip hop group",
                                "is a village", "is a city", "is a town", "is a municipality",
                                "is a district", "is a beach", "is an island", "is a resort",
                                "is a hotel", "is an airport", "is located in",
                                "was a fictional", "was a character", "was an album",
                                "was a television", "was a film", "was a band",
                                "studio album by", "collaborative album", "compilation album",
                                "is a long-distance", "is a cycling", "is a race", "is a marathon",
                                "is an annual", "is a sporting", "is a professional cycling",
                                "is a haunted", "is a location", "is a place", "is a building",
                                "is a nightclub", "is a restaurant", "is a bar", "is a pub",
                                # More facility/building types
                                "is a prison", "is a penitentiary", "is a correctional",
                                "is a supermax", "is a maximum-security", "is a high-security",
                                "is a federal", "is a state prison", "is a jail",
                                "united states penitentiary", "administrative maximum",
                                "is a hospital", "is a medical center", "is a clinic"
                            ]
                            
                            # Check if description starts with any skip phrase
                            should_skip = False
                            for phrase in skip_start_phrases:
                                # Check if description starts with the phrase
                                if desc_lower.startswith(phrase):
                                    should_skip = True
                                    break
                                # Check if phrase appears early but as complete words (not substring)
                                phrase_with_space = f" {phrase}"
                                if phrase_with_space in desc_lower[:150]:
                                    # Make sure it's not part of a larger word
                                    idx = desc_lower[:150].find(phrase_with_space)
                                    end_idx = idx + len(phrase_with_space)
                                    # Check if it ends at a word boundary (space, period, comma, or end)
                                    if end_idx >= len(desc_lower[:150]) or desc_lower[end_idx] in ' .,;:!?)':
                                        should_skip = True
                                        break
                            
                            # Also check for patterns like "is a [year] ... film"
                            if re.search(r'is a \d{4}.*?(film|movie|series|show|album|song|book|novel)', desc_lower[:200]):
                                should_skip = True
                            
                            # Check for university/school/institute patterns
                            if re.search(r'is a (public|private|research)?.*(university|college|institute|school)', desc_lower[:150]):
                                should_skip = True
                            
                            if should_skip:
                                pass  # Filtered out
                                continue
                            
                            # Additional filter for non-person entities (plants, animals, objects, locations)
                            non_person_description_keywords = [
                                "is a genus", "is a species", "is a family of", "is a type of",
                                "is a plant", "is a tree", "is a flower", "is a shrub",
                                "is a bird", "is a fish", "is a mammal", "is an animal",
                                "is a guitar", "is an instrument", "is a car", "is a vehicle",
                                "is a brand", "is a company", "is a product", "is a software",
                                "is a website", "is a game", "is an app", "flowering plants",
                                "is a genus of", "are a genus", "is a common name",
                                "is the capital", "is a capital", "is the largest city",
                                "is a seaport", "is a port", "is located on", "is situated",
                                "with a population", "inhabitants", "square kilometres",
                                "square miles", "administrative centre",
                                "is a football club", "is a professional football", "is a finnish",
                                "is a spanish", "is a german", "is a french", "is a english",
                                "football club", "soccer club", "basketball team", "hockey team",
                                "baseball team", "plays in the",
                                # More location keywords
                                "is an area", "is a suburb", "is a neighborhood", "is a neighbourhood",
                                "is a region", "is a territory", "is a census", "is a county",
                                "is a borough", "is a parish", "is a locality", "is a postal",
                                "is a residential", "is a commercial", "is a mixed-use",
                                "metropolitan area", "urban area", "incorporated city",
                                "unincorporated community", "census-designated",
                                "within the city", "in the city of", "located in the",
                                "is a neighborhood in", "is an area of", "is a suburb of"
                            ]
                            
                            if any(kw in desc_lower for kw in non_person_description_keywords):
                                continue
                            
                            # Must have person indicators
                            person_indicators = [
                                "born", "is a", "was a", "is an", "was an",
                                "singer", "actor", "actress", "musician", "footballer", 
                                "athlete", "politician", "presenter", "model", "chef", 
                                "comedian", "director", "rapper", "personality", "celebrity",
                                "businessman", "businesswoman", "entrepreneur", "influencer",
                                "author", "writer", "journalist", "host", "dancer",
                                "prince", "princess", "duke", "duchess", "queen", "king"
                            ]
                            
                            if not any(ind in desc_lower for ind in person_indicators):
                                continue
                            
                            # Estimate tier and price
                            tier = estimate_tier_from_description(desc)
                            price = get_price_for_tier(tier)
                            
                            # Ensure valid image
                            final_image = image if image else f"https://ui-avatars.com/api/?name={title.replace(' ', '+')}&size=64&background=FF0099&color=fff"
                            
                            results.append({
                                "name": title,
                                "description": desc[:150] + "..." if len(desc) > 150 else desc,
                                "image": final_image,
                                "estimated_tier": tier,
                                "estimated_price": price
                            })
                            
                            # Limit to 5 clean results
                            if len(results) >= 5:
                                break
                    except Exception as inner_e:
                        logger.error(f"Inner error processing {title}: {inner_e}")
                        continue
                
                logger.info(f"Autocomplete returning {len(results)} results for {query}")
                return results
    except Exception as e:
        logger.error(f"Wikipedia autocomplete error: {e}")
    return []

def estimate_tier_from_description(description: str) -> str:
    """Estimate celebrity tier from Wikipedia description"""
    desc_lower = description.lower()
    
    # Check for A-list indicators
    if any(ind in desc_lower for ind in A_LIST_INDICATORS):
        return "A"
    
    # Check for B-list indicators  
    if any(ind in desc_lower for ind in B_LIST_INDICATORS):
        return "B"
    
    # Check for C-list indicators
    if any(ind in desc_lower for ind in C_LIST_INDICATORS):
        return "C"
    
    return "D"

def get_base_price_for_tier(tier: str) -> float:
    """Get BASE price range for celebrity tier (in millions)"""
    # New pricing structure:
    # A-List: £9m-£12m (high scoring but expensive)
    # B-List: £5m-£8m (balanced steady picks)
    # C-List: £2m-£4m (risk/reward)
    # D-List: £0.5m-£1.5m (cheap wildcards)
    base_prices = {
        "A": 9.0,   # Base £9M, can go up to £12M
        "B": 5.0,   # Base £5M, can go up to £8M
        "C": 2.0,   # Base £2M, can go up to £4M
        "D": 0.5    # Base £0.5M, can go up to £1.5M
    }
    return base_prices.get(tier, 0.5)

def get_dynamic_price(tier: str, buzz_score: float, name: str = "") -> float:
    """Calculate dynamic price based on tier, buzz score
    
    Pricing Tiers (STRICT - MAX £12M for any celeb):
    - A-List: £9m-£12m (high scoring but expensive)
    - B-List: £5m-£8m (balanced steady picks)  
    - C-List: £2m-£4m (risk/reward)
    - D-List: £0.5m-£1.5m (cheap wildcards)
    """
    # Define STRICT price ranges for each tier
    price_ranges = {
        "A": (9.0, 12.0),   # £9m-£12m
        "B": (5.0, 8.0),    # £5m-£8m
        "C": (2.0, 4.0),    # £2m-£4m
        "D": (0.5, 1.5)     # £0.5m-£1.5m
    }
    
    min_price, max_price = price_ranges.get(tier, (0.5, 1.5))
    price_range = max_price - min_price
    
    # Dynamic pricing based on buzz score
    # Buzz score typically ranges from 5 (minimum) to 150 (very high)
    # Map this to a 0-1 scale for price adjustment
    buzz_factor = min(1.0, max(0.0, (buzz_score - 5) / 100))
    
    # Calculate dynamic price within the tier's range
    dynamic_price = min_price + (price_range * buzz_factor)
    
    # STRICT: Ensure price stays within tier range and NEVER exceeds £12M
    dynamic_price = max(min_price, min(max_price, dynamic_price))
    dynamic_price = min(12.0, dynamic_price)  # Hard cap at £12M
    
    # Round to 1 decimal place
    return round(dynamic_price, 1)

# Keep old function for backwards compatibility but make it use dynamic pricing
def get_price_for_tier(tier: str) -> float:
    """Get base price for tier (for autocomplete before buzz is calculated)"""
    return get_base_price_for_tier(tier)

async def calculate_celebrity_tier(bio: str, name: str) -> tuple:
    """Calculate celebrity tier based on bio content and return (tier, base_price)"""
    bio_lower = bio.lower()
    
    # A-list: Major awards, billions in earnings, legendary status
    a_list_score = sum(1 for ind in A_LIST_INDICATORS if ind in bio_lower)
    if a_list_score >= 2:
        return ("A", get_base_price_for_tier("A"))
    
    # B-list: Award-winning, millions, chart-topping
    b_list_score = sum(1 for ind in B_LIST_INDICATORS if ind in bio_lower)
    if a_list_score >= 1 or b_list_score >= 2:
        return ("B", get_base_price_for_tier("B"))
    
    # C-list: Known for appearances, contestants
    c_list_score = sum(1 for ind in C_LIST_INDICATORS if ind in bio_lower)
    if b_list_score >= 1 or c_list_score >= 1:
        return ("C", get_base_price_for_tier("C"))
    
    # D-list: Everyone else
    return ("D", get_base_price_for_tier("D"))

async def fetch_wikipedia_info(name: str) -> dict:
    """Fetch celebrity info from Wikipedia API"""
    try:
        headers = {
            "User-Agent": "CelebrityBuzzIndex/1.0 (contact@example.com)"
        }
        async with httpx.AsyncClient() as client:
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{name.replace(' ', '_')}"
            logger.info(f"Fetching Wikipedia for: {name}, URL: {url}")
            response = await client.get(url, timeout=10.0, headers=headers)
            logger.info(f"Wikipedia response status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                bio = data.get("extract", "No biography available.")
                logger.info(f"Got bio for {name}: {bio[:100]}...")
                
                # Also try to get birth year from short description via query API
                birth_year = 0
                try:
                    query_url = f"https://en.wikipedia.org/w/api.php?action=query&titles={name.replace(' ', '_')}&prop=pageprops&format=json"
                    query_response = await client.get(query_url, timeout=5.0, headers=headers)
                    if query_response.status_code == 200:
                        query_data = query_response.json()
                        pages = query_data.get("query", {}).get("pages", {})
                        if pages:
                            page = list(pages.values())[0]
                            short_desc = page.get("pageprops", {}).get("wikibase-shortdesc", "")
                            # Extract birth year from patterns like "(born 1930)" or "(b. 1945)"
                            birth_match = re.search(r'\((?:born|b\.)\s*(\d{4})\)', short_desc, re.IGNORECASE)
                            if birth_match:
                                birth_year = int(birth_match.group(1))
                except Exception as e:
                    logger.error(f"Failed to get birth year for {name}: {e}")
                
                return {
                    "name": data.get("title", name),
                    "bio": bio,
                    "image": data.get("thumbnail", {}).get("source", ""),
                    "wiki_url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                    "birth_year": birth_year
                }
            else:
                logger.error(f"Wikipedia returned status {response.status_code}: {response.text[:200]}")
    except Exception as e:
        logger.error(f"Wikipedia fetch error for {name}: {type(e).__name__}: {e}")
    return {"name": name, "bio": "Celebrity profile", "image": "", "wiki_url": "", "birth_year": 0}

def detect_category_from_bio(bio: str, name: str) -> str:
    """Detect celebrity category from bio text"""
    bio_lower = bio.lower()
    name_lower = name.lower()
    
    # Check for specific known celebrities first
    reality_tv_names = ["katie price", "gemma collins", "pete wicks", "joey essex", "sam faiers", 
                        "kardashian", "jenner", "love island"]
    royal_names = ["prince", "princess", "king charles", "queen", "duke", "duchess", 
                   "prince andrew", "prince william", "prince harry", "kate middleton", "meghan markle"]
    
    for rn in royal_names:
        if rn in name_lower or rn in bio_lower:
            return "royals"
    
    for rtn in reality_tv_names:
        if rtn in name_lower or rtn in bio_lower:
            return "reality_tv"
    
    # Reality TV keywords (check before actors)
    if any(x in bio_lower for x in ["reality television", "reality tv", "reality show", "glamour model", 
                                      "media personality", "television personality", "socialite",
                                      "keeping up with", "big brother", "love island", "towie",
                                      "i'm a celebrity", "strictly come dancing contestant"]):
        return "reality_tv"
    
    # Royals
    if any(x in bio_lower for x in ["royal family", "british royal", "heir to the throne", 
                                     "house of windsor", "buckingham palace", "monarchy"]):
        return "royals"
    
    # Athletes - check BEFORE musicians (racing driver, footballer, etc. should take priority)
    if any(x in bio_lower for x in ["footballer", "athlete", "football player", "basketball", "soccer", 
                                     "tennis", "olympic", "premier league", "f1", "formula one",
                                     "racing driver", "cricketer", "rugby", "boxing", "boxer",
                                     "striker", "goalkeeper", "midfielder", "defender",
                                     "bundesliga", "la liga", "serie a", "england national team",
                                     "world cup", "motorsport", "grand prix"]):
        return "athletes"
    
    # Musicians/Singers - removed "record" as it's too generic
    if any(x in bio_lower for x in ["singer", "songwriter", "musician", "rapper", "vocalist", 
                                     "band", "album", "grammy", "brit award", "concert", 
                                     "tour", "music artist", "pop star", "rock star", "hip hop",
                                     "r&b", "mezzo-soprano", "soprano", "tenor", "musical artist",
                                     "recording artist"]):
        return "musicians"
    
    # TV actors
    if any(x in bio_lower for x in ["television actor", "tv actor", "television series", "tv series", 
                                     "sitcom", "soap opera", "tv show", "bbc", "itv", "channel 4",
                                     "eastenders", "coronation street", "emmerdale", "doctor who",
                                     "killing eve", "the crown"]):
        return "tv_actors"
    
    # Movie stars - check for film/movie actors
    if any(x in bio_lower for x in ["actor", "actress", "film", "movie", "cinema", "hollywood", 
                                     "oscar", "bafta", "academy award", "golden globe",
                                     "box office", "marvel", "superhero", "spider-man"]):
        return "movie_stars"
    
    # Other (businesspeople, chefs, presenters, etc.)
    if any(x in bio_lower for x in ["chef", "presenter", "host", "businessman", "entrepreneur",
                                     "tv presenter", "author", "journalist", "comedian"]):
        return "other"
    
    return "other"  # Default to other

async def generate_celebrity_news(name: str, category: str) -> List[dict]:
    """Generate AI-powered news summaries for celebrity"""
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"news-{uuid.uuid4()}",
            system_message="""You are a celebrity news aggregator. Generate realistic, current celebrity news headlines and summaries.
            Return a JSON array with 5 news items. Each item should have:
            - title: A catchy headline
            - summary: 1-2 sentence summary
            - source: A realistic news source name (e.g., "Entertainment Weekly", "TMZ", "People", "BBC News", "Daily Mail")
            - date: Recent date in format "Jan 15, 2026"
            - sentiment: "positive", "neutral", or "negative"
            
            Make the news realistic and varied - mix of professional achievements, personal life, and industry news.
            ONLY return valid JSON array, no other text."""
        ).with_model("openai", "gpt-4o")

        message = UserMessage(text=f"Generate 5 recent news headlines about {name} ({category}). Return ONLY a JSON array.")
        response = await chat.send_message(message)
        
        # Parse the JSON response
        try:
            # Clean the response - remove markdown code blocks if present
            clean_response = response.strip()
            if clean_response.startswith("```"):
                clean_response = clean_response.split("```")[1]
                if clean_response.startswith("json"):
                    clean_response = clean_response[4:]
            clean_response = clean_response.strip()
            
            news = json.loads(clean_response)
            return news if isinstance(news, list) else []
        except json.JSONDecodeError:
            logger.error(f"JSON parse error for {name}")
            return []
    except Exception as e:
        logger.error(f"News generation error: {e}")
        return []

def calculate_buzz_score(news: List[dict]) -> float:
    """Calculate buzz score based on news coverage"""
    if not news:
        return 10.0  # Base score
    
    score = 10.0
    for article in news:
        sentiment = article.get("sentiment", "neutral")
        source = article.get("source", "").lower()
        
        # Source weight
        if any(x in source for x in ["tmz", "daily mail", "sun"]):
            score += 3.0
        elif any(x in source for x in ["people", "entertainment weekly", "variety"]):
            score += 2.0
        elif any(x in source for x in ["bbc", "cnn", "guardian"]):
            score += 1.5
        else:
            score += 1.0
        
        # Sentiment modifier - CONTROVERSY BONUS is 25 points!
        if sentiment == "positive":
            score += 0.5
        elif sentiment == "negative":
            score += 25.0  # Big controversy bonus!
    
    # Ensure minimum score of 5 points
    return round(max(5.0, min(score, 150.0)), 1)

def calculate_price(buzz_score: float, tier: str, name: str = "") -> float:
    """Calculate celebrity price with DYNAMIC PRICING based on buzz
    
    Prices go UP when celebrity is in the news (high buzz)
    Prices go DOWN when celebrity drifts out of the news (low buzz)
    """
    return get_dynamic_price(tier, buzz_score, name)

# Points calculation methodology
POINTS_METHODOLOGY = {
    "description": "Celebrity Buzz Points are calculated based on media coverage and public interest",
    "factors": [
        {
            "name": "News Mentions",
            "description": "Each news article mentioning the celebrity",
            "points_per_unit": 1.0,
            "unit": "article"
        },
        {
            "name": "Tabloid Coverage",
            "description": "Coverage in tabloids (Daily Mail, The Sun, TMZ) - higher weight due to engagement",
            "points_per_unit": 3.0,
            "unit": "article"
        },
        {
            "name": "Broadsheet Coverage",
            "description": "Coverage in quality press (BBC, Guardian, Times)",
            "points_per_unit": 2.0,
            "unit": "article"
        },
        {
            "name": "Controversy Bonus",
            "description": "Negative/scandal news generates more buzz",
            "points_per_unit": 25.0,
            "unit": "per scandal"
        },
        {
            "name": "Brown Bread Bonus 💀",
            "description": "If your celebrity passes away, you receive a massive points bonus!",
            "points_per_unit": 100.0,
            "unit": "per deceased celebrity"
        },
        {
            "name": "Social Media Trending",
            "description": "When celebrity trends on social platforms",
            "points_per_unit": 5.0,
            "unit": "trending event"
        }
    ],
    "tier_multipliers": {
        "A": "1.0x (baseline - already high visibility)",
        "B": "1.2x (needs more buzz to match A-list)",
        "C": "1.5x (buzz matters more for rising stars)",
        "D": "2.0x (buzz can rapidly elevate D-listers)"
    },
    "example": "A D-list celebrity with 10 tabloid mentions = 10 × 3.0 × 2.0 = 60 points"
}

# ==================== API ROUTES ====================

@api_router.get("/")
async def root():
    return {"message": "Celebrity Buzz Index API", "version": "1.0"}

@api_router.get("/categories")
async def get_categories():
    """Get all celebrity categories"""
    return {"categories": CATEGORIES}

@api_router.get("/points-methodology")
async def get_points_methodology():
    """Get explanation of how points are calculated"""
    return POINTS_METHODOLOGY

@api_router.get("/autocomplete")
async def autocomplete_search(q: str):
    """Get Wikipedia autocomplete suggestions for celebrity search"""
    if len(q) < 2:
        return {"suggestions": []}
    
    suggestions = await fetch_wikipedia_autocomplete(q)
    return {"suggestions": suggestions}

@api_router.post("/seed")
async def seed_initial_data():
    """Seed initial celebrity data for faster loading"""
    seeded = []
    # Seed 2 celebrities per category for quick initial load
    for category, names in TRENDING_CELEBRITIES.items():
        for name in names[:2]:
            existing = await db.celebrities.find_one({"name": {"$regex": f"^{name}$", "$options": "i"}})
            if not existing:
                try:
                    search = CelebritySearch(name=name)
                    result = await search_celebrity(search, override_category=category)
                    seeded.append(name)
                except Exception as e:
                    logger.error(f"Failed to seed {name}: {e}")
    return {"seeded": seeded, "count": len(seeded)}

@api_router.get("/trending")
async def get_trending():
    """Get trending celebrities across all categories with correct dynamic pricing"""
    # Check cache first
    cached = await db.trending_cache.find_one(
        {"type": "trending"},
        {"_id": 0}
    )
    
    # Return cached if less than 1 hour old
    if cached and cached.get("updated_at"):
        cache_time = datetime.fromisoformat(cached["updated_at"])
        if (datetime.now(timezone.utc) - cache_time).seconds < 3600:
            return {"trending": cached.get("celebrities", [])}
    
    # Otherwise fetch fresh data
    trending = []
    for category, names in TRENDING_CELEBRITIES.items():
        for name in names[:3]:  # Top 3 per category
            celeb = await db.celebrities.find_one(
                {"name": name},
                {"_id": 0}
            )
            if celeb:
                # Recalculate tier from bio if needed
                bio = celeb.get("bio", "")
                recalc_tier = estimate_tier_from_description(bio)
                
                # Use recalculated tier
                tier = recalc_tier
                buzz_score = celeb.get("buzz_score", 5)
                
                # Recalculate price with STRICT tier-based pricing
                celeb["tier"] = tier
                celeb["price"] = get_dynamic_price(tier, buzz_score, name)
                trending.append(celeb)
    
    if trending:
        # Sort by buzz score
        trending.sort(key=lambda x: x.get("buzz_score", 0), reverse=True)
        
        # Update cache
        await db.trending_cache.update_one(
            {"type": "trending"},
            {"$set": {
                "celebrities": trending[:15],
                "updated_at": datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )
    
    return {"trending": trending[:15]}

@api_router.post("/celebrity/search")
async def search_celebrity(search: CelebritySearch, override_category: str = None):
    """Search for a celebrity and get their buzz data"""
    name = search.name.strip()
    
    # Check if already in database
    existing = await db.celebrities.find_one({"name": {"$regex": f"^{name}$", "$options": "i"}}, {"_id": 0})
    if existing:
        return {"celebrity": existing}
    
    # Fetch from Wikipedia
    wiki_info = await fetch_wikipedia_info(name)
    logger.info(f"Wiki info for {name}: bio_length={len(wiki_info.get('bio', ''))}, bio_preview={wiki_info.get('bio', '')[:100]}")
    
    # Use override category if provided, otherwise detect from bio
    if override_category:
        category = override_category
    else:
        category = detect_category_from_bio(wiki_info.get("bio", ""), wiki_info["name"])
    
    # Calculate celebrity tier based on bio
    tier, base_price = await calculate_celebrity_tier(wiki_info.get("bio", ""), wiki_info["name"])
    
    # Generate news
    news = await generate_celebrity_news(wiki_info["name"], category)
    
    # Calculate buzz score
    buzz_score = calculate_buzz_score(news)
    
    # Final price based on tier, buzz, and controversy
    price = calculate_price(buzz_score, tier, wiki_info["name"])
    
    # Check if celebrity is deceased (look for death date in bio)
    bio_lower = wiki_info.get("bio", "").lower()
    is_deceased = any(x in bio_lower for x in ["was a ", "died ", "passed away", "1900–", "1910–", "1920–", "1930–", "1940–", "1950–", "1960–", "1970–", "1980–", "1990–", "2000–", "2010–", "2020–"])
    
    # Extract birth year - prefer wiki_info birth_year, fallback to bio extraction
    birth_year = wiki_info.get("birth_year", 0)
    if not birth_year:
        birth_year = extract_birth_year_from_bio(wiki_info.get("bio", ""))
    age = calculate_age(birth_year)
    
    # Create celebrity object
    celebrity = Celebrity(
        name=wiki_info["name"],
        bio=wiki_info["bio"][:500] if wiki_info["bio"] else "No biography available.",
        image=wiki_info["image"] or f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}&size=400&background=FF0099&color=fff",
        category=category,
        wiki_url=wiki_info["wiki_url"],
        buzz_score=buzz_score,
        price=price,
        tier=tier,
        news=news,
        is_deceased=is_deceased,
        birth_year=birth_year,
        age=age,
        times_picked=0
    )
    
    # Save to database
    doc = celebrity.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.celebrities.insert_one(doc)
    
    # Remove _id before returning
    if '_id' in doc:
        del doc['_id']
    
    return {"celebrity": doc}

@api_router.get("/celebrity/{celebrity_id}")
async def get_celebrity(celebrity_id: str):
    """Get celebrity by ID"""
    celebrity = await db.celebrities.find_one({"id": celebrity_id}, {"_id": 0})
    if not celebrity:
        raise HTTPException(status_code=404, detail="Celebrity not found")
    return {"celebrity": celebrity}

@api_router.get("/celebrities/category/{category}")
async def get_celebrities_by_category(category: str):
    """Get celebrities by category"""
    # First check if we have any in DB
    celebrities = await db.celebrities.find(
        {"category": category},
        {"_id": 0}
    ).to_list(20)
    
    # If empty, seed with trending (force correct category)
    if not celebrities and category in TRENDING_CELEBRITIES:
        for name in TRENDING_CELEBRITIES[category][:5]:
            search = CelebritySearch(name=name)
            await search_celebrity(search, override_category=category)
        
        celebrities = await db.celebrities.find(
            {"category": category},
            {"_id": 0}
        ).to_list(20)
    
    return {"celebrities": celebrities}

@api_router.get("/stats")
async def get_stats():
    """Get site statistics including player count and transfer window"""
    team_count = await db.teams.count_documents({})
    transfer_window = is_transfer_window_open()
    
    return {
        "player_count": team_count,
        "transfer_window": transfer_window
    }

@api_router.get("/pricing-info")
async def get_pricing_info():
    """Get pricing tier information for the game"""
    return {
        "tiers": [
            {
                "tier": "A-List",
                "price_range": "£9m-£12m",
                "description": "High scoring but expensive",
                "strategy": "Star players with guaranteed buzz"
            },
            {
                "tier": "B-List", 
                "price_range": "£5m-£8m",
                "description": "Balanced steady picks",
                "strategy": "Reliable performers with consistent coverage"
            },
            {
                "tier": "C-List",
                "price_range": "£2m-£4m", 
                "description": "Risk/reward",
                "strategy": "Could break out or fade away"
            },
            {
                "tier": "D-List",
                "price_range": "£0.5m-£1.5m",
                "description": "Cheap wildcards",
                "strategy": "High upside if they hit headlines"
            }
        ],
        "dynamic_pricing": "Prices fluctuate weekly based on media coverage. Hot celebs cost more, quiet celebs cost less.",
        "transfer_window": "Opens every Saturday at 12pm GMT for 24 hours"
    }

@api_router.get("/hot-celebs")
async def get_hot_celebs():
    """Get hot celebrities making headlines - RANDOMIZED on each refresh with real photos"""
    hot_list = []
    headers = {"User-Agent": "CelebrityBuzzIndex/1.0 (contact@example.com)"}
    
    # Get random selection of celebs from pool
    random_celebs = get_random_hot_celebs(8)
    
    async with httpx.AsyncClient() as client:
        for celeb_info in random_celebs:
            # Check if celeb exists in DB
            celeb = await db.celebrities.find_one(
                {"name": {"$regex": f"^{celeb_info['name']}$", "$options": "i"}},
                {"_id": 0}
            )
            
            if celeb and celeb.get("image") and not celeb.get("image", "").startswith("https://ui-avatars"):
                # Recalculate price with dynamic pricing based on tier and buzz
                tier = celeb.get("tier", celeb_info["tier"])
                buzz_score = celeb.get("buzz_score", 50)
                price = get_dynamic_price(tier, buzz_score, celeb.get("name", celeb_info["name"]))
                hot_list.append({
                    **celeb,
                    "tier": tier,
                    "price": price,
                    "hot_reason": celeb_info["reason"]
                })
            else:
                # Fetch real image from Wikipedia
                try:
                    wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{celeb_info['name'].replace(' ', '_')}"
                    response = await client.get(wiki_url, timeout=5.0, headers=headers)
                    
                    if response.status_code == 200:
                        wiki_data = response.json()
                        image = wiki_data.get("thumbnail", {}).get("source", "")
                        if not image:
                            image = f"https://ui-avatars.com/api/?name={celeb_info['name'].replace(' ', '+')}&size=200&background=FF0099&color=fff"
                    else:
                        image = f"https://ui-avatars.com/api/?name={celeb_info['name'].replace(' ', '+')}&size=200&background=FF0099&color=fff"
                except:
                    image = f"https://ui-avatars.com/api/?name={celeb_info['name'].replace(' ', '+')}&size=200&background=FF0099&color=fff"
                
                hot_list.append({
                    "name": celeb_info["name"],
                    "tier": celeb_info["tier"],
                    "category": celeb_info["category"],
                    "hot_reason": celeb_info["reason"],
                    "price": get_dynamic_price(celeb_info["tier"], 50, celeb_info["name"]),  # Use dynamic price with moderate buzz
                    "image": image
                })
    
    return {"hot_celebs": hot_list}

@api_router.get("/price-alerts/{team_id}")
async def get_price_alerts(team_id: str):
    """Get price change alerts for a team's celebrities
    
    Shows which celebrities have significant price changes coming:
    - Hot celebs (rising in news) = price likely to increase
    - Quiet celebs (out of news) = price likely to decrease
    """
    team = await db.teams.find_one({"id": team_id}, {"_id": 0})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    alerts = []
    for celeb_data in team.get("celebrities", []):
        celeb = await db.celebrities.find_one(
            {"id": celeb_data.get("celebrity_id")},
            {"_id": 0}
        )
        if celeb:
            current_price = celeb.get("price", 0)
            buzz_score = celeb.get("buzz_score", 5)
            tier = celeb.get("tier", "D")
            
            # Calculate what the new dynamic price would be
            new_price = get_dynamic_price(tier, buzz_score, celeb.get("name", ""))
            price_change = new_price - current_price
            
            # Only alert if significant change (>= £0.5M)
            if abs(price_change) >= 0.5:
                alert_type = "rising" if price_change > 0 else "falling"
                alerts.append({
                    "celebrity_id": celeb.get("id"),
                    "name": celeb.get("name"),
                    "image": celeb.get("image"),
                    "tier": tier,
                    "current_price": current_price,
                    "projected_price": new_price,
                    "change": round(price_change, 1),
                    "alert_type": alert_type,
                    "reason": f"High media buzz" if alert_type == "rising" else "Low media coverage"
                })
    
    # Sort by biggest changes first
    alerts.sort(key=lambda x: abs(x["change"]), reverse=True)
    
    return {
        "alerts": alerts,
        "team_id": team_id,
        "next_price_update": "Saturday 12pm GMT"
    }

@api_router.get("/hot-streaks/{team_id}")
async def get_hot_streaks(team_id: str):
    """Get hot streak notifications for team's celebrities
    
    A "hot streak" means a celebrity has been in the news for 3+ consecutive days.
    This indicates high buzz and potential price increases.
    """
    team = await db.teams.find_one({"id": team_id}, {"_id": 0})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    hot_streaks = []
    for celeb_data in team.get("celebrities", []):
        celeb = await db.celebrities.find_one(
            {"id": celeb_data.get("celebrity_id")},
            {"_id": 0}
        )
        if celeb:
            buzz_score = celeb.get("buzz_score", 5)
            tier = celeb.get("tier", "D")
            
            # Calculate streak based on buzz score
            # High buzz (>40) = likely on a streak
            # Very high buzz (>60) = definitely on a streak
            streak_days = 0
            streak_status = None
            
            if buzz_score >= 80:
                streak_days = 5
                streak_status = "🔥🔥🔥 ON FIRE!"
            elif buzz_score >= 60:
                streak_days = 4
                streak_status = "🔥🔥 Hot Streak!"
            elif buzz_score >= 40:
                streak_days = 3
                streak_status = "🔥 Warming Up!"
            
            if streak_days >= 3:
                hot_streaks.append({
                    "celebrity_id": celeb.get("id"),
                    "name": celeb.get("name"),
                    "image": celeb.get("image"),
                    "tier": tier,
                    "buzz_score": buzz_score,
                    "streak_days": streak_days,
                    "streak_status": streak_status,
                    "tip": "Consider keeping - price likely to rise!" if buzz_score >= 60 else "Watch closely - could heat up more!"
                })
    
    # Sort by streak days
    hot_streaks.sort(key=lambda x: x["streak_days"], reverse=True)
    
    return {
        "hot_streaks": hot_streaks,
        "team_id": team_id
    }

@api_router.get("/top-picked")
async def get_top_picked():
    """Get most picked celebrities"""
    top_celebs = await db.celebrities.find(
        {"times_picked": {"$gt": 0}},
        {"_id": 0}
    ).sort("times_picked", -1).to_list(10)
    
    return {"top_picked": top_celebs}

@api_router.get("/brown-bread-watch")
async def get_brown_bread_watch():
    """Get elderly celebrities for Brown Bread Watch - strategic picks for the bonus!
    
    SPECIAL PRICING: Top 3 oldest celebs can cost up to £15M (decreasing)
    - #1 oldest: £15M
    - #2 oldest: £13M  
    - #3 oldest: £11M
    - Rest: normal tier pricing (max £12M)
    """
    # Find living celebrities with known age >= 60
    elderly_celebs = await db.celebrities.find(
        {
            "is_deceased": False,
            "age": {"$gte": 60}
        },
        {"_id": 0}
    ).sort("age", -1).to_list(20)
    
    # Special pricing for top 3 oldest (Brown Bread premium)
    brown_bread_premium_prices = [15.0, 13.0, 11.0]  # Top 3 get premium pricing
    
    # Add risk level and special pricing to each
    watch_list = []
    for idx, celeb in enumerate(elderly_celebs):
        age = celeb.get("age", 0)
        risk = get_brown_bread_risk(age)
        
        # Apply Brown Bread premium pricing for top 3
        if idx < 3:
            special_price = brown_bread_premium_prices[idx]
        else:
            # Normal pricing for others (capped at £12M)
            tier = celeb.get("tier", "D")
            buzz_score = celeb.get("buzz_score", 5)
            special_price = get_dynamic_price(tier, buzz_score, celeb.get("name", ""))
        
        watch_list.append({
            **celeb,
            "risk_level": risk,
            "price": special_price,
            "is_premium": idx < 3  # Mark top 3 as premium
        })
    
    return {"watch_list": watch_list}

@api_router.get("/todays-news")
async def get_todays_news():
    """Get today's top REAL celebrity news from RSS feeds"""
    # Check cache (15 min cache for real news)
    cached = await db.news_cache.find_one(
        {"type": "todays_news_real"},
        {"_id": 0}
    )
    
    if cached and cached.get("updated_at"):
        cache_time = datetime.fromisoformat(cached["updated_at"])
        if (datetime.now(timezone.utc) - cache_time).seconds < 900:  # 15 min cache
            return {"news": cached.get("news", [])}
    
    # Fetch real news from RSS feeds
    news_items = []
    headers = {"User-Agent": "CelebrityBuzzIndex/1.0"}
    
    # News sources with RSS feeds - prioritize major news sources
    rss_sources = [
        ("https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml", "BBC News", True),  # Priority
        ("https://www.theguardian.com/lifeandstyle/celebrities/rss", "The Guardian", True),  # Priority
        ("https://www.tmz.com/rss.xml", "TMZ", False),
        ("https://people.com/feed/", "People", False),
        ("https://pagesix.com/feed/", "Page Six", False),
        ("https://www.dailymail.co.uk/tvshowbiz/index.rss", "Daily Mail", False),
    ]
    
    # Words that indicate MAJOR news (scandals, legal, deaths, awards)
    major_news_keywords = [
        "arrested", "charged", "court", "lawsuit", "sued", "divorce", "split",
        "dies", "dead", "death", "passed away", "funeral", "tribute",
        "scandal", "controversy", "fired", "axed", "cancelled", "banned",
        "award", "wins", "nominated", "grammy", "oscar", "emmy", "bafta",
        "pregnant", "baby", "engaged", "married", "wedding",
        "million", "billion", "record", "historic", "first ever",
        "feud", "slams", "blasts", "attacks", "responds", "breaks silence",
        "comeback", "returns", "quits", "retires", "leaves",
        "royal", "palace", "prince", "princess", "meghan", "harry", "andrew",
        "trump", "musk", "kanye", "taylor swift", "beyonce"
    ]
    
    # Words that indicate trivial gossip to SKIP
    skip_gossip_keywords = [
        "braless", "bikini", "swimsuit", "beach body", "abs", "toned",
        "shows off", "flaunts", "displays", "reveals figure",
        "lunch date", "coffee run", "grocery shopping", "walks dog",
        "outfit", "dress", "gown", "what she wore", "fashion moment",
        "lookalike", "doppelganger", "twinning"
    ]
    
    try:
        async with httpx.AsyncClient() as client:
            for rss_url, source_name, is_priority in rss_sources:
                try:
                    response = await client.get(rss_url, timeout=10.0, headers=headers)
                    if response.status_code == 200:
                        # Parse RSS (simple parsing)
                        content = response.text
                        # Extract items using simple string parsing
                        items = content.split("<item>")[1:10]  # Get first 10 items to filter
                        
                        for item in items:
                            try:
                                # Extract title
                                title_start = item.find("<title>") + 7
                                title_end = item.find("</title>")
                                title = item[title_start:title_end].replace("<![CDATA[", "").replace("]]>", "").strip()
                                title_lower = title.lower()
                                
                                # Skip trivial gossip
                                if any(skip_word in title_lower for skip_word in skip_gossip_keywords):
                                    continue
                                
                                # Check if it's major news OR from priority source
                                is_major = any(keyword in title_lower for keyword in major_news_keywords)
                                
                                # Skip non-major news from non-priority sources
                                if not is_major and not is_priority:
                                    continue
                                
                                # Extract link
                                link_start = item.find("<link>") + 6
                                link_end = item.find("</link>")
                                link = item[link_start:link_end].strip()
                                if not link or link_start < 6:
                                    # Try alternate link format
                                    link_start = item.find("<link/>") 
                                    if link_start > 0:
                                        link_end = item.find("<", link_start + 7)
                                        link = item[link_start+7:link_end].strip()
                                
                                # Extract description
                                desc_start = item.find("<description>") + 13
                                desc_end = item.find("</description>")
                                description = item[desc_start:desc_end].replace("<![CDATA[", "").replace("]]>", "").strip()
                                # Clean HTML tags from description
                                description = re.sub(r'<[^>]+>', '', description)[:200]
                                
                                # Decode HTML entities in title and description
                                title = decode_html_entities(title)
                                description = decode_html_entities(description)
                                celebrity = decode_html_entities(celebrity) if 'celebrity' in dir() else "Celebrity"
                                
                                if title and len(title) > 10:
                                    # Try to extract celebrity name from title
                                    celebrity = title.split(":")[0] if ":" in title else title.split(" - ")[0] if " - " in title else "Celebrity"
                                    celebrity = decode_html_entities(celebrity[:50])
                                    
                                    news_items.append({
                                        "celebrity": celebrity,
                                        "headline": title[:150],
                                        "summary": description[:200] if description else title,
                                        "source": source_name,
                                        "url": link,
                                        "category": "other",
                                        "is_major": is_major
                                    })
                            except Exception as e:
                                logger.error(f"Error parsing RSS item: {e}")
                                continue
                except Exception as e:
                    logger.error(f"Error fetching RSS from {source_name}: {e}")
                    continue
        
        # Sort by major news first, then limit to 6 items
        news_items.sort(key=lambda x: (not x.get("is_major", False)))
        news_items = news_items[:6]
        
        if news_items:
            # Cache it
            await db.news_cache.update_one(
                {"type": "todays_news_real"},
                {"$set": {
                    "news": news_items,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }},
                upsert=True
            )
        
        return {"news": news_items}
    except Exception as e:
        logger.error(f"Real news fetch error: {e}")
        if cached:
            return {"news": cached.get("news", [])}
        return {"news": []}

@api_router.post("/team/create")
async def create_team(team_data: TeamCreate):
    """Create a new team"""
    # Check for banned words
    if contains_banned_words(team_data.team_name):
        raise HTTPException(status_code=400, detail="Team name contains inappropriate language. Please choose another name.")
    
    team = UserTeam(
        team_name=team_data.team_name,
        last_transfer_reset=get_week_number()
    )
    doc = team.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.teams.insert_one(doc)
    if '_id' in doc:
        del doc['_id']
    return {"team": doc}

@api_router.post("/team/rename")
async def rename_team(team_id: str, new_name: str):
    """Rename a team (with profanity check)"""
    if contains_banned_words(new_name):
        raise HTTPException(status_code=400, detail="Team name contains inappropriate language")
    
    result = await db.teams.update_one(
        {"id": team_id},
        {"$set": {"team_name": new_name}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Team not found")
    
    team = await db.teams.find_one({"id": team_id}, {"_id": 0})
    return {"team": team}

@api_router.get("/team/customization-options")
async def get_customization_options():
    """Get available team customization options"""
    return {
        "colors": TEAM_COLORS,
        "icons": TEAM_ICONS
    }

@api_router.post("/team/customize")
async def customize_team(data: TeamCustomize):
    """Customize team appearance"""
    team = await db.teams.find_one({"id": data.team_id})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    updates = {}
    
    # Update team name (with profanity check)
    if data.team_name:
        if contains_banned_words(data.team_name):
            raise HTTPException(status_code=400, detail="Team name contains inappropriate language")
        updates["team_name"] = data.team_name
    
    # Update team color
    if data.team_color:
        valid_colors = [c["id"] for c in TEAM_COLORS]
        if data.team_color not in valid_colors:
            raise HTTPException(status_code=400, detail="Invalid color selection")
        updates["team_color"] = data.team_color
    
    # Update team icon
    if data.team_icon:
        valid_icons = [i["id"] for i in TEAM_ICONS]
        if data.team_icon not in valid_icons:
            raise HTTPException(status_code=400, detail="Invalid icon selection")
        updates["team_icon"] = data.team_icon
    
    if updates:
        await db.teams.update_one({"id": data.team_id}, {"$set": updates})
    
    # Return updated team
    updated_team = await db.teams.find_one({"id": data.team_id}, {"_id": 0})
    return {"team": updated_team, "message": "Team customized!"}

@api_router.get("/team/{team_id}")
async def get_team(team_id: str):
    """Get team by ID"""
    team = await db.teams.find_one({"id": team_id}, {"_id": 0})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check if transfer window reset needed
    current_week = get_week_number()
    if team.get("last_transfer_reset") != current_week:
        await db.teams.update_one(
            {"id": team_id},
            {"$set": {"transfers_this_week": 0, "last_transfer_reset": current_week}}
        )
        team["transfers_this_week"] = 0
        team["last_transfer_reset"] = current_week
    
    return {"team": team}

@api_router.post("/team/add")
async def add_to_team(data: AddToTeam):
    """Add celebrity to team"""
    MAX_TEAM_SIZE = 10
    
    team = await db.teams.find_one({"id": data.team_id})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check team size limit
    if len(team.get("celebrities", [])) >= MAX_TEAM_SIZE:
        raise HTTPException(status_code=400, detail=f"Team is full! Maximum {MAX_TEAM_SIZE} celebrities allowed")
    
    celebrity = await db.celebrities.find_one({"id": data.celebrity_id})
    if not celebrity:
        raise HTTPException(status_code=404, detail="Celebrity not found")
    
    # Check if already in team
    for c in team.get("celebrities", []):
        if c["celebrity_id"] == data.celebrity_id:
            raise HTTPException(status_code=400, detail="Celebrity already in team")
    
    # Check budget
    price = celebrity.get("price", 2)
    if team.get("budget_remaining", 0) < price:
        raise HTTPException(status_code=400, detail="Insufficient budget")
    
    # Calculate points including brown bread bonus (100 points for deceased)
    celeb_points = celebrity["buzz_score"]
    brown_bread_bonus = 0
    if celebrity.get("is_deceased"):
        brown_bread_bonus = 100.0  # 100 points for dead celebs!
        celeb_points += brown_bread_bonus
    
    # Add to team
    team_celeb = TeamCelebrity(
        celebrity_id=celebrity["id"],
        name=celebrity["name"],
        image=celebrity["image"],
        category=celebrity["category"],
        price=price,
        buzz_score=celebrity["buzz_score"],
        tier=celebrity.get("tier", "D"),
        added_at=datetime.now(timezone.utc).isoformat()
    )
    
    new_budget = team.get("budget_remaining", 50) - price
    new_points = team.get("total_points", 0) + celeb_points
    new_brown_bread = team.get("brown_bread_bonus", 0) + brown_bread_bonus
    
    await db.teams.update_one(
        {"id": data.team_id},
        {
            "$push": {"celebrities": team_celeb.model_dump()},
            "$set": {
                "budget_remaining": new_budget,
                "total_points": new_points,
                "brown_bread_bonus": new_brown_bread
            }
        }
    )
    
    # Increment times_picked for the celebrity
    await db.celebrities.update_one(
        {"id": data.celebrity_id},
        {"$inc": {"times_picked": 1}}
    )
    
    updated_team = await db.teams.find_one({"id": data.team_id}, {"_id": 0})
    return {"team": updated_team, "brown_bread_bonus": brown_bread_bonus > 0}

@api_router.post("/team/transfer")
async def transfer_celebrity(data: TransferRequest):
    """Transfer window: sell one celebrity and buy another (1 per week)"""
    team = await db.teams.find_one({"id": data.team_id})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check transfer window
    current_week = get_week_number()
    if team.get("last_transfer_reset") != current_week:
        # Reset transfers for new week
        team["transfers_this_week"] = 0
    
    if team.get("transfers_this_week", 0) >= 1:
        raise HTTPException(status_code=400, detail="You've already used your transfer this week! Wait until next week.")
    
    # Find celebrity to sell
    sell_celeb = None
    for c in team.get("celebrities", []):
        if c["celebrity_id"] == data.sell_celebrity_id:
            sell_celeb = c
            break
    
    if not sell_celeb:
        raise HTTPException(status_code=404, detail="Celebrity to sell not found in team")
    
    # Get celebrity to buy
    buy_celeb = await db.celebrities.find_one({"id": data.buy_celebrity_id})
    if not buy_celeb:
        raise HTTPException(status_code=404, detail="Celebrity to buy not found")
    
    # Check if already in team
    for c in team.get("celebrities", []):
        if c["celebrity_id"] == data.buy_celebrity_id:
            raise HTTPException(status_code=400, detail="Celebrity already in team")
    
    # Calculate budget after sale
    budget_after_sale = team.get("budget_remaining", 0) + sell_celeb["price"]
    
    # Check if can afford new celebrity
    if budget_after_sale < buy_celeb.get("price", 5):
        raise HTTPException(status_code=400, detail="Insufficient budget even after sale")
    
    # Perform transfer
    new_budget = budget_after_sale - buy_celeb["price"]
    new_points = team.get("total_points", 0) - sell_celeb["buzz_score"] + buy_celeb["buzz_score"]
    
    # Check brown bread bonus for new celeb (100 points)
    brown_bread_bonus = 0
    if buy_celeb.get("is_deceased"):
        brown_bread_bonus = 100.0  # 100 points for dead celebs!
        new_points += brown_bread_bonus
    
    new_team_celeb = TeamCelebrity(
        celebrity_id=buy_celeb["id"],
        name=buy_celeb["name"],
        image=buy_celeb["image"],
        category=buy_celeb["category"],
        price=buy_celeb["price"],
        buzz_score=buy_celeb["buzz_score"],
        tier=buy_celeb.get("tier", "D"),
        added_at=datetime.now(timezone.utc).isoformat()
    )
    
    await db.teams.update_one(
        {"id": data.team_id},
        {
            "$pull": {"celebrities": {"celebrity_id": data.sell_celebrity_id}},
        }
    )
    
    await db.teams.update_one(
        {"id": data.team_id},
        {
            "$push": {"celebrities": new_team_celeb.model_dump()},
            "$set": {
                "budget_remaining": new_budget,
                "total_points": max(0, new_points),
                "transfers_this_week": 1,
                "last_transfer_reset": current_week,
                "brown_bread_bonus": team.get("brown_bread_bonus", 0) + brown_bread_bonus
            }
        }
    )
    
    # Update pick counts
    await db.celebrities.update_one({"id": data.buy_celebrity_id}, {"$inc": {"times_picked": 1}})
    await db.celebrities.update_one({"id": data.sell_celebrity_id}, {"$inc": {"times_picked": -1}})
    
    updated_team = await db.teams.find_one({"id": data.team_id}, {"_id": 0})
    return {
        "team": updated_team,
        "sold": sell_celeb["name"],
        "bought": buy_celeb["name"],
        "brown_bread_bonus": brown_bread_bonus > 0
    }

@api_router.post("/team/remove")
async def remove_from_team(data: AddToTeam):
    """Remove celebrity from team"""
    team = await db.teams.find_one({"id": data.team_id})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Find celebrity in team
    removed = None
    for c in team.get("celebrities", []):
        if c["celebrity_id"] == data.celebrity_id:
            removed = c
            break
    
    if not removed:
        raise HTTPException(status_code=404, detail="Celebrity not in team")
    
    new_budget = team.get("budget_remaining", 0) + removed["price"]
    new_points = team.get("total_points", 0) - removed["buzz_score"]
    
    await db.teams.update_one(
        {"id": data.team_id},
        {
            "$pull": {"celebrities": {"celebrity_id": data.celebrity_id}},
            "$set": {
                "budget_remaining": new_budget,
                "total_points": max(0, new_points)
            }
        }
    )
    
    updated_team = await db.teams.find_one({"id": data.team_id}, {"_id": 0})
    return {"team": updated_team}

@api_router.get("/leaderboard")
async def get_leaderboard():
    """Get team leaderboard"""
    teams = await db.teams.find({}, {"_id": 0}).to_list(100)
    
    leaderboard = []
    for team in teams:
        # Get team color and icon info
        team_color = team.get("team_color", "pink")
        team_icon = team.get("team_icon", "star")
        
        color_info = next((c for c in TEAM_COLORS if c["id"] == team_color), TEAM_COLORS[0])
        icon_info = next((i for i in TEAM_ICONS if i["id"] == team_icon), TEAM_ICONS[0])
        
        leaderboard.append({
            "team_id": team["id"],
            "team_name": team.get("team_name", "Unknown"),
            "total_points": team.get("total_points", 0),
            "celebrity_count": len(team.get("celebrities", [])),
            "brown_bread_bonus": team.get("brown_bread_bonus", 0),
            "team_color": color_info["hex"],
            "team_icon": icon_info["emoji"],
            "badges": team.get("badges", [])[:3]  # Show first 3 badges
        })
    
    # Sort by points
    leaderboard.sort(key=lambda x: x["total_points"], reverse=True)
    
    return {"leaderboard": leaderboard[:20]}

@api_router.get("/share/{team_id}")
async def get_share_data(team_id: str):
    """Get shareable data for a team"""
    team = await db.teams.find_one({"id": team_id}, {"_id": 0})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    celeb_names = [c["name"] for c in team.get("celebrities", [])[:3]]
    
    share_text = f"Check out my Celebrity Buzz team '{team['team_name']}'! "
    if celeb_names:
        share_text += f"Featuring: {', '.join(celeb_names)}. "
    share_text += f"Total Buzz: {team.get('total_points', 0):.1f} points!"
    
    return {
        "share_text": share_text,
        "team_name": team["team_name"],
        "total_points": team.get("total_points", 0),
        "celebrity_count": len(team.get("celebrities", []))
    }

# ==================== LEAGUE ENDPOINTS ====================

@api_router.post("/league/create")
async def create_league(data: LeagueCreate):
    """Create a new friends league"""
    # Check for banned words
    if contains_banned_words(data.name):
        raise HTTPException(status_code=400, detail="League name contains inappropriate language")
    
    # Verify team exists
    team = await db.teams.find_one({"id": data.team_id})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Create league
    league = League(
        name=data.name,
        owner_team_id=data.team_id,
        team_ids=[data.team_id]
    )
    
    doc = league.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.leagues.insert_one(doc)
    
    if '_id' in doc:
        del doc['_id']
    
    return {"league": doc}

@api_router.post("/league/join")
async def join_league(data: LeagueJoin):
    """Join an existing league with code"""
    # Find league by code
    league = await db.leagues.find_one({"code": data.code.upper()})
    if not league:
        raise HTTPException(status_code=404, detail="League not found. Check your code!")
    
    # Verify team exists
    team = await db.teams.find_one({"id": data.team_id})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check if already in league
    if data.team_id in league.get("team_ids", []):
        raise HTTPException(status_code=400, detail="Already in this league!")
    
    # Check max teams
    if len(league.get("team_ids", [])) >= league.get("max_teams", 20):
        raise HTTPException(status_code=400, detail="League is full!")
    
    # Add team to league
    await db.leagues.update_one(
        {"id": league["id"]},
        {"$push": {"team_ids": data.team_id}}
    )
    
    updated_league = await db.leagues.find_one({"id": league["id"]}, {"_id": 0})
    return {"league": updated_league, "message": f"Welcome to {league['name']}!"}

@api_router.get("/league/code/{code}")
async def get_league_by_code(code: str):
    """Get league by invite code"""
    league = await db.leagues.find_one({"code": code.upper()}, {"_id": 0})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    return {"league": league}

@api_router.get("/league/{league_id}")
async def get_league(league_id: str):
    """Get league details"""
    league = await db.leagues.find_one({"id": league_id}, {"_id": 0})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    return {"league": league}

@api_router.get("/league/{league_id}/leaderboard")
async def get_league_leaderboard(league_id: str):
    """Get leaderboard for a specific league"""
    league = await db.leagues.find_one({"id": league_id}, {"_id": 0})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Get all teams in this league
    team_ids = league.get("team_ids", [])
    teams = await db.teams.find({"id": {"$in": team_ids}}, {"_id": 0}).to_list(100)
    
    leaderboard = []
    for team in teams:
        leaderboard.append({
            "team_id": team["id"],
            "team_name": team.get("team_name", "Unknown"),
            "total_points": team.get("total_points", 0),
            "celebrity_count": len(team.get("celebrities", [])),
            "brown_bread_bonus": team.get("brown_bread_bonus", 0),
            "is_owner": team["id"] == league.get("owner_team_id")
        })
    
    # Sort by points
    leaderboard.sort(key=lambda x: x["total_points"], reverse=True)
    
    return {
        "league_name": league["name"],
        "league_code": league["code"],
        "leaderboard": leaderboard
    }

@api_router.get("/team/{team_id}/leagues")
async def get_team_leagues(team_id: str):
    """Get all leagues a team belongs to"""
    leagues = await db.leagues.find(
        {"team_ids": team_id},
        {"_id": 0}
    ).to_list(20)
    return {"leagues": leagues}

@api_router.post("/league/{league_id}/leave")
async def leave_league(league_id: str, team_id: str):
    """Leave a league"""
    league = await db.leagues.find_one({"id": league_id})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Can't leave if you're the owner
    if league.get("owner_team_id") == team_id:
        raise HTTPException(status_code=400, detail="Owner cannot leave. Delete the league instead.")
    
    await db.leagues.update_one(
        {"id": league_id},
        {"$pull": {"team_ids": team_id}}
    )
    
    return {"message": "Left league successfully"}

# ==================== BADGE ENDPOINTS ====================

@api_router.get("/badges")
async def get_all_badges():
    """Get all available badges"""
    return {"badges": list(BADGES.values())}

@api_router.get("/team/{team_id}/badges")
async def get_team_badges(team_id: str):
    """Get badges earned by a team"""
    team = await db.teams.find_one({"id": team_id}, {"_id": 0, "badges": 1, "team_name": 1})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Enrich badge data with full badge info
    earned_badges = []
    for badge in team.get("badges", []):
        badge_info = BADGES.get(badge.get("id", ""))
        if badge_info:
            earned_badges.append({
                **badge_info,
                "earned_at": badge.get("earned_at"),
                "league_id": badge.get("league_id", "")
            })
    
    return {"badges": earned_badges, "team_name": team.get("team_name")}

@api_router.post("/league/{league_id}/award-weekly")
async def award_weekly_badge(league_id: str):
    """Award weekly winner badge to top team in league (call weekly)"""
    league = await db.leagues.find_one({"id": league_id})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Get all teams in league
    team_ids = league.get("team_ids", [])
    if not team_ids:
        raise HTTPException(status_code=400, detail="No teams in league")
    
    teams = await db.teams.find({"id": {"$in": team_ids}}, {"_id": 0}).to_list(100)
    
    if not teams:
        raise HTTPException(status_code=400, detail="No teams found")
    
    # Find winner (highest points)
    winner = max(teams, key=lambda t: t.get("total_points", 0))
    
    # Award badge
    badge = {
        "id": "weekly_winner",
        "earned_at": datetime.now(timezone.utc).isoformat(),
        "league_id": league_id
    }
    
    await db.teams.update_one(
        {"id": winner["id"]},
        {
            "$push": {"badges": badge},
            "$inc": {"weekly_wins": 1}
        }
    )
    
    # Check if they've earned League Legend (3+ wins)
    updated_team = await db.teams.find_one({"id": winner["id"]})
    if updated_team.get("weekly_wins", 0) >= 3:
        # Check if they already have the legend badge
        has_legend = any(b.get("id") == "league_champion" for b in updated_team.get("badges", []))
        if not has_legend:
            legend_badge = {
                "id": "league_champion",
                "earned_at": datetime.now(timezone.utc).isoformat(),
                "league_id": league_id
            }
            await db.teams.update_one(
                {"id": winner["id"]},
                {"$push": {"badges": legend_badge}}
            )
    
    return {
        "winner": winner["team_name"],
        "points": winner.get("total_points", 0),
        "badge_awarded": "weekly_winner"
    }

@api_router.get("/hall-of-fame")
async def get_hall_of_fame():
    """Get the Hall of Fame - teams with most badges"""
    # Find all teams with badges
    teams_with_badges = await db.teams.find(
        {"badges": {"$exists": True, "$ne": []}},
        {"_id": 0, "id": 1, "team_name": 1, "badges": 1, "weekly_wins": 1, "total_points": 1}
    ).to_list(100)
    
    hall_of_fame = []
    for team in teams_with_badges:
        badges = team.get("badges", [])
        # Enrich badges with full info
        enriched_badges = []
        for badge in badges:
            badge_info = BADGES.get(badge.get("id", ""))
            if badge_info:
                enriched_badges.append({
                    **badge_info,
                    "earned_at": badge.get("earned_at")
                })
        
        hall_of_fame.append({
            "team_id": team["id"],
            "team_name": team["team_name"],
            "badge_count": len(badges),
            "badges": enriched_badges,
            "weekly_wins": team.get("weekly_wins", 0),
            "total_points": team.get("total_points", 0)
        })
    
    # Sort by badge count, then by weekly wins
    hall_of_fame.sort(key=lambda x: (x["badge_count"], x["weekly_wins"]), reverse=True)
    
    return {"hall_of_fame": hall_of_fame[:20]}  # Top 20

# Include router
app.include_router(api_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
