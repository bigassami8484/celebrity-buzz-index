from fastapi import FastAPI, APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
import resend
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
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

async def check_wikidata_is_human(page_ids: List[int]) -> dict:
    """
    Check Wikidata to see if Wikipedia pages are about humans.
    Uses P31 (instance of) = Q5 (human) to verify.
    Returns dict mapping page_id to True/False for human status.
    """
    if not page_ids:
        return {}
    
    results = {}
    try:
        # Use a proper User-Agent as required by Wikipedia API
        headers = {
            "User-Agent": "CelebrityBuzzIndex/1.0 (https://celebrity-buzz-index.com; contact@example.com) httpx/0.27"
        }
        
        async with httpx.AsyncClient() as client:
            # First get Wikidata IDs for the Wikipedia pages
            page_ids_str = "|".join(str(pid) for pid in page_ids)
            url = f"https://en.wikipedia.org/w/api.php?action=query&pageids={page_ids_str}&prop=pageprops&ppprop=wikibase_item&format=json"
            
            response = await client.get(url, timeout=10.0, headers=headers)
            if response.status_code != 200:
                logger.error(f"Wikipedia API error: {response.status_code}")
                return {pid: False for pid in page_ids}
            
            data = response.json()
            pages = data.get("query", {}).get("pages", {})
            
            # Map page_id to wikidata_id
            wikidata_ids = {}
            for page_id, page_data in pages.items():
                wikibase_item = page_data.get("pageprops", {}).get("wikibase_item")
                if wikibase_item:
                    wikidata_ids[int(page_id)] = wikibase_item
            
            if not wikidata_ids:
                return {pid: False for pid in page_ids}
            
            # Now query Wikidata to check if these entities are humans (P31 = Q5)
            qids = list(wikidata_ids.values())
            qids_str = " ".join(f"wd:{qid}" for qid in qids)
            
            # SPARQL query to check instance of (P31) = human (Q5)
            sparql_query = f"""
            SELECT ?item WHERE {{
                VALUES ?item {{ {qids_str} }}
                ?item wdt:P31 wd:Q5 .
            }}
            """
            
            sparql_url = "https://query.wikidata.org/sparql"
            sparql_headers = {
                "User-Agent": "CelebrityBuzzIndex/1.0 (https://celebrity-buzz-index.com; contact@example.com) httpx/0.27",
                "Accept": "application/sparql-results+json"
            }
            sparql_response = await client.get(
                sparql_url,
                params={"query": sparql_query, "format": "json"},
                timeout=15.0,
                headers=sparql_headers
            )
            
            if sparql_response.status_code == 200:
                sparql_data = sparql_response.json()
                human_qids = set()
                for binding in sparql_data.get("results", {}).get("bindings", []):
                    item_uri = binding.get("item", {}).get("value", "")
                    # Extract QID from URI like "http://www.wikidata.org/entity/Q76"
                    if "/entity/" in item_uri:
                        qid = item_uri.split("/entity/")[1]
                        human_qids.add(qid)
                
                # Map back to page_ids
                for page_id, qid in wikidata_ids.items():
                    results[page_id] = qid in human_qids
            else:
                logger.error(f"Wikidata SPARQL error: {sparql_response.status_code}")
            
            # Mark pages without wikidata IDs as non-human
            for pid in page_ids:
                if pid not in results:
                    results[pid] = False
                    
    except Exception as e:
        logger.error(f"Error checking Wikidata: {e}")
        # On error, default to False (not human)
        return {pid: False for pid in page_ids}
    
    return results

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
auth_router = APIRouter(prefix="/api/auth")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup Resend for magic links
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

# Frontend URL for magic links
FRONTEND_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://starpower-draft.preview.emergentagent.com")

# Banned words for team names (racist, offensive)
BANNED_WORDS = [
    # Racial slurs
    "nigger", "nigga", "faggot", "fag", "retard", "spic", "chink", "gook", 
    "kike", "wetback", "beaner", "coon", "darkie", "paki", "raghead", 
    "cracker", "honky", "nazi", "hitler", "kkk", "n1gger", "n1gga",
    "racist", "racism", "white power", "white supremacy", "heil", 
    "holocaust", "aryan", "fuhrer", "reich",
    "slave", "slavery", "lynch", "lynching", "genocide",
    # Common swear words
    "fuck", "fucking", "fucked", "fucker", "fck", "f*ck", "fu*k",
    "shit", "shite", "sh1t", "bullshit", "horseshit",
    "cunt", "c*nt", "cnt",
    "bitch", "b1tch", "btch",
    "ass", "arse", "asshole", "arsehole", "a$$",
    "dick", "d1ck", "dickhead",
    "cock", "c0ck", "cockhead",
    "wanker", "wank", "tosser",
    "twat", "tw4t",
    "bastard", "bstrd",
    "piss", "pissed",
    "damn", "dammit", "goddamn",
    "whore", "slut", "slag", "skank",
    "bollocks", "balls",
    # Leet speak variations
    "f4g", "r3tard", "b1tch", "sh1t", "a55", "d1ck"
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

class PriceHistoryEntry(BaseModel):
    """Model for tracking celebrity price changes over time"""
    celebrity_id: str
    celebrity_name: str
    price: float
    tier: str
    buzz_score: float
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Celebrity(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    bio: str = ""
    image: str = ""
    category: str = ""
    wiki_url: str = ""
    buzz_score: float = 0.0
    price: float = 5.0
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
    price: float
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
    estimated_price: float

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

# ==================== AUTH MODELS ====================

class User(BaseModel):
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    is_guest: bool = False
    guest_team_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserSession(BaseModel):
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MagicLinkRequest(BaseModel):
    email: EmailStr

class MagicLinkVerify(BaseModel):
    token: str

class GuestConvert(BaseModel):
    guest_team_id: str

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


async def apply_brown_bread_premium(celeb: dict, base_price: float) -> float:
    """
    Check if celebrity qualifies for Brown Bread premium pricing.
    Top 3 oldest living celebrities get premium prices:
    - #1 oldest: £15M
    - #2 oldest: £13M
    - #3 oldest: £11M
    """
    age = celeb.get("age", 0)
    is_deceased = celeb.get("is_deceased", False)
    
    # Only living celebrities with known age qualify
    if is_deceased or age < 60:
        return base_price
    
    # Get top 3 oldest living celebrities from DB
    top_elderly = await db.celebrities.find(
        {"is_deceased": False, "age": {"$gte": 60}},
        {"_id": 0, "name": 1, "age": 1}
    ).sort("age", -1).limit(3).to_list(3)
    
    # Check if this celeb is in top 3
    celeb_name = celeb.get("name", "").lower()
    brown_bread_premium_prices = [15.0, 13.0, 11.0]
    
    for idx, elderly in enumerate(top_elderly):
        if elderly.get("name", "").lower() == celeb_name:
            return brown_bread_premium_prices[idx]
    
    return base_price


async def get_brown_bread_premium_by_name(name: str) -> float:
    """
    Check if a celebrity name matches a Brown Bread premium celebrity.
    Returns the premium price if they're in top 3 oldest, otherwise 0.
    """
    name_lower = name.lower().strip()
    
    # Get top 3 oldest living celebrities from DB
    top_elderly = await db.celebrities.find(
        {"is_deceased": False, "age": {"$gte": 60}},
        {"_id": 0, "name": 1, "age": 1}
    ).sort("age", -1).limit(3).to_list(3)
    
    brown_bread_premium_prices = [15.0, 13.0, 11.0]
    
    for idx, elderly in enumerate(top_elderly):
        if elderly.get("name", "").lower() == name_lower:
            return brown_bread_premium_prices[idx]
    
    return 0.0


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
    {"name": "Bad Bunny", "reason": "Latin music & film debut", "tier": "C", "category": "musicians"},
    {"name": "Britney Spears", "reason": "Memoir & documentaries", "tier": "B", "category": "musicians"},
    {"name": "Barry Manilow", "reason": "Vegas & health news", "tier": "C", "category": "musicians"},
    # Tech/Business
    {"name": "Elon Musk", "reason": "Tech & politics headlines", "tier": "A", "category": "other"},
    {"name": "Mark Zuckerberg", "reason": "Meta & AI news", "tier": "A", "category": "other"},
    {"name": "Jeff Bezos", "reason": "Space & business", "tier": "A", "category": "other"},
    # Politicians
    {"name": "Donald Trump", "reason": "Political & legal news", "tier": "A", "category": "other"},
    {"name": "Joe Biden", "reason": "Political headlines", "tier": "A", "category": "other"},
    # Reality TV/UK
    {"name": "Katie Price", "reason": "Tabloid regular", "tier": "D", "category": "reality_tv"},
    {"name": "Holly Willoughby", "reason": "TV drama", "tier": "D", "category": "tv_actors"},
    {"name": "Phillip Schofield", "reason": "TV scandal", "tier": "D", "category": "tv_actors"},
    {"name": "Gemma Collins", "reason": "Reality star antics", "tier": "D", "category": "reality_tv"},
    {"name": "Kerry Katona", "reason": "Tabloid stories", "tier": "D", "category": "reality_tv"},
    {"name": "Simone Biles", "reason": "Olympic champion", "tier": "D", "category": "athletes"},
    # Actors
    {"name": "Tom Cruise", "reason": "Mission Impossible & stunts", "tier": "A", "category": "movie_stars"},
    {"name": "Leonardo DiCaprio", "reason": "Film & dating life", "tier": "A", "category": "movie_stars"},
    {"name": "Jennifer Lawrence", "reason": "Film & fashion", "tier": "A", "category": "movie_stars"},
    {"name": "Brad Pitt", "reason": "Films & personal life", "tier": "A", "category": "movie_stars"},
    {"name": "Angelina Jolie", "reason": "Humanitarian & acting", "tier": "A", "category": "movie_stars"},
    {"name": "Eric Dane", "reason": "Grey's Anatomy star", "tier": "D", "category": "tv_actors"},
    {"name": "Shia LaBeouf", "reason": "Film & controversy", "tier": "B", "category": "movie_stars"},
    {"name": "Margot Robbie", "reason": "Barbie & film roles", "tier": "A", "category": "movie_stars"},
    # Sports
    {"name": "Cristiano Ronaldo", "reason": "Football & brand deals", "tier": "A", "category": "athletes"},
    {"name": "David Beckham", "reason": "Business & family", "tier": "A", "category": "athletes"},
    {"name": "Lewis Hamilton", "reason": "F1 & fashion", "tier": "A", "category": "athletes"},
    # NEW - Hot due to recent news coverage
    {"name": "Timothée Chalamet", "reason": "Dune sequel & awards buzz", "tier": "A", "category": "movie_stars"},
    {"name": "Zendaya", "reason": "Challengers film & fashion icon", "tier": "A", "category": "movie_stars"},
    {"name": "Travis Kelce", "reason": "NFL star & Taylor Swift relationship", "tier": "B", "category": "athletes"},
    {"name": "Sydney Sweeney", "reason": "Euphoria star & film roles", "tier": "B", "category": "tv_actors"},
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

# Mega-stars who should ALWAYS be A-list regardless of bio analysis
GUARANTEED_A_LIST = [
    "taylor swift", "beyoncé", "beyonce", "rihanna", "drake", "kanye west", "adele",
    "ed sheeran", "ariana grande", "justin bieber", "lady gaga", "bruno mars",
    "leonardo dicaprio", "tom cruise", "brad pitt", "angelina jolie", "tom hanks",
    "julia roberts", "denzel washington", "will smith", "johnny depp", "robert downey jr",
    "dwayne johnson", "the rock", "scarlett johansson", "jennifer lawrence", "margot robbie",
    "oprah winfrey", "kim kardashian", "elon musk", "jeff bezos", "cristiano ronaldo",
    "lionel messi", "lebron james", "serena williams", "roger federer", "michael jordan",
    "david beckham", "barack obama", "donald trump", "joe biden", "bill gates",
    # British Royal Family (all variations including Wikipedia formal names)
    "prince william", "william, prince of wales", "william prince of wales",
    "prince harry", "harry, duke of sussex", "harry duke of sussex", "prince harry, duke of sussex", "prince harry duke of sussex",
    "kate middleton", "catherine, princess of wales", "catherine princess of wales",
    "queen elizabeth", "elizabeth ii", "queen elizabeth ii",
    "king charles", "charles iii", "king charles iii",
    "prince andrew", "andrew, duke of york", "andrew duke of york", "andrew mountbatten-windsor",
    "meghan markle", "meghan, duchess of sussex", "meghan duchess of sussex",
    "princess diana", "diana, princess of wales", "diana princess of wales",
    "camilla", "queen camilla", "camilla, queen consort",
    "princess anne", "anne, princess royal", "anne princess royal",
    "prince edward", "edward, duke of edinburgh", "edward duke of edinburgh",
    "princess beatrice", "princess eugenie", "zara tindall", "peter phillips",
    "prince george", "princess charlotte", "prince louis",
    # Additional mega-stars
    "britney spears", "madonna", "michael jackson", "jennifer lopez", "shakira",
    "eminem", "jay-z", "jay z", "snoop dogg", "50 cent", "nicki minaj", "cardi b",
    "selena gomez", "miley cyrus", "katy perry", "demi lovato", "the weeknd",
    "tom brady", "tiger woods", "usain bolt", "muhammad ali", "mike tyson",
    "meryl streep", "nicole kidman", "cate blanchett", "natalie portman", "emma watson",
    "george clooney", "matt damon", "ben affleck", "keanu reeves", "morgan freeman",
    "samuel l. jackson", "samuel l jackson", "al pacino", "robert de niro", "jack nicholson",
    # Sports legends
    "simone biles", "venus williams", "novak djokovic", "wayne rooney", "diego maradona",
    "pele", "pelé", "zinedine zidane", "kobe bryant", "shaquille o'neal"
]

# Keywords that indicate A-list royalty (for partial matching)
ROYAL_A_LIST_KEYWORDS = ["prince william", "prince harry", "king charles", "kate middleton", 
                          "meghan markle", "princess diana", "queen elizabeth", "prince andrew",
                          "princess anne", "prince edward", "duke of sussex", "duke of york",
                          "prince of wales", "princess of wales", "duke of edinburgh"]

# Celebrity name aliases - maps alternate names to canonical Wikipedia names
# This prevents users from adding the same person twice under different names
CELEBRITY_ALIASES = {
    # British Royals
    "prince william": "William, Prince of Wales",
    "william": "William, Prince of Wales",
    "prince harry": "Prince Harry, Duke of Sussex",
    "harry": "Prince Harry, Duke of Sussex",
    "kate middleton": "Catherine, Princess of Wales",
    "princess kate": "Catherine, Princess of Wales",
    "catherine middleton": "Catherine, Princess of Wales",
    "king charles": "Charles III",
    "prince charles": "Charles III",
    "king charles iii": "Charles III",
    "prince andrew": "Prince Andrew, Duke of York",
    "andrew mountbatten-windsor": "Prince Andrew, Duke of York",
    "meghan markle": "Meghan, Duchess of Sussex",
    "duchess of sussex": "Meghan, Duchess of Sussex",
    "queen elizabeth": "Elizabeth II",
    "queen elizabeth ii": "Elizabeth II",
    "princess diana": "Diana, Princess of Wales",
    "lady diana": "Diana, Princess of Wales",
    "camilla": "Camilla",
    "queen camilla": "Camilla",
    # Other celebs with common alternate names
    "the rock": "Dwayne Johnson",
    "dwayne 'the rock' johnson": "Dwayne Johnson",
    "jay z": "Jay-Z",
    "jay-z": "Jay-Z",
    "50 cent": "50 Cent",
    "fiddy": "50 Cent",
    "p diddy": "Sean Combs",
    "puff daddy": "Sean Combs",
    "diddy": "Sean Combs",
    "snoop dogg": "Snoop Dogg",
    "snoop dog": "Snoop Dogg",
    "lady gaga": "Lady Gaga",
    "stefani germanotta": "Lady Gaga",
}

# Reverse mapping - canonical name to all aliases (for duplicate checking)
def get_all_name_variants(canonical_name: str) -> set:
    """Get all name variants for a canonical celebrity name"""
    variants = {canonical_name.lower()}
    for alias, canonical in CELEBRITY_ALIASES.items():
        if canonical.lower() == canonical_name.lower():
            variants.add(alias.lower())
    return variants

def get_canonical_name(name: str) -> str:
    """Get the canonical name for a celebrity (or return original if no alias)"""
    return CELEBRITY_ALIASES.get(name.lower(), name)

def are_same_celebrity(name1: str, name2: str) -> bool:
    """Check if two names refer to the same celebrity"""
    canonical1 = get_canonical_name(name1).lower()
    canonical2 = get_canonical_name(name2).lower()
    return canonical1 == canonical2

# Guaranteed B-list celebrities (not quite A-list but definitely not C or D)
GUARANTEED_B_LIST = [
    "shia labeouf", "megan fox", "lindsay lohan", "paris hilton", "nicole richie",
    "pete davidson", "machine gun kelly", "mgk", "post malone", "travis scott",
    "kylie jenner", "kendall jenner", "khloe kardashian", "kourtney kardashian",
    "gigi hadid", "bella hadid", "cara delevingne", "emily ratajkowski",
    "zac efron", "channing tatum", "ryan reynolds", "chris pratt", "chris evans",
    "henry cavill", "jason momoa", "idris elba", "tom hardy", "benedict cumberbatch"
]

# Guaranteed C-list celebrities (TV personalities, chefs, etc.)
GUARANTEED_C_LIST = [
    "gordon ramsay", "jamie oliver", "simon cowell", "piers morgan", "james corden",
    "jimmy fallon", "jimmy kimmel", "ellen degeneres", "graham norton", "alan carr",
    "rylan clark", "phillip schofield", "holly willoughby", "amanda holden",
    "ant mcpartlin", "declan donnelly", "dermot o'leary", "davina mccall"
]

# ==================== HELPER FUNCTIONS ====================

async def fetch_wikipedia_autocomplete(query: str) -> List[dict]:
    """
    Search Wikipedia for celebrity suggestions - ONLY returns humans (verified via Wikidata P31=Q5).
    Uses OpenSearch API for better partial name matching, then Wikidata for human verification.
    Preserves OpenSearch relevance order.
    """
    try:
        headers = {
            "User-Agent": "CelebrityBuzzIndex/1.0 (https://celebrity-buzz-index.com; contact@example.com) httpx/0.27"
        }
        query_lower = query.lower().strip()
        
        logger.info(f"Autocomplete search for: {query}")
        
        async with httpx.AsyncClient() as client:
            # Step 1: Use OpenSearch API for better name matching
            opensearch_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={query}&limit=20&format=json"
            response = await client.get(opensearch_url, timeout=8.0, headers=headers)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            titles = data[1] if len(data) > 1 else []
            
            if not titles:
                return []
            
            # Quick title filters (obvious non-people)
            quick_skip_keywords = [
                "filmography", "discography", "bibliography", "awards", "album", 
                "list of", "category:", "template:", "wikipedia:", "soundtrack",
                "video game", "tour", "concert", "episode", "series", "season",
                "fc", "cf", "afc", "united", "club", "team", "stadium"
            ]
            
            # Filter candidates - PRESERVE ORDER from OpenSearch
            candidates = []
            for title in titles:
                title_lower = title.lower()
                
                # Quick skip obvious non-people
                if any(kw in title_lower for kw in quick_skip_keywords):
                    continue
                
                # Skip titles with colons (usually not people)
                if ":" in title:
                    continue
                
                # Skip titles starting with "The" or "List"
                if title_lower.startswith("the ") or title_lower.startswith("list "):
                    continue
                
                candidates.append(title)
            
            if not candidates:
                return []
            
            # Step 2: Get page IDs for candidates
            titles_param = "|".join(candidates[:15])
            pageids_url = f"https://en.wikipedia.org/w/api.php?action=query&titles={titles_param}&format=json"
            pageids_response = await client.get(pageids_url, timeout=8.0, headers=headers)
            
            if pageids_response.status_code != 200:
                return []
            
            pageids_data = pageids_response.json()
            pages = pageids_data.get("query", {}).get("pages", {})
            
            # Map titles to page IDs - preserve candidate order
            title_to_pageid = {}
            for page_id, page_info in pages.items():
                if page_id != "-1":
                    title_to_pageid[page_info.get("title", "")] = int(page_id)
            
            page_ids = [title_to_pageid.get(t) for t in candidates if title_to_pageid.get(t)]
            
            if not page_ids:
                return []
            
            # Step 3: Use Wikidata to verify which are humans (P31 = Q5)
            human_status = await check_wikidata_is_human(page_ids)
            
            # Filter to only humans - PRESERVE ORIGINAL CANDIDATE ORDER
            human_titles = [t for t in candidates if human_status.get(title_to_pageid.get(t), False)]
            
            if not human_titles:
                logger.info(f"No humans found for query: {query}")
                return []
            
            # Step 4: Get full page info for verified humans
            human_titles_param = "|".join(human_titles[:10])
            info_url = f"https://en.wikipedia.org/w/api.php?action=query&titles={human_titles_param}&prop=extracts|pageimages|info&exintro=true&explaintext=true&pithumbsize=300&inprop=url&format=json"
            
            info_response = await client.get(info_url, timeout=8.0, headers=headers)
            
            if info_response.status_code != 200:
                return []
            
            info_data = info_response.json()
            pages = info_data.get("query", {}).get("pages", {})
            
            # Build a lookup by title (case-insensitive)
            page_info_by_title = {}
            for pid, pinfo in pages.items():
                page_info_by_title[pinfo.get("title", "").lower()] = pinfo
            
            results = []
            seen_names = set()
            
            # Process in order of human_titles (preserves OpenSearch relevance)
            for title in human_titles:
                page_info = page_info_by_title.get(title.lower())
                
                if not page_info:
                    continue
                
                actual_title = page_info.get("title", title)
                extract = page_info.get("extract", "")[:300]
                image = page_info.get("thumbnail", {}).get("source", "")
                wiki_url = page_info.get("fullurl", f"https://en.wikipedia.org/wiki/{actual_title.replace(' ', '_')}")
                
                # Skip duplicates
                base_name = actual_title.split("(")[0].strip().lower()
                if base_name in seen_names:
                    continue
                seen_names.add(base_name)
                
                # FIRST: Check if this celeb is in the Hot Celebs cache - use that price
                hot_celebs_cache = await db.news_cache.find_one(
                    {"type": "hot_celebs_from_news_v2"},
                    {"_id": 0, "hot_celebs": 1}
                )
                hot_celeb_match = None
                if hot_celebs_cache and hot_celebs_cache.get("hot_celebs"):
                    for hc in hot_celebs_cache["hot_celebs"]:
                        if hc.get("name", "").lower() == actual_title.lower():
                            hot_celeb_match = hc
                            break
                
                if hot_celeb_match:
                    # Use Hot Celebs price (includes news premium)
                    tier = hot_celeb_match.get("tier", "D")
                    price = hot_celeb_match["price"]
                else:
                    # Check if celebrity exists in DB
                    existing = await db.celebrities.find_one(
                        {"name": {"$regex": f"^{actual_title}$", "$options": "i"}},
                        {"_id": 0, "tier": 1, "price": 1}
                    )
                    
                    if existing:
                        tier = existing.get("tier", "D")
                        price = get_dynamic_price(tier, 50, actual_title)
                    else:
                        # Check if in HOT_CELEBS_POOL for known tier
                        pool_entry = next((c for c in HOT_CELEBS_POOL if c["name"].lower() == actual_title.lower()), None)
                        if pool_entry:
                            tier = pool_entry["tier"]
                        else:
                            # Estimate tier from description (pass name for guaranteed A-list check)
                            tier = estimate_tier_from_description(extract, actual_title)
                        price = get_dynamic_price(tier, 50, actual_title)
                
                results.append({
                    "name": actual_title,
                    "description": extract or f"{actual_title} is a notable person.",
                    "image": image or f"https://ui-avatars.com/api/?name={actual_title}&size=150&background=FF0099&color=fff",
                    "wiki_url": wiki_url,
                    "estimated_tier": tier,
                    "estimated_price": price,
                    "news_premium": hot_celeb_match is not None
                })
                
                if len(results) >= 5:
                    break
            
            logger.info(f"Wikidata-verified autocomplete returning {len(results)} humans for '{query}'")
            return results
            
    except Exception as e:
        logger.error(f"Wikipedia autocomplete error: {e}")
        return []
        return []

def estimate_tier_from_description(description: str, name: str = "") -> str:
    """Estimate celebrity tier from Wikipedia description"""
    
    # First check if this is a guaranteed A-lister
    if name and name.lower() in GUARANTEED_A_LIST:
        return "A"
    
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

async def record_price_history(celebrity_id: str, celebrity_name: str, price: float, tier: str, buzz_score: float):
    """Record a price point in the celebrity's price history"""
    try:
        # Check if we already have a recent entry (within 1 hour) to avoid duplicates
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        recent_entry = await db.price_history.find_one({
            "celebrity_id": celebrity_id,
            "recorded_at": {"$gte": one_hour_ago}
        })
        
        if recent_entry:
            return  # Don't record if we have a recent entry
        
        # Record the new price point
        entry = {
            "celebrity_id": celebrity_id,
            "celebrity_name": celebrity_name,
            "price": price,
            "tier": tier,
            "buzz_score": buzz_score,
            "recorded_at": datetime.now(timezone.utc)
        }
        await db.price_history.insert_one(entry)
        logger.info(f"Recorded price history for {celebrity_name}: £{price}M ({tier})")
    except Exception as e:
        logger.error(f"Error recording price history: {e}")

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
    name_lower = name.lower() if name else ""
    
    # First check guaranteed lists (mega-star overrides)
    if name_lower in GUARANTEED_A_LIST:
        return ("A", get_base_price_for_tier("A"))
    
    # Check for royal family members using partial keyword matching
    if any(keyword in name_lower for keyword in ROYAL_A_LIST_KEYWORDS):
        return ("A", get_base_price_for_tier("A"))
    
    if name_lower in GUARANTEED_B_LIST:
        return ("B", get_base_price_for_tier("B"))
    if name_lower in GUARANTEED_C_LIST:
        return ("C", get_base_price_for_tier("C"))
    
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
                
                # Get image - use fallback if not available
                wiki_image = data.get("thumbnail", {}).get("source", "")
                if not wiki_image:
                    # Try pageimages API as backup
                    try:
                        pageimages_url = f"https://en.wikipedia.org/w/api.php?action=query&titles={name.replace(' ', '_')}&prop=pageimages&format=json&pithumbsize=400"
                        img_response = await client.get(pageimages_url, timeout=5.0, headers=headers)
                        if img_response.status_code == 200:
                            img_data = img_response.json()
                            pages = img_data.get("query", {}).get("pages", {})
                            if pages:
                                page = list(pages.values())[0]
                                wiki_image = page.get("thumbnail", {}).get("source", "")
                    except:
                        pass
                
                # If still no image, use a styled placeholder with initials
                if not wiki_image:
                    # Create a nice gradient placeholder using UI Avatars
                    clean_name = data.get("title", name).replace(" ", "+")
                    wiki_image = f"https://ui-avatars.com/api/?name={clean_name}&size=400&background=1a1a1a&color=FF0099&bold=true&format=png"
                
                return {
                    "name": data.get("title", name),
                    "bio": bio,
                    "image": wiki_image,
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
    
    # Check for specific known celebrities first - ACTORS should be checked before royals
    known_actors = ["michael caine", "ian mckellen", "morgan freeman", "judi dench", 
                    "al pacino", "helen mirren", "anthony hopkins", "maggie smith",
                    "clint eastwood", "robert de niro", "meryl streep", "jack nicholson"]
    
    for actor in known_actors:
        if actor in name_lower:
            logger.info(f"Category detection: {name} matched known actor '{actor}' - returning movie_stars")
            return "movie_stars"
    
    reality_tv_names = ["katie price", "gemma collins", "pete wicks", "joey essex", "sam faiers", 
                        "kardashian", "jenner", "love island"]
    
    # Royal names - must specifically be about royal family, not just knighted actors
    royal_names = ["prince andrew", "prince william", "prince harry", "kate middleton", "meghan markle",
                   "king charles", "queen elizabeth", "princess diana", "princess charlotte",
                   "prince george", "prince louis", "camilla"]
    
    for rn in royal_names:
        if rn in name_lower:
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
    
    # Royals - must specifically be about royal family, NOT just people with royal honors like "Sir"
    # Only match actual members of royal families
    if any(x in bio_lower for x in ["member of the british royal family", "member of the royal family",
                                     "heir to the throne", "house of windsor", "buckingham palace", 
                                     "line of succession", "son of king", "daughter of queen",
                                     "grandson of queen", "granddaughter of queen"]):
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


def determine_tier_from_bio(bio: str, name: str = "") -> str:
    """Synchronous helper to determine celebrity tier from bio text"""
    name_lower = name.lower() if name else ""
    
    # First check if this is a guaranteed A-lister (mega-star override)
    if name_lower in GUARANTEED_A_LIST:
        return "A"
    
    # Check for royal family members using partial keyword matching
    if any(keyword in name_lower for keyword in ROYAL_A_LIST_KEYWORDS):
        return "A"
    
    # Check if guaranteed B-lister
    if name_lower in GUARANTEED_B_LIST:
        return "B"
    
    # Check if guaranteed C-lister  
    if name_lower in GUARANTEED_C_LIST:
        return "C"
    
    bio_lower = bio.lower()
    
    # A-list: Major awards, legendary status
    a_list_score = sum(1 for ind in A_LIST_INDICATORS if ind in bio_lower)
    if a_list_score >= 2:
        return "A"
    
    # B-list: Award-winning, successful
    b_list_score = sum(1 for ind in B_LIST_INDICATORS if ind in bio_lower)
    if a_list_score >= 1 or b_list_score >= 2:
        return "B"
    
    # C-list: Known for appearances
    c_list_score = sum(1 for ind in C_LIST_INDICATORS if ind in bio_lower)
    if b_list_score >= 1 or c_list_score >= 1:
        return "C"
    
    return "D"


def get_category_from_bio(bio: str, name: str) -> str:
    """Synchronous wrapper for detect_category_from_bio"""
    return detect_category_from_bio(bio, name)


async def generate_celebrity_news(name: str, category: str, real_news_context: str = None) -> List[dict]:
    """Generate AI-powered news summaries for celebrity, incorporating real news if available"""
    # Get current date for context
    now = datetime.now(timezone.utc)
    current_date_str = now.strftime("%b %d, %Y")  # e.g., "Feb 21, 2026"
    one_week_ago = (now - timedelta(days=7)).strftime("%b %d, %Y")
    
    # Build context about real news events
    real_news_instruction = ""
    if real_news_context:
        real_news_instruction = f"""
            CRITICAL: This celebrity is currently in the news for: "{real_news_context}"
            The FIRST news item MUST be about this real event. Make sure to accurately reflect this news.
            If the news mentions death, illness, or a major event, this MUST be the primary focus."""
    
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"news-{uuid.uuid4()}",
            system_message=f"""You are a celebrity news aggregator. Generate realistic celebrity news headlines and summaries based on CURRENT events.
            
            IMPORTANT: Today's date is {current_date_str}. All news dates MUST be from the PAST 7 days (between {one_week_ago} and {current_date_str}). 
            DO NOT use any future dates!
            {real_news_instruction}
            
            Return a JSON array with 5 news items. Each item should have:
            - title: A catchy headline
            - summary: 1-2 sentence summary
            - source: A realistic news source name (e.g., "Entertainment Weekly", "TMZ", "People", "BBC News", "Daily Mail")
            - date: A date from the past week in format "Feb 15, 2026" - MUST be before or on {current_date_str}
            - sentiment: "positive", "neutral", or "negative"
            
            Make the news realistic and relevant to current events.
            ONLY return valid JSON array, no other text."""
        ).with_model("openai", "gpt-4o")

        prompt = f"Generate 5 recent news headlines about {name} ({category}). Today is {current_date_str}. All dates must be from the past week."
        if real_news_context:
            prompt += f" The most important current news is: {real_news_context}"
        prompt += " Return ONLY a JSON array."
        
        message = UserMessage(text=prompt)
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
            
            # Validate and fix any future dates
            if isinstance(news, list):
                for article in news:
                    if "date" in article:
                        try:
                            # Try to parse the date
                            article_date = datetime.strptime(article["date"], "%b %d, %Y")
                            # If it's in the future, set it to a random past date
                            if article_date > now:
                                days_ago = random.randint(1, 7)
                                past_date = now - timedelta(days=days_ago)
                                article["date"] = past_date.strftime("%b %d, %Y")
                        except:
                            # If parsing fails, set a default past date
                            days_ago = random.randint(1, 7)
                            past_date = now - timedelta(days=days_ago)
                            article["date"] = past_date.strftime("%b %d, %Y")
            
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
    
    # Check for Brown Bread premium pricing on each suggestion
    for suggestion in suggestions:
        premium_price = await get_brown_bread_premium_by_name(suggestion.get("name", ""))
        if premium_price > 0:
            suggestion["estimated_price"] = premium_price
            suggestion["is_brown_bread_premium"] = True
    
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
                # Recalculate tier from bio if needed (pass name for guaranteed A-list check)
                bio = celeb.get("bio", "")
                recalc_tier = estimate_tier_from_description(bio, name)
                
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
    
    # Check if this is a common name that should redirect to Wikipedia name
    # e.g., "King Charles" -> "Charles III", "Prince William" -> search Wikipedia
    wikipedia_search_name = name
    if name.lower() in CELEBRITY_ALIASES:
        # Use the canonical Wikipedia name for searching
        wikipedia_search_name = CELEBRITY_ALIASES[name.lower()]
        logger.info(f"Redirecting search from '{name}' to '{wikipedia_search_name}'")
    
    # FIRST: Check if this celeb is in the Hot Celebs cache - use that price for consistency
    hot_celebs_cache = await db.news_cache.find_one(
        {"type": "hot_celebs_from_news_v4"},
        {"_id": 0}
    )
    hot_celeb_match = None
    if hot_celebs_cache and hot_celebs_cache.get("hot_celebs"):
        for hc in hot_celebs_cache["hot_celebs"]:
            hc_name = hc.get("name", "").lower()
            # Check both original name and wikipedia name
            if hc_name == name.lower() or hc_name == wikipedia_search_name.lower():
                hot_celeb_match = hc
                break
            # Also check if they're aliases of each other
            if are_same_celebrity(hc.get("name", ""), name) or are_same_celebrity(hc.get("name", ""), wikipedia_search_name):
                hot_celeb_match = hc
                break
    
    # Check if already in database (try both original name and Wikipedia name)
    existing = await db.celebrities.find_one({"name": {"$regex": f"^{name}$", "$options": "i"}}, {"_id": 0})
    if not existing and wikipedia_search_name != name:
        existing = await db.celebrities.find_one({"name": {"$regex": f"^{wikipedia_search_name}$", "$options": "i"}}, {"_id": 0})
    
    if existing:
        # Check if this is a guaranteed A-lister (mega-star override)
        celeb_name = existing.get("name", name)
        is_mega_star = celeb_name.lower() in GUARANTEED_A_LIST
        
        # Check for royal keywords in name
        is_royal = any(keyword in celeb_name.lower() for keyword in ROYAL_A_LIST_KEYWORDS)
        
        # If this celeb is in Hot Celebs, use that price (includes news premium)
        if hot_celeb_match:
            existing["price"] = hot_celeb_match["price"]
            # Use A-tier for mega-stars regardless of what's in cache
            existing["tier"] = "A" if (is_mega_star or is_royal) else hot_celeb_match.get("tier", existing.get("tier", "D"))
            existing["news_premium"] = hot_celeb_match.get("news_premium", False)
            existing["trending_tag"] = hot_celeb_match.get("trending_tag", "")
        else:
            # Use CONSISTENT pricing - same as Hot Celebs (buzz_score = 50)
            # Use A-tier for mega-stars
            tier = "A" if (is_mega_star or is_royal) else existing.get("tier", "D")
            existing["tier"] = tier
            default_buzz = 50
            new_price = get_dynamic_price(tier, default_buzz, celeb_name)
            
            # Check if this celeb qualifies for Brown Bread premium pricing
            new_price = await apply_brown_bread_premium(existing, new_price)
            existing["price"] = new_price
        
        # Regenerate news if empty or missing
        if not existing.get("news") or len(existing.get("news", [])) == 0:
            category = existing.get("category", "other")
            # Get real news context from hot celebs if available
            real_news_context = hot_celeb_match.get("hot_reason") if hot_celeb_match else None
            news = await generate_celebrity_news(celeb_name, category, real_news_context)
            existing["news"] = news
            # Update in database
            await db.celebrities.update_one(
                {"id": existing.get("id")},
                {"$set": {"news": news}}
            )
        
        # Record price history
        await record_price_history(
            celebrity_id=existing.get("id", ""),
            celebrity_name=existing.get("name", ""),
            price=existing["price"],
            tier=existing.get("tier", "D"),
            buzz_score=existing.get("buzz_score", 50)
        )
        
        return {"celebrity": existing}
    
    # Fetch from Wikipedia using the Wikipedia search name (handles aliases like "King Charles" -> "Charles III")
    wiki_info = await fetch_wikipedia_info(wikipedia_search_name)
    logger.info(f"Wiki info for {wikipedia_search_name}: bio_length={len(wiki_info.get('bio', ''))}, bio_preview={wiki_info.get('bio', '')[:100]}")
    
    # Use override category if provided, otherwise detect from bio
    if override_category:
        category = override_category
    else:
        category = detect_category_from_bio(wiki_info.get("bio", ""), wiki_info["name"])
    
    # Calculate celebrity tier based on bio
    tier, base_price = await calculate_celebrity_tier(wiki_info.get("bio", ""), wiki_info["name"])
    
    # Generate news - pass real news context if available from hot celebs
    real_news_context = hot_celeb_match.get("hot_reason") if hot_celeb_match else None
    news = await generate_celebrity_news(wiki_info["name"], category, real_news_context)
    
    # Calculate buzz score
    buzz_score = calculate_buzz_score(news)
    
    # Final price using CONSISTENT buzz (50) for initial display price
    default_buzz = 50
    price = get_dynamic_price(tier, default_buzz, wiki_info["name"])
    
    # If this celeb is in Hot Celebs, use that price (includes news premium)
    if hot_celeb_match:
        price = hot_celeb_match["price"]
        tier = hot_celeb_match.get("tier", tier)
    
    # Check if celebrity is deceased (look for death date in bio)
    bio_lower = wiki_info.get("bio", "").lower()
    is_deceased = any(x in bio_lower for x in ["was a ", "died ", "passed away", "1900–", "1910–", "1920–", "1930–", "1940–", "1950–", "1960–", "1970–", "1980–", "1990–", "2000–", "2010–", "2020–"])
    
    # Extract birth year - prefer wiki_info birth_year, fallback to bio extraction
    birth_year = wiki_info.get("birth_year", 0)
    if not birth_year:
        birth_year = extract_birth_year_from_bio(wiki_info.get("bio", ""))
    age = calculate_age(birth_year)
    
    # Check for Brown Bread premium pricing (for elderly celebrities) - only if not already in Hot Celebs
    if not hot_celeb_match:
        temp_celeb = {"name": wiki_info["name"], "age": age, "is_deceased": is_deceased}
        price = await apply_brown_bread_premium(temp_celeb, price)
    
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
    
    # Record initial price history
    await record_price_history(
        celebrity_id=celebrity.id,
        celebrity_name=celebrity.name,
        price=price,
        tier=tier,
        buzz_score=buzz_score
    )
    
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

@api_router.get("/celebrity/{celebrity_id}/price-history")
async def get_celebrity_price_history(celebrity_id: str, limit: int = 30):
    """Get price history for a celebrity"""
    # Get the celebrity first
    celebrity = await db.celebrities.find_one({"id": celebrity_id}, {"_id": 0})
    if not celebrity:
        raise HTTPException(status_code=404, detail="Celebrity not found")
    
    # Get price history entries, sorted by date descending
    history = await db.price_history.find(
        {"celebrity_id": celebrity_id},
        {"_id": 0}
    ).sort("recorded_at", -1).limit(limit).to_list(limit)
    
    # Convert datetime objects to ISO strings
    for entry in history:
        if isinstance(entry.get("recorded_at"), datetime):
            entry["recorded_at"] = entry["recorded_at"].isoformat()
    
    # If no history, return current price as the only entry
    if not history:
        history = [{
            "celebrity_id": celebrity_id,
            "celebrity_name": celebrity.get("name", ""),
            "price": celebrity.get("price", 5),
            "tier": celebrity.get("tier", "D"),
            "buzz_score": celebrity.get("buzz_score", 0),
            "recorded_at": datetime.now(timezone.utc).isoformat()
        }]
    
    return {
        "celebrity_name": celebrity.get("name", ""),
        "current_price": celebrity.get("price", 5),
        "current_tier": celebrity.get("tier", "D"),
        "history": history
    }

@api_router.get("/price-history/celebrity-name/{name}")
async def get_price_history_by_name(name: str, limit: int = 30):
    """Get price history for a celebrity by name"""
    # Get the celebrity first
    celebrity = await db.celebrities.find_one(
        {"name": {"$regex": f"^{name}$", "$options": "i"}}, 
        {"_id": 0}
    )
    if not celebrity:
        raise HTTPException(status_code=404, detail="Celebrity not found")
    
    celebrity_id = celebrity.get("id", "")
    
    # Get price history entries
    history = await db.price_history.find(
        {"celebrity_id": celebrity_id},
        {"_id": 0}
    ).sort("recorded_at", -1).limit(limit).to_list(limit)
    
    # Convert datetime objects to ISO strings
    for entry in history:
        if isinstance(entry.get("recorded_at"), datetime):
            entry["recorded_at"] = entry["recorded_at"].isoformat()
    
    # If no history, return current price
    if not history:
        history = [{
            "celebrity_id": celebrity_id,
            "celebrity_name": celebrity.get("name", ""),
            "price": celebrity.get("price", 5),
            "tier": celebrity.get("tier", "D"),
            "buzz_score": celebrity.get("buzz_score", 0),
            "recorded_at": datetime.now(timezone.utc).isoformat()
        }]
    
    return {
        "celebrity_name": celebrity.get("name", ""),
        "current_price": celebrity.get("price", 5),
        "current_tier": celebrity.get("tier", "D"),
        "history": history
    }

@api_router.get("/celebrities/category/{category}")
async def get_celebrities_by_category(category: str):
    """Get celebrities by category with correct dynamic pricing"""
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
    
    # Recalculate dynamic prices for all celebrities - use CONSISTENT buzz (50)
    default_buzz = 50
    for celeb in celebrities:
        tier = celeb.get("tier", "D")
        celeb["price"] = get_dynamic_price(tier, default_buzz, celeb.get("name", ""))
    
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
    """Get 15+ hot celebrities WHO ARE ACTUALLY IN THE NEWS from the PAST 7 DAYS - Monday to Monday refresh"""
    
    now = datetime.now(timezone.utc)
    
    # Calculate the start of the current week (Monday 00:00 UTC)
    days_since_monday = now.weekday()  # Monday = 0
    current_week_start = now - timedelta(days=days_since_monday, hours=now.hour, minutes=now.minute, seconds=now.second, microseconds=now.microsecond)
    
    # News window: past 7 days (rolling week)
    news_cutoff = now - timedelta(days=7)
    
    # Check cache first (1 hour cache) but invalidate on Monday (new week)
    cached = await db.news_cache.find_one(
        {"type": "hot_celebs_from_news_v4"},  # New version with 7-day rolling window
        {"_id": 0}
    )
    
    if cached and cached.get("updated_at") and cached.get("week_start"):
        cache_time = datetime.fromisoformat(cached["updated_at"])
        cache_week_start = datetime.fromisoformat(cached["week_start"])
        cache_age = now - cache_time
        
        # Use cache if: 
        # 1. Less than 1 hour old AND
        # 2. From the same week (cache invalidates every Monday)
        if cache_age.total_seconds() < 3600 and cache_week_start >= current_week_start:
            return {"hot_celebs": cached.get("hot_celebs", [])}
    
    headers = {
        "User-Agent": "CelebrityBuzzIndex/1.0 (https://celebrity-buzz-index.com; contact@example.com) httpx/0.27"
    }
    
    # Large list of well-known celebrities to check against news
    KNOWN_CELEBRITIES = [
        # A-List Actors
        "Taylor Swift", "Beyoncé", "Rihanna", "Drake", "Kanye West", "Adele", "Ed Sheeran",
        "Lady Gaga", "Justin Bieber", "Ariana Grande", "Dua Lipa", "Harry Styles", "Billie Eilish",
        "The Weeknd", "Post Malone", "Bad Bunny", "Doja Cat", "Lizzo", "Cardi B", "Nicki Minaj",
        # Hollywood
        "Leonardo DiCaprio", "Brad Pitt", "Angelina Jolie", "Tom Cruise", "Jennifer Aniston",
        "Johnny Depp", "Amber Heard", "Margot Robbie", "Scarlett Johansson", "Chris Hemsworth",
        "Robert Downey Jr.", "Tom Holland", "Zendaya", "Timothée Chalamet", "Florence Pugh",
        "Sydney Sweeney", "Jennifer Lawrence", "Anne Hathaway", "Emma Stone", "Ryan Gosling",
        "Dwayne Johnson", "Will Smith", "Jada Pinkett Smith", "Chris Rock", "Kevin Hart",
        "Adam Sandler", "Ben Affleck", "Jennifer Lopez", "George Clooney", "Matt Damon",
        "Meryl Streep", "Nicole Kidman", "Sandra Bullock", "Julia Roberts", "Reese Witherspoon",
        # British
        "David Beckham", "Victoria Beckham", "Gordon Ramsay", "Simon Cowell", "Adele",
        "Daniel Craig", "Idris Elba", "Tom Hardy", "Benedict Cumberbatch", "Henry Cavill",
        "Emma Watson", "Kate Winslet", "Judi Dench", "Helen Mirren", "Ian McKellen",
        "Michael Caine", "Anthony Hopkins", "Gary Oldman", "Christian Bale", "Hugh Grant",
        # Royals
        "Prince Harry", "Meghan Markle", "Prince William", "Kate Middleton", "King Charles",
        "Prince Andrew", "Princess Beatrice", "Princess Eugenie", "Camilla",
        # Reality TV / UK
        "Katie Price", "Kerry Katona", "Gemma Collins", "Peter Andre", "Katie Hopkins",
        "Piers Morgan", "Holly Willoughby", "Phillip Schofield", "Amanda Holden", "Ant McPartlin",
        "Declan Donnelly", "Rylan Clark", "Stacey Solomon", "Joe Swash", "Coleen Rooney",
        # Sports
        "Cristiano Ronaldo", "Lionel Messi", "Neymar", "Kylian Mbappé", "Erling Haaland",
        "Lewis Hamilton", "Max Verstappen", "Serena Williams", "Roger Federer", "Rafael Nadal",
        "LeBron James", "Michael Jordan", "Tom Brady", "Patrick Mahomes", "Travis Kelce",
        "Simone Biles", "Usain Bolt", "Tiger Woods", "Conor McGregor", "Floyd Mayweather",
        "David Beckham", "Wayne Rooney", "Harry Kane", "Marcus Rashford", "Bukayo Saka",
        # Tech/Business
        "Elon Musk", "Jeff Bezos", "Mark Zuckerberg", "Bill Gates", "Kim Kardashian",
        "Kylie Jenner", "Kendall Jenner", "Kourtney Kardashian", "Khloé Kardashian",
        # TV Stars
        "Oprah Winfrey", "Ellen DeGeneres", "Jimmy Fallon", "Jimmy Kimmel", "Trevor Noah",
        "James Corden", "Graham Norton", "Jonathan Ross", "Alan Carr", "David Letterman",
        # Recently in news (2024-2025)
        "Britney Spears", "Shia LaBeouf", "Mia Goth", "Barry Manilow", "Eric Dane",
        "Liza Minnelli", "Jessica Alba", "Scott Wolf", "Tyreek Hill", "Jonathan Owens",
        "Sam Fender", "Cillian Murphy", "Robert Pattinson", "Pedro Pascal", "Jenna Ortega",
        "Aubrey Plaza", "Glen Powell", "Jacob Elordi", "Barry Keoghan", "Paul Mescal",
        # More current celebs
        "Taylor Lautner", "Selena Gomez", "Hailey Bieber", "Gigi Hadid", "Bella Hadid",
        "Cara Delevingne", "Emily Ratajkowski", "Megan Fox", "Machine Gun Kelly", "Pete Davidson",
        "Kim Petras", "Sam Smith", "Lil Nas X", "Megan Thee Stallion", "Ice Spice",
    ]
    
    # RSS feeds to scan
    rss_sources = [
        ("https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml", "BBC News"),
        ("https://www.tmz.com/rss.xml", "TMZ"),
        ("https://people.com/feed/", "People"),
        ("https://pagesix.com/feed/", "Page Six"),
        ("https://www.dailymail.co.uk/tvshowbiz/index.rss", "Daily Mail"),
        ("https://www.theguardian.com/lifeandstyle/celebrities/rss", "The Guardian"),
    ]
    
    # Collect all headlines
    all_headlines = []
    
    async with httpx.AsyncClient() as client:
        for rss_url, source_name in rss_sources:
            try:
                response = await client.get(rss_url, timeout=10.0, headers=headers)
                if response.status_code == 200:
                    content = response.text
                    items = content.split("<item>")[1:30]  # Get 30 items per source
                    
                    for item in items:
                        try:
                            title_start = item.find("<title>") + 7
                            title_end = item.find("</title>")
                            title = item[title_start:title_end].replace("<![CDATA[", "").replace("]]>", "").strip()
                            title = decode_html_entities(title)
                            
                            # Try to extract publication date
                            pub_date = None
                            if "<pubDate>" in item:
                                date_start = item.find("<pubDate>") + 9
                                date_end = item.find("</pubDate>")
                                date_str = item[date_start:date_end].strip()
                                try:
                                    # Parse RSS date format (e.g., "Mon, 09 Dec 2024 12:00:00 GMT")
                                    from email.utils import parsedate_to_datetime
                                    pub_date = parsedate_to_datetime(date_str)
                                except:
                                    pass
                            
                            # Only include if: no date (assume recent) OR within past 7 days
                            if pub_date is None or pub_date >= news_cutoff:
                                all_headlines.append({"title": title, "source": source_name, "date": pub_date})
                            
                        except:
                            continue
            except Exception as e:
                logger.error(f"Error fetching RSS from {source_name}: {e}")
                continue
        
        # Check which known celebrities appear in headlines from PAST 7 DAYS
        celeb_mentions = {}
        all_text = " ".join([h["title"].lower() for h in all_headlines])
        
        for celeb_name in KNOWN_CELEBRITIES:
            name_lower = celeb_name.lower()
            # Check for full name or last name (for unique last names)
            name_parts = name_lower.split()
            
            # Count mentions
            mention_count = all_text.count(name_lower)
            
            # Also check last name for unique surnames
            if len(name_parts) > 1:
                last_name = name_parts[-1]
                # Only count last name if it's unique enough (not common names)
                common_last_names = ["smith", "jones", "williams", "brown", "davis", "miller", "wilson", "moore", "taylor", "anderson", "white", "harris", "martin", "king", "lee"]
                if last_name not in common_last_names and len(last_name) > 4:
                    mention_count += all_text.count(f" {last_name} ") + all_text.count(f" {last_name}'")
            
            if mention_count > 0:
                # Find the headline that mentions them
                headline = ""
                for h in all_headlines:
                    if name_lower in h["title"].lower() or (len(name_parts) > 1 and name_parts[-1] in h["title"].lower()):
                        headline = h["title"]
                        break
                
                celeb_mentions[celeb_name] = {
                    "count": mention_count,
                    "headline": headline
                }
        
        # Sort by mention count
        sorted_celebs = sorted(celeb_mentions.items(), key=lambda x: x[1]["count"], reverse=True)
        
        # Fetch details for top celebrities - need at least 15 with real photos
        hot_list = []
        
        for name, data in sorted_celebs:
            if len(hot_list) >= 18:  # Get a few extra in case some don't have photos
                break
            
            try:
                wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{name.replace(' ', '_')}"
                response = await client.get(wiki_url, timeout=5.0, headers=headers)
                
                if response.status_code == 200:
                    wiki_data = response.json()
                    image = wiki_data.get("thumbnail", {}).get("source", "")
                    
                    # ONLY include if they have a real photo
                    if image and "wikipedia" in image.lower():
                        bio = wiki_data.get("extract", "")
                        actual_name = wiki_data.get("title", name)
                        tier = determine_tier_from_bio(bio, actual_name)
                        category = get_category_from_bio(bio, actual_name)
                        base_price = get_dynamic_price(tier, 50, actual_name)
                        
                        # Apply NEWS PREMIUM based on mention count
                        # More mentions = higher price (capped at 3x base)
                        mention_count = data["count"]
                        if mention_count >= 5:
                            news_multiplier = 3.0  # 5+ mentions = 3x price
                        elif mention_count >= 3:
                            news_multiplier = 2.0  # 3-4 mentions = 2x price
                        elif mention_count >= 2:
                            news_multiplier = 1.5  # 2 mentions = 1.5x price
                        else:
                            news_multiplier = 1.0
                        
                        price = round(base_price * news_multiplier, 1)
                        # Cap at £15M unless Brown Bread premium
                        price = min(price, 15.0)
                        
                        hot_reason = data["headline"][:70] + "..." if data["headline"] else "Trending in news"
                        
                        # Add trending indicator if high mentions
                        trending_tag = ""
                        if mention_count >= 5:
                            trending_tag = "🔥🔥🔥"
                        elif mention_count >= 3:
                            trending_tag = "🔥🔥"
                        elif mention_count >= 2:
                            trending_tag = "🔥"
                        
                        hot_list.append({
                            "name": actual_name,
                            "tier": tier,
                            "category": category,
                            "price": price,
                            "base_price": base_price,
                            "news_premium": news_multiplier > 1.0,
                            "trending_tag": trending_tag,
                            "hot_reason": hot_reason,
                            "image": image,
                            "mention_count": mention_count
                        })
                        
                        # Store in DB for consistency with autocomplete
                        actual_name = wiki_data.get("title", name)
                        existing = await db.celebrities.find_one({"name": {"$regex": f"^{actual_name}$", "$options": "i"}})
                        if not existing:
                            await db.celebrities.update_one(
                                {"name": actual_name},
                                {"$set": {
                                    "name": actual_name,
                                    "tier": tier,
                                    "category": category,
                                    "image": image,
                                    "bio": bio[:500],
                                    "updated_at": datetime.now(timezone.utc).isoformat()
                                }},
                                upsert=True
                            )
            except Exception as e:
                logger.error(f"Error fetching {name}: {e}")
                continue
        
        # Only use fallback if we have very few celebs from news (less than 8)
        # This ensures we prioritize actual news mentions
        if len(hot_list) < 8:
            fallback_names = [c["name"] for c in HOT_CELEBS_POOL if c["name"] not in [h["name"] for h in hot_list]]
            random.shuffle(fallback_names)
            
            for name in fallback_names:
                if len(hot_list) >= 12:  # Only fill up to 12 with fallback
                    break
                
                try:
                    wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{name.replace(' ', '_')}"
                    response = await client.get(wiki_url, timeout=5.0, headers=headers)
                    
                    if response.status_code == 200:
                        wiki_data = response.json()
                        image = wiki_data.get("thumbnail", {}).get("source", "")
                        
                        if image and "wikipedia" in image.lower():
                            bio = wiki_data.get("extract", "")
                            actual_name = wiki_data.get("title", name)
                            tier = determine_tier_from_bio(bio, actual_name)
                            category = get_category_from_bio(bio, actual_name)
                            price = get_dynamic_price(tier, 50, actual_name)
                            
                            # Find reason from pool
                            pool_entry = next((c for c in HOT_CELEBS_POOL if c["name"] == name), None)
                            hot_reason = pool_entry["reason"] if pool_entry else "Always making headlines"
                            
                            hot_list.append({
                                "name": actual_name,
                                "tier": tier,
                                "category": category,
                                "price": price,
                                "base_price": price,
                                "news_premium": False,
                                "trending_tag": "",
                                "hot_reason": hot_reason,
                                "image": image,
                                "mention_count": 0
                            })
                except:
                    continue
    
    # Cache the results with week tracking (refreshes every Monday)
    if hot_list:
        await db.news_cache.update_one(
            {"type": "hot_celebs_from_news_v4"},
            {"$set": {
                "hot_celebs": hot_list,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "week_start": current_week_start.isoformat(),
                "news_cutoff": news_cutoff.isoformat()
            }},
            upsert=True
        )
    
    return {"hot_celebs": hot_list}


def extract_celebrity_names_from_headline(headline: str) -> List[str]:
    """Extract potential celebrity names from news headlines"""
    names = []
    
    # Common patterns:
    # "Taylor Swift announces..." -> "Taylor Swift"
    # "Brad Pitt and Angelina Jolie..." -> "Brad Pitt", "Angelina Jolie"
    # "Eric Dane's death..." -> "Eric Dane"
    # "Meghan King Accuses Jim Edmonds" -> "Meghan King", "Jim Edmonds"
    
    # Skip headlines that are clearly not about specific people
    skip_starts = ["the ", "how ", "why ", "what ", "when ", "where ", "best ", "top ", "new "]
    if any(headline.lower().startswith(skip) for skip in skip_starts):
        return names
    
    # Pattern 1: Name at start followed by verb or possessive
    # Match: "First Last" or "First Middle Last"
    name_pattern = r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})(?:'s|:|\s+(?:says|announces|reveals|dies|dead|wins|loses|accused|claims|faces|fires|quits|returns|slams|blasts|responds|breaks|speaks|shares|posts|confirms|denies|splits|divorces|marries|pregnant|engaged|announces|launches|releases|signs|joins|leaves))"
    match = re.search(name_pattern, headline)
    if match:
        names.append(match.group(1))
    
    # Pattern 2: "Name and Name" pattern
    and_pattern = r"([A-Z][a-z]+\s+[A-Z][a-z]+)\s+and\s+([A-Z][a-z]+\s+[A-Z][a-z]+)"
    and_match = re.search(and_pattern, headline)
    if and_match:
        names.append(and_match.group(1))
        names.append(and_match.group(2))
    
    # Pattern 3: "Name Name's" possessive
    poss_pattern = r"([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)'s"
    poss_match = re.search(poss_pattern, headline)
    if poss_match:
        names.append(poss_match.group(1))
    
    # Pattern 4: Names followed by colon (common in headlines)
    colon_pattern = r"^([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?):"
    colon_match = re.search(colon_pattern, headline)
    if colon_match:
        names.append(colon_match.group(1))
    
    # Pattern 5: "Accuses Name Name" or "with Name Name"
    accuses_pattern = r"(?:accuses|with|and|vs|against|featuring)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)"
    accuses_matches = re.findall(accuses_pattern, headline, re.IGNORECASE)
    names.extend(accuses_matches)
    
    # Clean and dedupe
    cleaned = []
    for name in names:
        name = name.strip()
        # Skip if too short or too long
        if len(name) < 5 or len(name) > 40:
            continue
        # Skip common non-name phrases
        skip_phrases = ["the ", "real housewives", "love island", "strictly come", "good morning", 
                       "this morning", "breaking news", "just in", "watch video"]
        if any(skip in name.lower() for skip in skip_phrases):
            continue
        if name not in cleaned:
            cleaned.append(name)
    
    return cleaned

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
    # Check cache (24 hour cache for real news)
    cached = await db.news_cache.find_one(
        {"type": "todays_news_real"},
        {"_id": 0}
    )
    
    if cached and cached.get("updated_at"):
        cache_time = datetime.fromisoformat(cached["updated_at"])
        cache_age = datetime.now(timezone.utc) - cache_time
        if cache_age.total_seconds() < 86400:  # 24 hour cache (86400 seconds)
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
    
    celeb_name = celebrity.get("name", "")
    
    # Check if already in team (including alternate name variants)
    # This prevents adding "Prince William" if "William, Prince of Wales" is already in team
    for c in team.get("celebrities", []):
        existing_name = c.get("name", "")
        # Check exact match
        if c["celebrity_id"] == data.celebrity_id:
            raise HTTPException(status_code=400, detail="Celebrity already in team")
        # Check if same person under different name
        if are_same_celebrity(existing_name, celeb_name):
            raise HTTPException(status_code=400, detail=f"This celebrity is already in your team as '{existing_name}'")
    
    # RECALCULATE PRICE using consistent pricing (same as Hot Celebs and search)
    tier = celebrity.get("tier", "D")
    default_buzz = 50
    price = get_dynamic_price(tier, default_buzz, celeb_name)
    
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


# ==================== AUTH ENDPOINTS ====================

async def get_current_user(request: Request) -> Optional[dict]:
    """Get current user from session token in cookie or Authorization header"""
    session_token = None
    
    # Check Authorization header first
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        session_token = auth_header[7:]
    
    # Fallback to cookie
    if not session_token:
        session_token = request.cookies.get("session_token")
    
    if not session_token:
        return None
    
    # Find session
    session = await db.user_sessions.find_one(
        {"session_token": session_token, "expires_at": {"$gt": datetime.now(timezone.utc).isoformat()}},
        {"_id": 0}
    )
    
    if not session:
        return None
    
    # Find user
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    return user


def create_session_token() -> str:
    """Generate a secure session token"""
    return str(uuid.uuid4()) + "-" + str(uuid.uuid4())


async def create_user_session(user_id: str) -> str:
    """Create a new session for user"""
    session_token = create_session_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    
    session = {
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.user_sessions.insert_one(session)
    return session_token


@auth_router.get("/me")
async def get_me(request: Request):
    """Get current user info"""
    user = await get_current_user(request)
    if not user:
        return {"user": None, "is_authenticated": False}
    
    # Get user's team
    team = await db.teams.find_one({"owner_user_id": user["user_id"]}, {"_id": 0})
    
    return {
        "user": user,
        "team": team,
        "is_authenticated": True
    }


@auth_router.post("/magic-link/send")
async def send_magic_link(request: MagicLinkRequest):
    """Send magic link email for passwordless login"""
    email = request.email.lower().strip()
    
    # Generate magic link token
    token = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    # Store magic link
    await db.magic_links.update_one(
        {"email": email},
        {"$set": {
            "email": email,
            "token": token,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "used": False
        }},
        upsert=True
    )
    
    # Send email
    magic_link_url = f"{FRONTEND_URL}?auth_token={token}"
    
    if RESEND_API_KEY:
        try:
            resend.Emails.send({
                "from": SENDER_EMAIL,
                "to": email,
                "subject": "Sign in to Celebrity Buzz Index",
                "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #FF0099; margin-bottom: 20px;">Celebrity Buzz Index</h1>
                    <p style="font-size: 16px; color: #333;">Click the link below to sign in:</p>
                    <a href="{magic_link_url}" style="display: inline-block; background: linear-gradient(90deg, #FF0099, #00F0FF); color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; font-weight: bold;">
                        Sign In to Celebrity Buzz Index
                    </a>
                    <p style="font-size: 14px; color: #666; margin-top: 20px;">This link expires in 1 hour.</p>
                    <p style="font-size: 12px; color: #999;">If you didn't request this email, you can safely ignore it.</p>
                </div>
                """
            })
            logger.info(f"Magic link sent to {email}")
        except Exception as e:
            logger.error(f"Failed to send magic link: {e}")
            # In development, return the token for testing
            return {"success": True, "message": "Magic link sent! Check your email.", "dev_token": token}
    else:
        # No Resend API key - return token for testing
        logger.warning("No RESEND_API_KEY set - returning token for testing")
        return {"success": True, "message": "Magic link generated (email not sent - dev mode)", "dev_token": token}
    
    return {"success": True, "message": "Magic link sent! Check your email."}


@auth_router.post("/magic-link/verify")
async def verify_magic_link(request: MagicLinkVerify, response: Response):
    """Verify magic link token and create session"""
    token = request.token
    
    # Find magic link
    magic_link = await db.magic_links.find_one(
        {"token": token, "used": False, "expires_at": {"$gt": datetime.now(timezone.utc).isoformat()}},
        {"_id": 0}
    )
    
    if not magic_link:
        raise HTTPException(status_code=400, detail="Invalid or expired magic link")
    
    email = magic_link["email"]
    
    # Mark magic link as used
    await db.magic_links.update_one({"token": token}, {"$set": {"used": True}})
    
    # Find or create user
    user = await db.users.find_one({"email": email}, {"_id": 0})
    
    if not user:
        # Create new user
        user_id = str(uuid.uuid4())
        user = {
            "user_id": user_id,
            "email": email,
            "name": email.split("@")[0],
            "picture": f"https://ui-avatars.com/api/?name={email.split('@')[0]}&background=FF0099&color=fff",
            "is_guest": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user)
        if '_id' in user:
            del user['_id']
    
    # Create session
    session_token = await create_user_session(user["user_id"])
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=30 * 24 * 60 * 60  # 30 days
    )
    
    return {
        "success": True,
        "user": user,
        "session_token": session_token
    }


@auth_router.post("/google/callback")
async def google_auth_callback(request: Request, response: Response):
    """Handle Google OAuth callback"""
    body = await request.json()
    google_token = body.get("credential") or body.get("token")
    
    if not google_token:
        raise HTTPException(status_code=400, detail="No Google token provided")
    
    # Verify Google token
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={google_token}",
                timeout=10.0
            )
            
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail="Invalid Google token")
            
            google_user = resp.json()
    except Exception as e:
        logger.error(f"Google token verification failed: {e}")
        raise HTTPException(status_code=400, detail="Failed to verify Google token")
    
    email = google_user.get("email", "").lower()
    name = google_user.get("name", email.split("@")[0])
    picture = google_user.get("picture", "")
    
    if not email:
        raise HTTPException(status_code=400, detail="No email in Google token")
    
    # Find or create user
    user = await db.users.find_one({"email": email}, {"_id": 0})
    
    if not user:
        user_id = str(uuid.uuid4())
        user = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture or f"https://ui-avatars.com/api/?name={name}&background=FF0099&color=fff",
            "is_guest": False,
            "google_id": google_user.get("sub"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user)
        if '_id' in user:
            del user['_id']
    
    # Create session
    session_token = await create_user_session(user["user_id"])
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=30 * 24 * 60 * 60
    )
    
    return {
        "success": True,
        "user": user,
        "session_token": session_token
    }


@auth_router.post("/guest/convert")
async def convert_guest_to_user(request: Request, body: GuestConvert, response: Response):
    """Link a guest team to an authenticated user"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    guest_team_id = body.guest_team_id
    
    # Find guest team
    guest_team = await db.teams.find_one({"id": guest_team_id}, {"_id": 0})
    if not guest_team:
        raise HTTPException(status_code=404, detail="Guest team not found")
    
    # Check if user already has a team
    existing_team = await db.teams.find_one({"owner_user_id": user["user_id"]}, {"_id": 0})
    
    if existing_team:
        # Merge guest team celebrities into existing team
        guest_celebs = guest_team.get("celebrities", [])
        existing_celebs = existing_team.get("celebrities", [])
        
        # Add guest celebs that aren't already in team
        existing_celeb_ids = {c["id"] for c in existing_celebs}
        for celeb in guest_celebs:
            if celeb["id"] not in existing_celeb_ids and len(existing_celebs) < 10:
                existing_celebs.append(celeb)
        
        # Update team
        await db.teams.update_one(
            {"id": existing_team["id"]},
            {"$set": {"celebrities": existing_celebs}}
        )
        
        # Delete guest team
        await db.teams.delete_one({"id": guest_team_id})
        
        return {"success": True, "team": existing_team, "merged": True}
    else:
        # Transfer ownership of guest team to user
        await db.teams.update_one(
            {"id": guest_team_id},
            {"$set": {
                "owner_user_id": user["user_id"],
                "is_guest": False
            }}
        )
        
        guest_team["owner_user_id"] = user["user_id"]
        guest_team["is_guest"] = False
        
        return {"success": True, "team": guest_team, "merged": False}


@auth_router.post("/logout")
async def logout(request: Request, response: Response):
    """Log out user by deleting session"""
    session_token = request.cookies.get("session_token")
    auth_header = request.headers.get("Authorization", "")
    
    if auth_header.startswith("Bearer "):
        session_token = auth_header[7:]
    
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    
    response.delete_cookie("session_token")
    
    return {"success": True, "message": "Logged out"}


@auth_router.post("/session")
async def exchange_session(request: Request, response: Response):
    """
    Exchange Emergent Auth session_id for user session.
    This endpoint receives session_id from frontend after Google OAuth redirect.
    REMINDER: The redirect URL on frontend MUST NOT be hardcoded - use window.location.origin
    """
    body = await request.json()
    session_id = body.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="No session_id provided")
    
    # Call Emergent Auth to get user data
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": session_id},
                timeout=15.0
            )
            
            if resp.status_code != 200:
                logger.error(f"Emergent Auth session-data error: {resp.status_code} - {resp.text}")
                raise HTTPException(status_code=400, detail="Invalid session_id")
            
            auth_data = resp.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Auth service timeout")
    except Exception as e:
        logger.error(f"Emergent Auth session exchange failed: {e}")
        raise HTTPException(status_code=400, detail="Failed to exchange session")
    
    email = auth_data.get("email", "").lower()
    name = auth_data.get("name", email.split("@")[0])
    picture = auth_data.get("picture", "")
    
    if not email:
        raise HTTPException(status_code=400, detail="No email in auth data")
    
    # Find or create user
    user = await db.users.find_one({"email": email}, {"_id": 0})
    
    if not user:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        user = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture or f"https://ui-avatars.com/api/?name={name}&background=FF0099&color=fff",
            "is_guest": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user)
        if '_id' in user:
            del user['_id']
    else:
        # Update user info if needed
        update_fields = {}
        if name and name != user.get("name"):
            update_fields["name"] = name
        if picture and picture != user.get("picture"):
            update_fields["picture"] = picture
        
        if update_fields:
            await db.users.update_one({"email": email}, {"$set": update_fields})
            user.update(update_fields)
    
    # Create session
    session_token = await create_user_session(user["user_id"])
    
    # Set httpOnly cookie with path="/", secure=True, samesite="none"
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60  # 7 days
    )
    
    return {
        "success": True,
        "user": user,
        "session_token": session_token
    }


# Include routers
app.include_router(api_router)
app.include_router(auth_router)

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
