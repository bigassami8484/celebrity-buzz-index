from fastapi import FastAPI, APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
import resend
import base64
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
from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Import from modular structure
from utils.helpers import normalize_text, decode_html_entities, sanitize_team_name
from data import (
    CELEBRITY_POOLS, HOT_CELEBS_POOL, A_LIST_INDICATORS, B_LIST_INDICATORS,
    C_LIST_INDICATORS, GUARANTEED_A_LIST, ROYAL_A_LIST_KEYWORDS, CELEBRITY_ALIASES,
    GUARANTEED_B_LIST, GUARANTEED_C_LIST, BANNED_WORDS, CONTROVERSIAL_CELEBS,
    STARTING_BUDGET, MAX_TEAM_SIZE, MAX_WEEKLY_TRANSFERS, PRICE_TIERS, TEAM_EMOJIS, TEAM_COLORS, CATEGORIES
)

async def generate_ai_celebrity_image(name: str, description: str = "") -> Optional[str]:
    """
    Generate an AI portrait for a celebrity and return base64 encoded image.
    Returns None if generation fails.
    """
    try:
        api_key = os.environ.get("EMERGENT_LLM_KEY")
        if not api_key:
            logger.warning("No EMERGENT_LLM_KEY found for AI image generation")
            return None
        
        # Create a generic professional portrait prompt
        # Avoid using celebrity names to prevent safety system issues
        desc_lower = (description or "").lower()
        
        # Determine profession/style based on description
        if "actor" in desc_lower or "actress" in desc_lower or "film" in desc_lower:
            style = "A professional Hollywood headshot portrait of an elegant person in dramatic studio lighting"
        elif "singer" in desc_lower or "musician" in desc_lower or "music" in desc_lower:
            style = "A professional portrait of a stylish music artist with creative lighting and modern aesthetic"
        elif "footballer" in desc_lower or "soccer" in desc_lower or "athlete" in desc_lower or "sports" in desc_lower:
            style = "A professional sports portrait of an athletic person with dynamic energy"
        elif "model" in desc_lower or "fashion" in desc_lower:
            style = "A high fashion editorial portrait with elegant lighting and sophisticated styling"
        elif "royal" in desc_lower or "prince" in desc_lower or "princess" in desc_lower:
            style = "A dignified formal portrait with classic elegant lighting"
        elif "reality" in desc_lower or "media" in desc_lower or "personality" in desc_lower:
            style = "A modern social media influencer style portrait with trendy aesthetic"
        elif "chef" in desc_lower or "cook" in desc_lower:
            style = "A professional portrait of a culinary expert in a kitchen setting"
        elif "comedian" in desc_lower or "comic" in desc_lower:
            style = "A warm friendly portrait with expressive lighting"
        else:
            style = "A professional celebrity headshot portrait with elegant studio lighting"
        
        prompt = f"{style}. High quality photography, clean background, portrait orientation, photorealistic, 8k resolution."
        
        image_gen = OpenAIImageGeneration(api_key=api_key)
        images = await image_gen.generate_images(
            prompt=prompt,
            model="gpt-image-1",
            number_of_images=1
        )
        
        if images and len(images) > 0:
            image_base64 = base64.b64encode(images[0]).decode('utf-8')
            return f"data:image/png;base64,{image_base64}"
        
        return None
    except Exception as e:
        logger.error(f"AI image generation failed for {name}: {e}")
        return None

async def get_or_generate_celebrity_image(name: str, description: str = "") -> str:
    """
    Get cached AI-generated image or generate a new one.
    Falls back to UI Avatars if AI generation fails.
    """
    # Check cache first
    cached = await db.ai_images.find_one({"name": name.lower()}, {"_id": 0})
    if cached and cached.get("image"):
        return cached["image"]
    
    # Generate new AI image
    ai_image = await generate_ai_celebrity_image(name, description)
    
    if ai_image:
        # Cache the generated image
        await db.ai_images.update_one(
            {"name": name.lower()},
            {"$set": {
                "name": name.lower(),
                "display_name": name,
                "image": ai_image,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )
        return ai_image
    
    # Fallback to UI Avatars
    clean_name = name.replace(" ", "+")
    return f"https://ui-avatars.com/api/?name={clean_name}&size=400&background=1a1a1a&color=FF0099&bold=true&format=png"

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

# Import auth router from modular routes
from routes import auth_router, get_current_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup Resend for magic links
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

# Frontend URL for magic links
FRONTEND_URL = os.environ.get("FRONTEND_URL", "")

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
    previous_week_price: float = 0.0  # Track last week's price for change indicator
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
    previous_week_price: float = 0.0  # Track price change from last week
    is_deceased: bool = False  # For skull icon display
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
    team_ids: List[str] = []  # Teams in this league (max 10)
    max_teams: int = 10  # Maximum 10 friends per league
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # Weekly tracking
    current_week: str = ""  # ISO week (e.g., "2026-W08")
    weekly_scores: dict = {}  # {team_id: weekly_points}
    weekly_winner_history: List[dict] = []  # [{week: str, team_id: str, team_name: str, points: float}]
    # Monthly tracking
    current_month: str = ""  # (e.g., "2026-02")
    monthly_scores: dict = {}  # {team_id: accumulated_monthly_points}
    monthly_winner_history: List[dict] = []  # [{month: str, team_id: str, team_name: str, points: float}]

class LeagueChatMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    league_id: str
    team_id: str
    team_name: str
    team_color: str = "pink"
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LeagueChatSend(BaseModel):
    team_id: str
    message: str

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
    "monthly_winner": {
        "id": "monthly_winner",
        "name": "Monthly Master",
        "icon": "🌟",
        "description": "Won a monthly league competition",
        "color": "#FF0099"
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
    },
    "league_founder": {
        "id": "league_founder",
        "name": "League Founder",
        "icon": "🎯",
        "description": "Created a league with 5+ members",
        "color": "#00F0FF"
    },
    "undefeated": {
        "id": "undefeated",
        "name": "Undefeated",
        "icon": "💪",
        "description": "Won 4 weeks in a row",
        "color": "#10B981"
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
    """Get current ISO week number as string for transfer window tracking"""
    now = datetime.now(timezone.utc)
    return f"{now.year}-W{now.isocalendar()[1]:02d}"

def get_monday_reset_week() -> str:
    """Get the current week identifier for Monday resets (points reset every Monday)"""
    now = datetime.now(timezone.utc)
    # Get the Monday of the current week
    monday = now - timedelta(days=now.weekday())
    return f"{monday.year}-W{monday.isocalendar()[1]:02d}"

def is_transfer_window_open() -> dict:
    """Check if transfer window is open (Sunday 12pm to 12am GMT - 12 hours before new week)"""
    now = datetime.now(timezone.utc)
    
    # Transfer window opens Sunday 12:00 GMT (noon) and closes Sunday 23:59 GMT (midnight)
    # This gives players 12 hours to make transfers before the new week starts Monday
    
    # Calculate when the current/next window starts
    if now.weekday() == 6:  # It's Sunday
        window_start = now.replace(hour=12, minute=0, second=0, microsecond=0)
        window_end = now.replace(hour=23, minute=59, second=59, microsecond=0)
        
        if now < window_start:
            # Before 12pm Sunday - window hasn't opened yet today
            is_open = False
        elif now <= window_end:
            # Between 12pm and midnight Sunday - window is open
            is_open = True
        else:
            # After midnight (shouldn't happen as weekday would be 0)
            is_open = False
    else:
        # Not Sunday - window is closed
        is_open = False
        window_start = None
        window_end = None
    
    # Calculate next window (next Sunday 12pm)
    if is_open:
        next_window = (now + timedelta(days=7)).replace(hour=12, minute=0, second=0, microsecond=0)
        time_remaining = window_end - now
        hours_remaining = int(time_remaining.total_seconds() // 3600)
        mins_remaining = int((time_remaining.total_seconds() % 3600) // 60)
        status_text = f"OPEN - {hours_remaining}h {mins_remaining}m left"
    else:
        # Calculate time until next Sunday 12pm
        days_until_sunday = (6 - now.weekday()) % 7
        if days_until_sunday == 0:
            # It's Sunday but window closed (before noon or after midnight edge case)
            if now.hour < 12:
                days_until_sunday = 0  # Today at noon
            else:
                days_until_sunday = 7  # Next Sunday
        next_window = (now + timedelta(days=days_until_sunday)).replace(hour=12, minute=0, second=0, microsecond=0)
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
        "window_start": window_start.isoformat() if window_start else None,
        "window_end": window_end.isoformat() if window_end else None,
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


# ==========================================
# RECOGNITION SCORE MODEL (0-100)
# ==========================================
# Weighted metrics for tier calculation:
# - Longevity (20%): Years active in industry
# - Wikipedia Languages (25%): Global recognition via language editions
# - Awards/Achievements (20%): Industry recognition
# - Commercial Impact (20%): Box office, sales, brand value
# - Wikipedia Page Views (15%): 12-month popularity

AWARD_KEYWORDS = [
    # Film Awards
    "oscar", "academy award", "golden globe", "bafta", "cannes", "venice film",
    "screen actors guild", "sag award", "critics choice",
    # Music Awards
    "grammy", "brit award", "mtv", "billboard", "american music award", "iheartradio",
    "rock and roll hall of fame", "songwriters hall of fame",
    # TV Awards
    "emmy", "primetime emmy", "daytime emmy",
    # Other Major Awards
    "tony award", "pulitzer", "nobel", "peabody", "webby",
    # Honours
    "knighthood", "knighted", "dame", "cbe", "obe", "mbe", "order of the british empire",
    "presidential medal", "legion of honour", "national medal",
    # Hall of Fame
    "hall of fame", "inducted", "lifetime achievement", "icon award",
    # Sports
    "olympic gold", "world champion", "mvp", "ballon d'or", "grand slam",
    "super bowl", "world cup winner", "all-star", "pro bowl"
]

COMMERCIAL_KEYWORDS = [
    "billion", "billionaire", "multi-million", "highest-paid", "highest paid",
    "best-selling", "best selling", "record-breaking", "record breaking",
    "#1", "number one", "chart-topping", "platinum", "diamond certified",
    "box office", "grossed", "forbes", "fortune 500", "time 100",
    "most influential", "richest", "wealthiest", "net worth",
    "founded", "founder", "ceo", "entrepreneur", "business empire",
    "brand", "franchise", "global icon", "household name"
]

async def calculate_recognition_score(name: str, bio: str, http_client: httpx.AsyncClient = None) -> dict:
    """
    Calculate Recognition Score (0-100) based on weighted metrics:
    - Longevity (20%): Years active
    - Wikipedia Languages (25%): Global recognition
    - Awards/Achievements (20%): Industry recognition  
    - Commercial Impact (20%): Sales, box office, brand value
    - Wikipedia Page Views (15%): 12-month popularity
    
    Tier Rules:
    - A = 85+ (Global household name)
    - B = 65-84 (Strong mainstream recognition)
    - C = 45-64 (Recognisable public figure)
    - D = Below 45 (Emerging / limited recognition)
    
    Safeguard Rules:
    - 15+ years active AND 10+ wiki languages → minimum C
    - 15+ years AND (commercial success OR lead TV/film role) → minimum B
    - D-tier only if <10 years active AND <10 languages AND no major commercial success
    
    Returns: {
        "recognition_score": 0-100,
        "tier": "A"/"B"/"C"/"D",
        "metrics": {longevity, languages, awards, commercial, pageviews},
        "safeguards_applied": []
    }
    """
    import re
    from datetime import datetime, timedelta
    
    bio_lower = bio.lower() if bio else ""
    safeguards_applied = []
    
    # Initialize scores (0-100 for each metric)
    longevity_score = 0
    language_score = 0
    awards_score = 0
    commercial_score = 0
    pageviews_score = 0
    
    # ===== 1. LONGEVITY SCORE (20%) =====
    years_active = 0
    
    # Look for career start patterns
    career_patterns = [
        r"career spanning (\d+)",
        r"active since (\d{4})",
        r"began .* career in (\d{4})",
        r"started .* in (\d{4})",
        r"debut in (\d{4})",
        r"debuted in (\d{4})",
        r"first .* in (\d{4})",
        r"since (\d{4})",
        r"\(born .* (\d{4})\)",
        r"born .* (\d{4})",
        r"(\d{4})[\s\-–]+present",
        r"(\d{4})–present",
        r"career began in (\d{4})",
        r"professional career in (\d{4})",
        r"acting career in (\d{4})",
        r"music career in (\d{4})",
    ]
    
    current_year = datetime.now().year
    for pattern in career_patterns:
        match = re.search(pattern, bio_lower)
        if match:
            try:
                year_or_span = int(match.group(1))
                if year_or_span > 100:  # It's a year
                    years_active = max(years_active, current_year - year_or_span)
                else:  # It's a span
                    years_active = max(years_active, year_or_span)
            except:
                pass
    
    # If no career pattern found, estimate from birth year (assume career starts at 18-22)
    if years_active == 0:
        birth_match = re.search(r"born .* (\d{4})", bio_lower)
        if birth_match:
            birth_year = int(birth_match.group(1))
            # Estimate career start (18-22 years old depending on field)
            estimated_career_start = birth_year + 20
            years_active = max(0, current_year - estimated_career_start)
    
    # Score longevity (max 100 at 40+ years)
    if years_active >= 40:
        longevity_score = 100
    elif years_active >= 30:
        longevity_score = 85
    elif years_active >= 20:
        longevity_score = 70
    elif years_active >= 15:
        longevity_score = 55
    elif years_active >= 10:
        longevity_score = 40
    elif years_active >= 5:
        longevity_score = 25
    else:
        longevity_score = 10
    
    # ===== 2. WIKIPEDIA LANGUAGES SCORE (25%) =====
    language_count = 0
    if http_client:
        try:
            wikidata_url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&sites=enwiki&titles={name.replace(' ', '_')}&props=sitelinks&format=json"
            response = await http_client.get(wikidata_url, timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                entities = data.get("entities", {})
                for entity in entities.values():
                    sitelinks = entity.get("sitelinks", {})
                    language_count = len([k for k in sitelinks.keys() if k.endswith('wiki') and not any(x in k for x in ['quote', 'source', 'books', 'news', 'versity'])])
        except Exception as e:
            logger.debug(f"Error fetching Wikidata for {name}: {e}")
    
    # Score languages (max 100 at 80+ languages)
    if language_count >= 80:
        language_score = 100
    elif language_count >= 60:
        language_score = 90
    elif language_count >= 40:
        language_score = 75
    elif language_count >= 25:
        language_score = 60
    elif language_count >= 15:
        language_score = 45
    elif language_count >= 10:
        language_score = 30
    elif language_count >= 5:
        language_score = 15
    else:
        language_score = 5
    
    # ===== 3. AWARDS/ACHIEVEMENTS SCORE (20%) =====
    awards_found = sum(1 for keyword in AWARD_KEYWORDS if keyword in bio_lower)
    
    # Score awards (max 100 at 8+ major awards/honours)
    if awards_found >= 8:
        awards_score = 100
    elif awards_found >= 6:
        awards_score = 90
    elif awards_found >= 4:
        awards_score = 75
    elif awards_found >= 3:
        awards_score = 60
    elif awards_found >= 2:
        awards_score = 45
    elif awards_found >= 1:
        awards_score = 30
    else:
        awards_score = 5
    
    # ===== 4. COMMERCIAL IMPACT SCORE (20%) =====
    commercial_found = sum(1 for keyword in COMMERCIAL_KEYWORDS if keyword in bio_lower)
    
    # Check for lead role indicators
    lead_role_indicators = [
        "starring role", "leading role", "lead role", "title role",
        "protagonist", "main character", "stars as", "starred in",
        "headlined", "fronted", "lead actor", "lead actress",
        "main cast", "series regular", "franchise lead"
    ]
    has_lead_role = any(indicator in bio_lower for indicator in lead_role_indicators)
    if has_lead_role:
        commercial_found += 2  # Boost for lead roles
    
    # Score commercial impact (max 100 at 6+ indicators)
    if commercial_found >= 6:
        commercial_score = 100
    elif commercial_found >= 4:
        commercial_score = 80
    elif commercial_found >= 3:
        commercial_score = 60
    elif commercial_found >= 2:
        commercial_score = 45
    elif commercial_found >= 1:
        commercial_score = 25
    else:
        commercial_score = 5
    
    # ===== 5. WIKIPEDIA PAGE VIEWS SCORE (15%) =====
    pageviews = 0
    if http_client:
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            pageviews_url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents/{name.replace(' ', '_')}/monthly/{start_date.strftime('%Y%m')}01/{end_date.strftime('%Y%m')}01"
            response = await http_client.get(pageviews_url, timeout=5.0, headers={"User-Agent": "CelebrityBuzzIndex/1.0"})
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                pageviews = sum(item.get("views", 0) for item in items)
        except Exception as e:
            logger.debug(f"Error fetching pageviews for {name}: {e}")
    
    # Score pageviews (max 100 at 10M+ annual views)
    if pageviews >= 10000000:
        pageviews_score = 100
    elif pageviews >= 5000000:
        pageviews_score = 90
    elif pageviews >= 2000000:
        pageviews_score = 75
    elif pageviews >= 1000000:
        pageviews_score = 60
    elif pageviews >= 500000:
        pageviews_score = 45
    elif pageviews >= 200000:
        pageviews_score = 30
    elif pageviews >= 100000:
        pageviews_score = 20
    else:
        pageviews_score = 10
    
    # ===== CALCULATE WEIGHTED TOTAL =====
    recognition_score = (
        (longevity_score * 0.20) +
        (language_score * 0.25) +
        (awards_score * 0.20) +
        (commercial_score * 0.20) +
        (pageviews_score * 0.15)
    )
    recognition_score = round(recognition_score)
    
    # ===== DETERMINE BASE TIER =====
    if recognition_score >= 85:
        tier = "A"
    elif recognition_score >= 65:
        tier = "B"
    elif recognition_score >= 45:
        tier = "C"
    else:
        tier = "D"
    
    # ===== APPLY SAFEGUARD RULES =====
    has_commercial_success = commercial_found >= 2
    
    # Safeguard 1: 15+ years active AND 10+ wiki languages → minimum C
    if years_active >= 15 and language_count >= 10 and tier == "D":
        tier = "C"
        safeguards_applied.append("Upgraded to C: 15+ years active with 10+ wiki languages")
    
    # Safeguard 2: 15+ years AND (commercial success OR lead TV/film role) → minimum B
    if years_active >= 15 and (has_commercial_success or has_lead_role):
        if tier in ["C", "D"]:
            tier = "B"
            safeguards_applied.append("Upgraded to B: 15+ years with commercial success or lead role")
    
    # Safeguard 3: D-tier only if <10 years active AND <10 languages AND no major commercial success
    if tier == "D":
        if years_active >= 10 or language_count >= 10 or has_commercial_success:
            tier = "C"
            safeguards_applied.append("Upgraded to C: Does not meet D-tier criteria (needs <10 years, <10 langs, no commercial success)")
    
    return {
        "recognition_score": recognition_score,
        "tier": tier,
        "metrics": {
            "longevity": {"score": longevity_score, "years_active": years_active, "weight": "20%"},
            "languages": {"score": language_score, "count": language_count, "weight": "25%"},
            "awards": {"score": awards_score, "found": awards_found, "weight": "20%"},
            "commercial": {"score": commercial_score, "found": commercial_found, "has_lead_role": has_lead_role, "weight": "20%"},
            "pageviews": {"score": pageviews_score, "annual": pageviews, "weight": "15%"}
        },
        "safeguards_applied": safeguards_applied
    }

def calculate_recognition_score_from_metrics(metrics: dict) -> dict:
    """Calculate recognition score from pre-computed metrics (for DB-stored data) with safeguards"""
    longevity_score = metrics.get("longevity", {}).get("score", 10)
    language_score = metrics.get("languages", {}).get("score", 10)
    awards_score = metrics.get("awards", {}).get("score", 10)
    commercial_score = metrics.get("commercial", {}).get("score", 10)
    pageviews_score = metrics.get("pageviews", {}).get("score", 10)
    
    # Get raw values for safeguard checks
    years_active = metrics.get("longevity", {}).get("years_active", 0)
    language_count = metrics.get("languages", {}).get("count", 0)
    commercial_found = metrics.get("commercial", {}).get("found", 0)
    has_lead_role = metrics.get("commercial", {}).get("has_lead_role", False)
    
    recognition_score = round(
        (longevity_score * 0.20) +
        (language_score * 0.25) +
        (awards_score * 0.20) +
        (commercial_score * 0.20) +
        (pageviews_score * 0.15)
    )
    
    # Base tier
    if recognition_score >= 85:
        tier = "A"
    elif recognition_score >= 65:
        tier = "B"
    elif recognition_score >= 45:
        tier = "C"
    else:
        tier = "D"
    
    # Apply safeguards
    safeguards_applied = []
    has_commercial_success = commercial_found >= 2
    
    # Safeguard 1: 15+ years active AND 10+ wiki languages → minimum C
    if years_active >= 15 and language_count >= 10 and tier == "D":
        tier = "C"
        safeguards_applied.append("Upgraded to C: 15+ years with 10+ languages")
    
    # Safeguard 2: 15+ years AND (commercial success OR lead role) → minimum B
    if years_active >= 15 and (has_commercial_success or has_lead_role):
        if tier in ["C", "D"]:
            tier = "B"
            safeguards_applied.append("Upgraded to B: 15+ years with commercial success")
    
    # Safeguard 3: D-tier only if meets all criteria
    if tier == "D":
        if years_active >= 10 or language_count >= 10 or has_commercial_success:
            tier = "C"
            safeguards_applied.append("Upgraded to C: Does not meet D-tier criteria")
    
    return {
        "recognition_score": recognition_score, 
        "tier": tier,
        "safeguards_applied": safeguards_applied
    }


async def get_brown_bread_premium(celeb: dict, base_price: float) -> float:
    """
    Check if celebrity qualifies for Brown Bread premium pricing.
    Top 3 oldest living celebrities (80+) get premium prices:
    - #1 oldest: £15M
    - #2 oldest: £13M
    - #3 oldest: £11M
    """
    age = celeb.get("age", 0)
    is_deceased = celeb.get("is_deceased", False)
    
    # Only living celebrities aged 80+ qualify
    if is_deceased or age < 80:
        return base_price
    
    # Get top 3 oldest living celebrities from DB
    top_elderly = await db.celebrities.find(
        {"is_deceased": False, "age": {"$gte": 80}},
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
    Returns the premium price if they're in top 3 oldest (80+), otherwise 0.
    """
    name_lower = name.lower().strip()
    
    # Get top 3 oldest living celebrities from DB
    top_elderly = await db.celebrities.find(
        {"is_deceased": False, "age": {"$gte": 80}},
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
    {"id": "tv_personalities", "name": "TV Personalities", "icon": "video"},
    {"id": "musicians", "name": "Musicians", "icon": "music"},
    {"id": "athletes", "name": "Athletes", "icon": "trophy"},
    {"id": "royals", "name": "Royals", "icon": "crown"},
    {"id": "reality_tv", "name": "Reality TV", "icon": "star"},
    {"id": "public_figure", "name": "Public Figure", "icon": "megaphone"},
    {"id": "other", "name": "Other", "icon": "users"},
]

# Pre-defined trending celebrities per category (UK & International mix)
TRENDING_CELEBRITIES = {
    "movie_stars": ["Tom Holland", "Florence Pugh", "Idris Elba", "Emily Blunt", "Dev Patel"],
    "tv_actors": ["Jenna Coleman", "Jodie Comer", "Richard Madden", "Ncuti Gatwa", "Olivia Colman"],
    "tv_personalities": ["Graham Norton", "Holly Willoughby", "Ant McPartlin", "Dec Donnelly", "Phillip Schofield"],
    "musicians": ["Dua Lipa", "Ed Sheeran", "Adele", "Harry Styles", "Stormzy"],
    "athletes": ["Harry Kane", "Marcus Rashford", "Emma Raducanu", "Lewis Hamilton", "Raheem Sterling"],
    "royals": ["Prince William", "Kate Middleton", "Prince Harry", "Meghan Markle", "Prince Andrew"],
    "reality_tv": ["Katie Price", "Gemma Collins", "Pete Wicks", "Joey Essex", "Sam Faiers"],
    "public_figure": ["Elon Musk", "Donald Trump", "Boris Johnson", "Greta Thunberg", "Alexandria Ocasio-Cortez", "Joe Rogan", "Andrew Tate", "Jordan Peterson", "Nigel Farage", "Rishi Sunak"],
    "other": ["Gordon Ramsay", "Bear Grylls", "Jeremy Clarkson", "Jamie Oliver", "Nigella Lawson"],
}

# LARGE CELEBRITY POOLS - 50+ celebrities per category to pull from
CELEBRITY_POOLS = {
    "movie_stars": [
        # Current A-listers
        "Tom Holland", "Florence Pugh", "Idris Elba", "Emily Blunt", "Dev Patel",
        "Leonardo DiCaprio", "Brad Pitt", "Angelina Jolie", "Tom Cruise", "Jennifer Lawrence",
        "Margot Robbie", "Ryan Gosling", "Emma Stone", "Chris Hemsworth", "Scarlett Johansson",
        "Robert Downey Jr", "Chris Evans", "Zendaya", "Timothee Chalamet", "Sydney Sweeney",
        "Ana de Armas", "Austin Butler", "Jacob Elordi", "Glen Powell", "Jenna Ortega",
        "Anya Taylor-Joy", "Paul Mescal", "Barry Keoghan", "Daisy Edgar-Jones", "Josh O'Connor",
        "Cillian Murphy", "Dakota Johnson", "Pedro Pascal", "Oscar Isaac", "Florence Pugh",
        "Jason Momoa", "Gal Gadot", "Henry Cavill", "Dwayne Johnson", "Vin Diesel",
        "Keanu Reeves", "Sandra Bullock", "Julia Roberts", "George Clooney", "Matt Damon",
        "Ben Affleck", "Jennifer Garner", "Reese Witherspoon", "Nicole Kidman", "Cate Blanchett",
        "Meryl Streep", "Viola Davis", "Denzel Washington", "Samuel L Jackson", "Morgan Freeman",
        "Al Pacino", "Robert De Niro", "Michael Caine", "Anthony Hopkins", "Ian McKellen",
        "Patrick Stewart", "Judi Dench", "Helen Mirren", "Emma Thompson", "Kate Winslet",
        "Rachel McAdams", "Anne Hathaway", "Natalie Portman", "Keira Knightley", "Saoirse Ronan",
        # More stars
        "Chris Pratt", "Ryan Reynolds", "Hugh Jackman", "Mark Wahlberg", "Will Smith",
        "Johnny Depp", "Tom Hanks", "Harrison Ford", "Michael B Jordan", "John Boyega",
        "Lupita Nyongo", "Awkwafina", "Simu Liu", "Gemma Chan", "Michelle Yeoh",
        "Jamie Lee Curtis", "Brendan Fraser", "Ke Huy Quan", "Jessica Chastain", "Julianne Moore",
        "Amy Adams", "Emily Ratajkowski", "Hailee Steinfeld", "Elle Fanning", "Dakota Fanning"
    ],
    "tv_actors": [
        # British TV
        "Jenna Coleman", "Jodie Comer", "Richard Madden", "Ncuti Gatwa", "Olivia Colman",
        "David Tennant", "Matt Smith", "Peter Capaldi", "Jodie Whittaker", "Karen Gillan",
        "Suranne Jones", "Martin Compston", "Vicky McClure", "Adrian Dunbar", "Keeley Hawes",
        "Ruth Wilson", "Dominic West", "Gillian Anderson", "Jamie Dornan", "Cush Jumbo",
        "David Oyelowo", "Thandiwe Newton", "Michaela Coel", "Phoebe Waller-Bridge", "Andrew Scott",
        "Fleabag", "Rosamund Pike", "Maxine Peake", "Sheridan Smith", "Sarah Lancashire",
        "Stephen Graham", "Sean Bean", "Jason Statham", "Gemma Arterton", "Naomie Harris",
        "Michelle Keegan",  # Coronation Street, Our Girl, Brassic
        # US TV
        "Kit Harington", "Emilia Clarke", "Sophie Turner", "Maisie Williams", "Nikolaj Coster-Waldau",
        "Bryan Cranston", "Aaron Paul", "Elisabeth Moss", "Steve Carell", "Jenna Fischer",
        "Rainn Wilson", "John Krasinski", "Sarah Snook", "Jeremy Strong", "Brian Cox",
        "Matthew Macfadyen", "Kieran Culkin", "Jason Sudeikis", "Hannah Waddingham", "Brett Goldstein",
        "Zooey Deschanel", "Kaley Cuoco", "Jim Parsons", "Johnny Galecki", "Kunal Nayyar",
        "Jennifer Aniston", "Courteney Cox", "Lisa Kudrow", "Matt LeBlanc", "David Schwimmer",
        "Sofia Vergara", "Julie Bowen", "Ty Burrell", "Jesse Tyler Ferguson", "Eric Stonestreet",
        "Zach Braff", "Donald Faison", "Neil Patrick Harris", "Jason Segel", "Alyson Hannigan"
    ],
    "musicians": [
        # Current pop stars
        "Dua Lipa", "Ed Sheeran", "Adele", "Harry Styles", "Stormzy",
        "Taylor Swift", "Beyonce", "Rihanna", "Lady Gaga", "Ariana Grande",
        "Billie Eilish", "Olivia Rodrigo", "Doja Cat", "SZA", "Lizzo",
        "Post Malone", "Bad Bunny", "Drake", "Kendrick Lamar", "Travis Scott",
        "The Weeknd", "Bruno Mars", "Justin Bieber", "Shawn Mendes", "Charlie Puth",
        "Sam Smith", "Lewis Capaldi", "Tom Grennan", "George Ezra", "Rag'n'Bone Man",
        # UK legends
        "Elton John", "Paul McCartney", "Mick Jagger", "Rod Stewart", "Ozzy Osbourne",
        "Noel Gallagher", "Liam Gallagher", "Robbie Williams", "Gary Barlow", "Olly Murs",
        "Rita Ora", "Jessie J", "Anne-Marie", "Ellie Goulding", "Dua Lipa",
        "Florence Welch", "Leona Lewis", "Cheryl Cole", "Nicole Scherzinger", "Mel B",
        # US & International
        "Cardi B", "Megan Thee Stallion", "Nicki Minaj", "Ice Spice", "Latto",
        "Miley Cyrus", "Selena Gomez", "Demi Lovato", "Katy Perry", "Pink",
        "Justin Timberlake", "Usher", "Chris Brown", "Jason Derulo", "Ne-Yo",
        "Kanye West", "Jay-Z", "Eminem", "50 Cent", "Snoop Dogg",
        "Liza Minnelli", "Cher", "Madonna", "Britney Spears", "Christina Aguilera",
        "Shakira", "Jennifer Lopez", "Mariah Carey", "Celine Dion", "Whitney Houston"
    ],
    "athletes": [
        # Football
        "Harry Kane", "Marcus Rashford", "Raheem Sterling", "Jude Bellingham", "Phil Foden",
        "Bukayo Saka", "Jack Grealish", "Mason Mount", "Declan Rice", "Trent Alexander-Arnold",
        "Mo Salah", "Virgil van Dijk", "Erling Haaland", "Kevin De Bruyne", "Bruno Fernandes",
        "Cristiano Ronaldo", "Lionel Messi", "Neymar", "Kylian Mbappe", "Robert Lewandowski",
        "David Beckham", "Wayne Rooney", "Steven Gerrard", "Frank Lampard", "John Terry",
        "Gary Lineker", "Alan Shearer", "Michael Owen", "Rio Ferdinand", "Paul Scholes",
        # Tennis
        "Andy Murray", "Roger Federer", "Rafael Nadal", "Novak Djokovic", "Emma Raducanu",
        "Serena Williams", "Venus Williams", "Naomi Osaka", "Coco Gauff", "Maria Sharapova",
        # Other sports
        "Lewis Hamilton", "Max Verstappen", "Lando Norris", "George Russell", "Daniel Ricciardo",
        "Usain Bolt", "Mo Farah", "Jessica Ennis-Hill", "Dina Asher-Smith", "Katarina Johnson-Thompson",
        "Anthony Joshua", "Tyson Fury", "Conor McGregor", "Floyd Mayweather", "Mike Tyson",
        "LeBron James", "Steph Curry", "Kevin Durant", "Michael Jordan", "Kobe Bryant",
        "Tom Brady", "Patrick Mahomes", "Simone Biles", "Michael Phelps", "Adam Peaty"
    ],
    "royals": [
        # British Royal Family
        "King Charles III", "Queen Camilla", "Prince William", "Catherine Princess of Wales",
        "Prince Harry", "Meghan Markle", "Prince George", "Princess Charlotte", "Prince Louis",
        "Princess Anne", "Prince Andrew", "Prince Edward", "Sophie Duchess of Edinburgh",
        "Princess Beatrice", "Princess Eugenie", "Zara Tindall", "Peter Phillips",
        "Lady Louise Windsor", "James Viscount Severn", "Sarah Ferguson",
        "Archie Mountbatten-Windsor", "Lilibet Mountbatten-Windsor",
        "Mike Tindall", "Edoardo Mapelli Mozzi", "Jack Brooksbank",
        # Historical
        "Queen Elizabeth II", "Princess Diana", "Prince Philip",
        # European Royals
        "King Felipe VI of Spain", "Queen Letizia of Spain",
        "King Willem-Alexander of Netherlands", "Queen Maxima of Netherlands",
        "Crown Princess Victoria of Sweden", "Prince Daniel of Sweden",
        "Crown Princess Mary of Denmark", "King Frederik X of Denmark",
        "Prince Albert of Monaco", "Princess Charlene of Monaco",
        "King Carl XVI Gustaf of Sweden", "Queen Silvia of Sweden"
    ],
    "reality_tv": [
        # TOWIE & UK Reality
        "Katie Price", "Gemma Collins", "Pete Wicks", "Joey Essex", "Sam Faiers",
        "Mark Wright", "Amy Childs", "Lauren Goodger", "Billie Faiers",
        "Vicky Pattison", "Charlotte Crosby", "Holly Hagan", "Chloe Ferry", "Marnie Simpson",
        # Made in Chelsea
        "Georgia Toffolo", "Jamie Laing", "Spencer Matthews", "Binky Felstead",
        "Ollie Locke", "Sam Thompson", "Zara McDermott", "Lucy Watson", "Proudlock",
        # Love Island UK
        "Molly-Mae Hague", "Tommy Fury", "Maura Higgins", "Amber Gill", "Dani Dyer",
        "Jack Fincham", "Ekin-Su Culculoglu", "Davide Sanclimenti", "Olivia Attwood",
        "Amber Davies", "Kem Cetinay", "Cara De La Hoyde", "Nathan Massey", "Olivia Buckland",
        # Kardashians & US Reality
        "Kim Kardashian", "Khloe Kardashian", "Kourtney Kardashian", "Kylie Jenner", "Kendall Jenner",
        "Kris Jenner", "Scott Disick", "Travis Barker", "Paris Hilton", "Nicole Richie",
        "Lauren Conrad", "Kristin Cavallari", "Spencer Pratt", "Heidi Montag", "Brody Jenner",
        "Lisa Vanderpump", "Kyle Richards", "Teresa Giudice", "NeNe Leakes", "Bethenny Frankel"
    ],
    "public_figure": [
        # Tech billionaires
        "Elon Musk", "Mark Zuckerberg", "Jeff Bezos", "Bill Gates", "Tim Cook",
        "Sundar Pichai", "Satya Nadella", "Jack Dorsey", "Reed Hastings", "Jensen Huang",
        # US Politicians
        "Donald Trump", "Joe Biden", "Barack Obama", "Michelle Obama", "Hillary Clinton",
        "Nancy Pelosi", "Alexandria Ocasio-Cortez", "Bernie Sanders", "Kamala Harris", "Mike Pence",
        # UK Politicians
        "Boris Johnson", "Rishi Sunak", "Keir Starmer", "Nigel Farage", "Liz Truss",
        "Theresa May", "David Cameron", "Tony Blair", "Jeremy Corbyn", "Sadiq Khan",
        # World Leaders
        "Vladimir Putin", "Volodymyr Zelenskyy", "Emmanuel Macron", "Angela Merkel", "Justin Trudeau",
        "Xi Jinping", "Narendra Modi", "Jair Bolsonaro", "Benjamin Netanyahu", "Kim Jong-un",
        # Activists & Influencers
        "Greta Thunberg", "Malala Yousafzai", "Andrew Tate", "Jordan Peterson", "Joe Rogan",
        "Ben Shapiro", "Tucker Carlson", "Piers Morgan", "Megyn Kelly", "Rachel Maddow",
        # Business & Other
        "Richard Branson", "Alan Sugar", "Warren Buffett", "Oprah Winfrey", "Martha Stewart",
        "Pope Francis", "Dalai Lama", "Neil deGrasse Tyson", "Bill Nye", "Dr Phil"
    ],
    "tv_personalities": [
        # UK TV Presenters
        "Graham Norton", "Jonathan Ross", "Alan Carr", "James Corden", "Piers Morgan",
        "Holly Willoughby", "Phillip Schofield", "Ant McPartlin", "Dec Donnelly", "Dermot O'Leary",
        "Claudia Winkleman", "Tess Daly", "Rylan Clark", "Alison Hammond", "Rochelle Humes",
        "Vernon Kay", "Lorraine Kelly", "Susanna Reid", "Kate Garraway", "Ben Shephard",
        "Davina McCall", "Emma Willis", "Paddy McGuinness", "Keith Lemon", "Fearne Cotton",
        "Christine Lampard", "Ruth Langsford", "Eamonn Holmes", "Nadia Sawalha", "Coleen Nolan",
        # Entertainment Show Hosts
        "Simon Cowell", "Amanda Holden", "David Walliams", "Alesha Dixon", "Bruno Tonioli",
        "Craig Revel Horwood", "Shirley Ballas", "Motsi Mabuse", "Anton Du Beke", "Oti Mabuse",
        # Sports Presenters
        "Gary Lineker", "Ian Wright", "Alan Shearer", "Gabby Logan", "Clare Balding",
        "Alex Scott", "Micah Richards", "Rio Ferdinand", "Jamie Carragher", "Gary Neville",
        # Science/Documentary Presenters
        "David Attenborough", "Brian Cox", "Stephen Fry", "Michael Palin",
        # US TV Personalities
        "Oprah Winfrey", "Ellen DeGeneres", "Jimmy Fallon", "Jimmy Kimmel", "Stephen Colbert",
        "Trevor Noah", "James Corden", "Ryan Seacrest", "Carson Daly", "Kelly Clarkson"
    ],
    "other": [
        # Chefs
        "Gordon Ramsay", "Jamie Oliver", "Nigella Lawson", "Mary Berry", "Paul Hollywood",
        "Prue Leith", "Ainsley Harriott", "Gino D'Acampo", "James Martin", "Nadiya Hussain",
        # Comedians
        "Peter Kay", "Michael McIntyre", "Ricky Gervais", "Jimmy Carr", "Russell Howard",
        "Jack Whitehall", "Rob Beckett", "Romesh Ranganathan", "Kevin Hart", "Chris Rock",
        "Dave Chappelle", "Joe Rogan", "Russell Brand", "Eddie Izzard", "Sarah Millican",
        # Adventurers/Explorers
        "Bear Grylls", "Jeremy Clarkson", "Richard Hammond", "James May", "Ranulph Fiennes",
        # Beckham Family
        "David Beckham", "Victoria Beckham", "Brooklyn Beckham", "Romeo Beckham", "Cruz Beckham",
        # Models & Influencers  
        "Naomi Campbell", "Kate Moss", "Cara Delevingne", "Rosie Huntington-Whiteley", "Daisy Lowe",
        "Zoe Sugg", "Tanya Burr", "Mrs Hinch", "Stacey Solomon", "Joe Wicks",
        # Writers/Authors
        "J.K. Rowling", "Stephen King", "George R.R. Martin", "Neil Gaiman", "Dan Brown",
        # Business/Entrepreneurs (non-political)
        "Richard Branson", "Alan Sugar", "Deborah Meaden", "Peter Jones", "Theo Paphitis",
        # Other
        "Chris Hughes"
    ]
}

# HOT CELEBS POOL - Large pool to randomly select from on each refresh
HOT_CELEBS_POOL = [
    # Royals
    {"name": "Andrew Mountbatten-Windsor", "reason": "Royal scandal & legal battles", "tier": "A", "category": "royals"},
    {"name": "Meghan Markle", "reason": "Netflix & Royal drama", "tier": "A", "category": "royals"},
    {"name": "Prince Harry", "reason": "Spare memoir revelations", "tier": "A", "category": "royals"},
    {"name": "Kate Middleton", "reason": "Royal duties & fashion", "tier": "A", "category": "royals"},
    {"name": "King Charles III", "reason": "Royal family head", "tier": "A", "category": "royals"},
    # Musicians
    {"name": "Kanye West", "reason": "Controversy & headlines", "tier": "A", "category": "musicians"},
    {"name": "Taylor Swift", "reason": "Eras Tour & awards", "tier": "A", "category": "musicians"},
    {"name": "Beyoncé", "reason": "Renaissance & Grammys", "tier": "A", "category": "musicians"},
    {"name": "Drake (musician)", "reason": "Music & feuds", "tier": "A", "category": "musicians"},
    {"name": "Rihanna", "reason": "Fenty & fashion empire", "tier": "A", "category": "musicians"},
    {"name": "Ed Sheeran", "reason": "Tours & legal battles", "tier": "A", "category": "musicians"},
    {"name": "Adele", "reason": "Vegas residency", "tier": "A", "category": "musicians"},
    {"name": "Bad Bunny", "reason": "Latin music & film debut", "tier": "B", "category": "musicians"},
    {"name": "Britney Spears", "reason": "Memoir & documentaries", "tier": "B", "category": "musicians"},
    {"name": "Debbie Harry", "reason": "Blondie legend", "tier": "B", "category": "musicians"},
    # Tech/Business
    {"name": "Elon Musk", "reason": "Tech & politics headlines", "tier": "A", "category": "public_figure"},
    {"name": "Mark Zuckerberg", "reason": "Meta & AI news", "tier": "A", "category": "public_figure"},
    {"name": "Jeff Bezos", "reason": "Space & business", "tier": "A", "category": "public_figure"},
    # Politicians
    {"name": "Donald Trump", "reason": "Political & legal news", "tier": "A", "category": "public_figure"},
    {"name": "Joe Biden", "reason": "Political headlines", "tier": "A", "category": "public_figure"},
    # Reality TV/UK
    {"name": "Katie Price", "reason": "Tabloid regular", "tier": "C", "category": "reality_tv"},
    {"name": "Holly Willoughby", "reason": "TV presenter", "tier": "C", "category": "tv_personalities"},
    {"name": "Phillip Schofield", "reason": "TV scandal", "tier": "C", "category": "tv_personalities"},
    {"name": "Gemma Collins", "reason": "Reality star", "tier": "C", "category": "reality_tv"},
    {"name": "Simone Biles", "reason": "Olympic GOAT", "tier": "A", "category": "athletes"},
    # Actors
    {"name": "Tom Cruise", "reason": "Mission Impossible & stunts", "tier": "A", "category": "movie_stars"},
    {"name": "Leonardo DiCaprio", "reason": "Film & dating life", "tier": "A", "category": "movie_stars"},
    {"name": "Jennifer Lawrence", "reason": "Film & fashion", "tier": "A", "category": "movie_stars"},
    {"name": "Brad Pitt", "reason": "Films & personal life", "tier": "A", "category": "movie_stars"},
    {"name": "Angelina Jolie", "reason": "Humanitarian & acting", "tier": "A", "category": "movie_stars"},
    {"name": "Adam Sandler", "reason": "Netflix & comedy empire", "tier": "A", "category": "movie_stars"},
    {"name": "Michael B. Jordan", "reason": "Creed & directing debut", "tier": "A", "category": "movie_stars"},
    {"name": "Shia LaBeouf", "reason": "Film & controversy", "tier": "B", "category": "movie_stars"},
    {"name": "Margot Robbie", "reason": "Barbie & film roles", "tier": "A", "category": "movie_stars"},
    {"name": "Andrew Garfield", "reason": "Spider-Man & Oscar buzz", "tier": "A", "category": "movie_stars"},
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
A_LIST_INDICATORS = [
    # Major Awards
    "oscar", "academy award", "grammy", "emmy", "golden globe", "bafta", "tony award",
    "pulitzer", "nobel", "knighthood", "dame", "order of the british empire",
    # Hall of Fame
    "hall of fame", "rock and roll hall", "hollywood walk of fame", "inducted",
    # Career Longevity & Success
    "billion", "legendary", "iconic", "superstar", "megastar", "one of the most",
    "best-selling", "highest-paid", "most famous", "world record", "all-time",
    "pioneer", "trailblazer", "revolutionized", "transformed",
    # Global Brand/Franchise
    "founded", "entrepreneur", "business empire", "brand", "franchise",
    "forbes", "time 100", "most influential", "global icon",
    # Sports Excellence  
    "world cup winner", "olympic gold", "world champion", "grand slam",
    "mvp", "all-star", "pro bowl", "ballon d'or"
]
B_LIST_INDICATORS = ["award-winning", "acclaimed", "successful", "popular", "well-known", 
                      "million", "chart-topping", "hit", "starring", "lead role",
                      "critically acclaimed", "box office", "platinum", "gold record"]
C_LIST_INDICATORS = ["known for", "appeared in", "featured", "contestant", "participant"]

# Mega-stars who should ALWAYS be A-list regardless of bio analysis
GUARANTEED_A_LIST = [
    # Global Music Superstars (20+ years, major awards, Hall of Fame)
    "taylor swift", "beyoncé", "beyonce", "rihanna", "drake", "kanye west", "adele",
    "ed sheeran", "ariana grande", "justin bieber", "lady gaga", "bruno mars",
    "britney spears", "madonna", "michael jackson", "jennifer lopez", "shakira",
    "eminem", "jay-z", "jay z", "snoop dogg", "50 cent", "nicki minaj", "cardi b",
    "selena gomez", "miley cyrus", "katy perry", "demi lovato", "the weeknd",
    "harry styles", "zayn malik", "niall horan", "liam payne", "louis tomlinson",
    "victoria beckham", "cheryl", "robbie williams", "elton john", "paul mccartney",
    "mick jagger", "keith richards", "sting", "bono", "phil collins", "rod stewart",
    "stevie wonder", "whitney houston", "mariah carey", "celine dion", "barbra streisand",
    "cher", "tina turner", "janet jackson", "diana ross", "dolly parton",
    "bruce springsteen", "billy joel", "eric clapton", "bob dylan", "prince",
    "david bowie", "freddie mercury", "ozzy osbourne", "slash", "axl rose",
    # Global Movie Stars (franchise leads, major awards)
    "leonardo dicaprio", "tom cruise", "brad pitt", "angelina jolie", "tom hanks",
    "julia roberts", "denzel washington", "will smith", "johnny depp", "robert downey jr",
    "dwayne johnson", "the rock", "scarlett johansson", "jennifer lawrence", "margot robbie",
    "meryl streep", "nicole kidman", "cate blanchett", "natalie portman", "emma watson",
    "george clooney", "matt damon", "ben affleck", "keanu reeves", "morgan freeman",
    "samuel l. jackson", "samuel l jackson", "al pacino", "robert de niro", "jack nicholson",
    "clint eastwood", "harrison ford", "sylvester stallone", "arnold schwarzenegger",
    "sean connery", "anthony hopkins", "michael caine", "ian mckellen", "patrick stewart",
    "judi dench", "helen mirren", "emma thompson", "kate winslet", "sandra bullock",
    "reese witherspoon", "charlize theron", "halle berry", "viola davis", "lupita nyong'o",
    # Global TV Stars (iconic shows, Emmy winners)
    "jennifer aniston", "courteney cox", "lisa kudrow", "matthew perry", "david schwimmer",
    "matt leblanc", "jerry seinfeld", "sarah jessica parker", "kim cattrall",
    "bryan cranston", "aaron paul", "peter dinklage", "emilia clarke", "kit harington",
    # Global Athletes (20+ years, Hall of Fame, Olympic gold)
    "cristiano ronaldo", "lionel messi", "lebron james", "serena williams", "roger federer", 
    "michael jordan", "david beckham", "tom brady", "tiger woods", "usain bolt", 
    "muhammad ali", "mike tyson", "simone biles", "venus williams", "novak djokovic", 
    "wayne rooney", "diego maradona", "pele", "pelé", "zinedine zidane", "kobe bryant", "shaquille o'neal",
    "michael phelps", "rafael nadal", "lewis hamilton", "floyd mayweather", "floyd mayweather jr",
    "manny pacquiao", "conor mcgregor", "neymar", "kylian mbappe", "erling haaland",
    # Global Business Leaders (founded global brands)
    "oprah winfrey", "elon musk", "jeff bezos", "bill gates", "mark zuckerberg",
    "warren buffett", "richard branson", "steve jobs", "martha stewart", "kylie jenner",
    "rihanna", "jessica alba", "gwyneth paltrow",
    # Media Icons & Cultural Figures
    "kim kardashian", "khloe kardashian", "kourtney kardashian", "kris jenner", "kendall jenner",
    "paris hilton", "ellen degeneres", "james corden", "jimmy fallon", "jimmy kimmel",
    "conan o'brien", "david letterman", "jay leno", "anderson cooper", "ryan seacrest",
    "simon cowell", "gordon ramsay", "guy fieri", "anthony bourdain",
    # Political & Public Figures
    "barack obama", "michelle obama", "donald trump", "joe biden", "hillary clinton",
    "bill clinton", "george w. bush", "george h. w. bush", "angela merkel",
    "nelson mandela", "dalai lama", "pope francis", "malala yousafzai", "greta thunberg",
    # British Royal Family (globally famous)
    "prince william", "william, prince of wales", "william prince of wales",
    "prince harry", "harry, duke of sussex", "harry duke of sussex", "prince harry, duke of sussex",
    "kate middleton", "catherine, princess of wales", "catherine princess of wales",
    "queen elizabeth", "elizabeth ii", "queen elizabeth ii",
    "king charles", "charles iii", "king charles iii",
    "meghan markle", "meghan, duchess of sussex", "meghan duchess of sussex",
    "princess diana", "diana, princess of wales", "diana princess of wales",
    "camilla", "queen camilla", "camilla, queen consort",
    "princess anne", "anne, princess royal",
    "prince george", "prince george of wales",
    "princess charlotte", "princess charlotte of wales",
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
    "camilla": "Queen Camilla",
    "queen camilla": "Queen Camilla",
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
    # Brian Cox disambiguation
    "brian cox": "Brian Cox (physicist)",
    "brian cox physicist": "Brian Cox (physicist)",
    "brian cox scientist": "Brian Cox (physicist)",
    "professor brian cox": "Brian Cox (physicist)",
    "brian cox actor": "Brian Cox (actor)",
    # Reality TV Personalities
    "sam thompson": "Sam Thompson (TV personality)",
    "spencer matthews": "Spencer Matthews",
    # Musicians with disambiguation
    "drake": "Drake (musician)",
    "usher": "Usher (musician)",
    "chris brown": "Chris Brown",
    # Sports presenters
    "alex scott": "Alex Scott (footballer, born 1984)",
    "george russell": "George Russell (racing driver)",
    # Royals with disambiguation
    "prince edward": "Prince Edward, Duke of Edinburgh",
    "prince frederick": "Frederik X",
    "prince frederik of denmark": "Frederik X",
    "sophie duchess of edinburgh": "Sophie, Duchess of Edinburgh",
    "sophie wessex": "Sophie, Duchess of Edinburgh",
    "james viscount severn": "James, Earl of Wessex",
    "king willem-alexander": "Willem-Alexander of the Netherlands",
    "king willem-alexander of netherlands": "Willem-Alexander of the Netherlands",
    "queen maxima": "Queen Máxima of the Netherlands",
    "queen maxima of netherlands": "Queen Máxima of the Netherlands",
    # Royal Children - Prince William's kids
    "prince george": "Prince George of Wales",
    "george cambridge": "Prince George of Wales",
    "george of wales": "Prince George of Wales",
    "princess charlotte": "Princess Charlotte of Wales",
    "charlotte cambridge": "Princess Charlotte of Wales",
    "charlotte of wales": "Princess Charlotte of Wales",
    "prince louis": "Prince Louis of Wales",
    "louis cambridge": "Princess Louis of Wales",
    "louis of wales": "Prince Louis of Wales",
    # Royal Children - Prince Harry's kids
    "prince archie": "Prince Archie of Sussex",
    "archie mountbatten-windsor": "Prince Archie of Sussex",
    "archie of sussex": "Prince Archie of Sussex",
    "archie harrison": "Prince Archie of Sussex",
    "princess lilibet": "Princess Lilibet of Sussex",
    "lilibet mountbatten-windsor": "Princess Lilibet of Sussex", 
    "lilibet of sussex": "Princess Lilibet of Sussex",
    "lilibet diana": "Princess Lilibet of Sussex",
    # Actors with disambiguation
    "christopher evans": "Chris Evans",
    "chris evans actor": "Chris Evans",
    "chris evans captain america": "Chris Evans",
    # Cheryl (singer) - various name aliases
    "cheryl cole": "Cheryl (singer)",
    "cheryl singer": "Cheryl (singer)",
    "cheryl tweedy": "Cheryl (singer)",
    "cheryl fernandez-versini": "Cheryl (singer)",
    "cheryl ann tweedy": "Cheryl (singer)",
    # Willie Colon - footballer not trombonist
    "willie colon": "Willie Colon (American football)",
    "willie colón": "Willie Colon (American football)",
    # Mark Wright - reality TV star
    "mark wright": "Mark Wright (television personality)",
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
                
                # If no image from Wikipedia, try Wikidata P18
                if not image:
                    try:
                        wikidata_url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&sites=enwiki&titles={actual_title.replace(' ', '_')}&props=claims&format=json"
                        wd_response = await client.get(wikidata_url, timeout=3.0, headers=headers)
                        if wd_response.status_code == 200:
                            wd_data = wd_response.json()
                            for entity in wd_data.get("entities", {}).values():
                                claims = entity.get("claims", {})
                                if "P18" in claims:
                                    img_file = claims["P18"][0]["mainsnak"]["datavalue"]["value"]
                                    img_file_encoded = img_file.replace(" ", "_")
                                    image = f"https://commons.wikimedia.org/wiki/Special:FilePath/{img_file_encoded}?width=150"
                                    break
                    except:
                        pass
                
                # Skip duplicates
                base_name = actual_title.split("(")[0].strip().lower()
                if base_name in seen_names:
                    continue
                seen_names.add(base_name)
                
                # FIRST: Check if this celeb is in the Hot Celebs cache - use that price
                hot_celebs_cache = await db.news_cache.find_one(
                    {"type": "hot_celebs_from_news_v4"},
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
                    # Check if celebrity exists in DB - use their stored price
                    existing = await db.celebrities.find_one(
                        {"name": {"$regex": f"^{actual_title}$", "$options": "i"}},
                        {"_id": 0, "tier": 1, "price": 1}
                    )
                    
                    if existing and existing.get("price"):
                        tier = existing.get("tier", "D")
                        price = existing.get("price")  # Use stored DB price for consistency
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
                    "tier": tier,
                    "estimated_tier": tier,
                    "price": price,
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
    """Estimate celebrity tier from Wikipedia description using indicator scoring"""
    # NOTE: This is a quick estimation. Full Recognition Score calculation 
    # should be used for database storage via calculate_recognition_score()
    
    desc_lower = description.lower()
    
    # Score based on indicators
    a_score = sum(1 for ind in A_LIST_INDICATORS if ind in desc_lower)
    b_score = sum(1 for ind in B_LIST_INDICATORS if ind in desc_lower)
    c_score = sum(1 for ind in C_LIST_INDICATORS if ind in desc_lower)
    
    # Check for A-list indicators
    if a_score >= 2:
        return "A"
    
    # Check for B-list indicators  
    if a_score >= 1 or b_score >= 2:
        return "B"
    
    # Check for C-list indicators
    if b_score >= 1 or c_score >= 1:
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

def get_base_price_for_tier(tier: str, name: str = "") -> float:
    """Get BASE price range for celebrity tier (in millions) with variation"""
    import random
    import hashlib
    
    # Price ranges for each tier
    price_ranges = {
        "A": (9.0, 12.0),   # £9m-£12m
        "B": (5.0, 8.0),    # £5m-£8m
        "C": (2.0, 4.0),    # £2m-£4m
        "D": (0.5, 1.5)     # £0.5m-£1.5m
    }
    
    min_price, max_price = price_ranges.get(tier, (0.5, 1.5))
    
    # Use name hash for consistent but varied pricing (same celeb = same price)
    if name:
        # Create a deterministic "random" factor based on the name
        name_hash = int(hashlib.md5(name.lower().encode()).hexdigest()[:8], 16)
        variation = (name_hash % 100) / 100.0  # 0.0 to 0.99
    else:
        variation = random.random()
    
    # Calculate price within range
    price_range = max_price - min_price
    price = min_price + (price_range * variation)
    
    return round(price, 1)

def get_dynamic_price(tier: str, buzz_score: float, name: str = "") -> float:
    """Calculate dynamic price based on tier and buzz score
    
    Pricing Tiers (STRICT - MAX £12M for any celeb):
    - A-List: £9m-£12m (high scoring but expensive)
    - B-List: £5m-£8m (balanced steady picks)  
    - C-List: £2m-£4m (risk/reward)
    - D-List: £0.5m-£1.5m (cheap wildcards)
    
    Buzz Score Impact:
    - buzz_score 0-25: Price at lower end of tier range
    - buzz_score 25-50: Price at mid-low range
    - buzz_score 50-75: Price at mid-high range
    - buzz_score 75-100+: Price at higher end of tier range
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
    # Buzz score typically ranges from 0 (minimum) to 100+ (very high)
    # Map this to a 0-1 scale for price adjustment within the tier
    # Using a more aggressive curve to make buzz score more impactful
    if buzz_score <= 0:
        buzz_factor = 0.0
    elif buzz_score >= 100:
        buzz_factor = 1.0
    else:
        # Smooth curve that makes mid-range buzz scores have significant impact
        buzz_factor = min(1.0, buzz_score / 100.0)
    
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


async def calculate_tier_from_wikipedia_data(name: str, http_client: httpx.AsyncClient) -> dict:
    """
    Calculate celebrity tier using Recognition Score model (0-100).
    
    Weighted metrics:
    - Longevity (20%): Years active in industry
    - Wikipedia Languages (25%): Global recognition via language editions
    - Awards/Achievements (20%): Industry recognition
    - Commercial Impact (20%): Box office, sales, brand value
    - Wikipedia Page Views (15%): 12-month popularity
    
    Tier thresholds:
    - 85+ = A-List
    - 65-84 = B-List  
    - 45-64 = C-List
    - Below 45 = D-List
    """
    try:
        # Fetch Wikipedia bio
        headers = {"User-Agent": "CelebrityBuzzIndex/1.0"}
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{name.replace(' ', '_')}"
        response = await http_client.get(url, timeout=10.0, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            bio = data.get("extract", "")
            
            # Calculate Recognition Score
            score_result = await calculate_recognition_score(name, bio, http_client)
            
            tier = score_result["tier"]
            recognition_score = score_result["recognition_score"]
            metrics = score_result["metrics"]
            
            # Calculate price based on tier
            base_price = get_base_price_for_tier(tier, name)
            
            return {
                "tier": tier,
                "price": base_price,
                "recognition_score": recognition_score,
                "tier_metrics": metrics,
                "bio": bio,
                "image": data.get("thumbnail", {}).get("source", ""),
                "wiki_url": data.get("content_urls", {}).get("desktop", {}).get("page", "")
            }
        else:
            # Default to D-list if Wikipedia lookup fails
            return {
                "tier": "D",
                "price": get_base_price_for_tier("D", name),
                "recognition_score": 20,
                "tier_metrics": {}
            }
    except Exception as e:
        logger.error(f"Error calculating tier for {name}: {e}")
        return {
            "tier": "D", 
            "price": get_base_price_for_tier("D", name),
            "recognition_score": 20,
            "tier_metrics": {}
        }

# Legacy function for backwards compatibility - now uses Recognition Score
def determine_tier_from_bio_legacy(bio: str, name: str = "") -> str:
    """Legacy wrapper - just calls the new Recognition Score-based tier calculation"""
    return determine_tier_from_bio(bio, name)


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
                
                # Get image - PREFER Wikidata P18 (more reliable, avoids rate limits)
                # Also check P570 (date of death) to detect deceased status
                wiki_image = ""
                is_deceased_from_wikidata = False
                
                # First, try Wikidata P18 - most reliable image source
                try:
                    wikidata_url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&sites=enwiki&titles={name.replace(' ', '_')}&props=claims&format=json"
                    logger.info(f"Fetching Wikidata image for {name}: {wikidata_url}")
                    wd_response = await client.get(wikidata_url, timeout=5.0, headers=headers)
                    if wd_response.status_code == 200:
                        wd_data = wd_response.json()
                        entities = wd_data.get("entities", {})
                        for entity in entities.values():
                            claims = entity.get("claims", {})
                            if "P18" in claims:  # P18 is the image property
                                img_file = claims["P18"][0]["mainsnak"]["datavalue"]["value"]
                                # URL encode the filename properly for Commons
                                from urllib.parse import quote
                                img_file_encoded = quote(img_file.replace(" ", "_"), safe='')
                                wiki_image = f"https://commons.wikimedia.org/wiki/Special:FilePath/{img_file_encoded}?width=400"
                                logger.info(f"Got Wikidata image for {name}: {wiki_image}")
                            # Check for death date (P570)
                            if "P570" in claims:
                                is_deceased_from_wikidata = True
                    else:
                        logger.warning(f"Wikidata returned status {wd_response.status_code} for {name}")
                except Exception as e:
                    logger.warning(f"Wikidata fetch failed for {name}: {e}")
                
                # Fallback to Wikipedia thumbnail if Wikidata didn't have an image
                if not wiki_image:
                    wiki_image = data.get("thumbnail", {}).get("source", "")
                
                # If still no image, try pageimages API as backup
                if not wiki_image:
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
                    "birth_year": birth_year,
                    "is_deceased": is_deceased_from_wikidata
                }
            else:
                logger.error(f"Wikipedia returned status {response.status_code}: {response.text[:200]}")
    except Exception as e:
        logger.error(f"Wikipedia fetch error for {name}: {type(e).__name__}: {e}")
    return {"name": name, "bio": "Celebrity profile", "image": "", "wiki_url": "", "birth_year": 0, "is_deceased": False}

def detect_category_from_bio(bio: str, name: str) -> str:
    """Detect celebrity category from bio text"""
    bio_lower = bio.lower()
    name_lower = name.lower()
    
    # GUARANTEED CATEGORY OVERRIDES - takes highest priority
    # These are celebrities whose primary occupation is well-known
    GUARANTEED_CATEGORIES = {
        # TV Presenters/Hosts
        "tv_personalities": [
            "graham norton", "james corden", "jonathan ross", "alan carr", "piers morgan",
            "david letterman", "jimmy fallon", "jimmy kimmel", "ellen degeneres", "oprah winfrey",
            "conan o'brien", "stephen colbert", "trevor noah", "holly willoughby", "phillip schofield",
            "ant mcpartlin", "declan donnelly", "lorraine kelly", "rylan clark", "claudia winkleman",
            "dermot o'leary", "amanda holden", "simon cowell", "david attenborough", "gordon ramsay",
            "jamie oliver", "nigella lawson", "mary berry", "paul hollywood", "prue leith",
            "ainsley harriott", "delia smith", "heston blumenthal", "marco pierre white",
            "guy fieri", "bobby flay", "rachael ray", "ina garten", "ryan seacrest",
            "seth meyers", "john oliver", "wendy williams", "steve harvey", "nick cannon",
            "howie mandel", "louis walsh", "sharon osbourne", "nicole scherzinger",
            "alesha dixon", "david walliams", "bruno tonioli", "tess daly", "zoe ball",
            "vernon kay", "matt baker", "alex jones", "naga munchetty", "charlie stayt",
            "susanna reid", "ben shephard", "kate garraway", "richard madeley", "judy finnigan",
            "christine lampard", "emma willis", "regis philbin", "keke palmer", "fearne cotton",
            "scott mills", "craig ferguson", "drew barrymore", "sherri shepherd", "mario lopez",
            "kelly ripa", "mayim bialik", "lawrence o'donnell",
            # Additional TV personalities (broadcasters known primarily for TV work)
            "jeremy clarkson", "richard hammond", "james may", "alan titchmarsh", "sue perkins",
            "alexander armstrong", "sophie raworth", "andrew marr", "chris cuomo", "eamonn holmes",
            "gary lineker", "matt lucas", "david mitchell", "lee mack", "mel giedroyc",
        ],
        
        # Reality TV Stars
        "reality_tv": [
            "katie price", "kerry katona", "gemma collins", "peter andre", "joey essex",
            "kim kardashian", "kylie jenner", "kendall jenner", "khloé kardashian",
            "kourtney kardashian", "kris jenner", "paris hilton", "nicole richie",
            "caitlyn jenner", "jojo siwa", "stacey solomon", "joe swash",
            "charlotte crosby", "vicky pattison", "tommy fury", "molly-mae hague",
            "ekin-su cülcüloğlu", "davide sanclimenti", "dani dyer", "olivia attwood",
            "amber gill", "millie court", "tasha ghouri", "nicole snooki polizzi",
            "bethenny frankel", "lisa vanderpump", "kyle richards", "teresa giudice",
            "chloe ferry", "scotty t", "marnie simpson", "jamie laing", "sam thompson",
            "zara mcdermott", "georgia toffolo", "spencer matthews", "lucy watson",
        ],
        
        # Athletes
        "athletes": [
            "david beckham", "cristiano ronaldo", "lionel messi", "lebron james",
            "michael jordan", "serena williams", "venus williams", "roger federer",
            "rafael nadal", "novak djokovic", "tiger woods", "usain bolt",
            "simone biles", "michael phelps", "tom brady", "patrick mahomes",
            "lewis hamilton", "max verstappen", "conor mcgregor", "floyd mayweather",
            "wayne rooney", "harry kane", "marcus rashford", "bukayo saka",
            "neymar", "kylian mbappé", "erling haaland", "kevin de bruyne",
            "mo salah", "jack grealish", "gareth bale", "emma raducanu",
            "anthony joshua", "tyson fury", "ronda rousey", "amanda nunes",
            "travis kelce", "jonathan owens", "tyreek hill",
        ],
        
        # Musicians (primary occupation is music, even if they've acted)
        "musicians": [
            "taylor swift", "beyoncé", "beyonce", "rihanna", "drake", "ed sheeran",
            "lady gaga", "bruno mars", "justin bieber", "ariana grande",
            "kanye west", "jay-z", "eminem", "madonna", "cher",
            "elton john", "paul mccartney", "mick jagger", "bono", "sting",
            "celine dion", "mariah carey", "janet jackson", "diana ross",
            "harry styles", "billie eilish", "dua lipa", "the weeknd",
            "post malone", "bad bunny", "doja cat", "lizzo", "cardi b",
            "nicki minaj", "katy perry", "miley cyrus", "selena gomez",
            "demi lovato", "shawn mendes", "camila cabello", "halsey",
            "adele", "sam smith", "lewis capaldi", "robbie williams",
            "gary barlow", "olly murs", "craig david", "stormzy",
            "victoria beckham", "mel b", "mel c", "geri halliwell",
            "dolly parton", "barbra streisand", "tina turner", "aretha franklin",
            "stevie wonder", "bob dylan", "bruce springsteen", "eric clapton",
            "phil collins", "rod stewart", "billy joel", "debbie harry",
            "50 cent", "snoop dogg", "dr. dre", "ice cube",
            "britney spears", "christina aguilera", "whitney houston",
            "michael jackson", "prince", "david bowie", "freddie mercury",
        ],
        
        # Royals
        "royals": [
            "king charles iii", "king charles", "queen elizabeth", "prince william",
            "kate middleton", "catherine", "princess of wales", "prince harry",
            "meghan markle", "duchess of sussex", "princess diana", "camilla",
            "prince andrew", "andrew mountbatten-windsor", "princess beatrice",
            "princess eugenie", "prince edward", "princess anne", "zara tindall",
        ],
        
        # Public Figures (politicians, business, activists)
        "public_figure": [
            "elon musk", "jeff bezos", "bill gates", "mark zuckerberg", "warren buffett",
            "donald trump", "joe biden", "barack obama", "michelle obama",
            "boris johnson", "rishi sunak", "keir starmer", "nigel farage",
            "hillary clinton", "nancy pelosi", "alexandria ocasio-cortez",
            "vladimir putin", "volodymyr zelenskyy", "pope francis", "dalai lama",
            "greta thunberg", "malala yousafzai", "joe rogan", "andrew tate",
            "jordan peterson", "charlie kirk", "ben shapiro", "tucker carlson",
            "rachel maddow", "anderson cooper", "don lemon", "sean hannity",
        ],
    }
    
    # Check guaranteed categories first
    for category, names in GUARANTEED_CATEGORIES.items():
        if name_lower in names:
            return category
    
    # SPECIFIC CELEBRITY CATEGORY OVERRIDES - secondary priority
    category_overrides = {
        # Musicians - people known primarily for singing
        "peter andre": "musicians",
        "kerry katona": "musicians",
        "jessica simpson": "musicians",
        
        # Other - notorious/infamous figures
        "ghislaine maxwell": "other",
        "harvey weinstein": "other",
        "jeffrey epstein": "other",
        "elizabeth holmes": "other",
        
        # Movie Stars - actors who may have "musician" keywords in bio due to film soundtracks
        "timothée chalamet": "movie_stars",
        "shia labeouf": "movie_stars",
        "richard madden": "movie_stars",
        
        # TV Actors - primarily known for TV roles
        "jenna coleman": "tv_actors",
        "jodie comer": "tv_actors",
        "ncuti gatwa": "tv_actors",
        "olivia colman": "tv_actors",
        "jessica alba": "tv_actors",
        "tyreek hill": "athletes",
        "simone biles": "athletes",
        "lebron james": "athletes",
    }
    
    for override_name, override_category in category_overrides.items():
        if override_name in name_lower:
            logger.info(f"Category detection: {name} matched override '{override_name}' - returning {override_category}")
            return override_category
    
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
    
    # =================================================================
    # CHECK FIRST OCCUPATION - Find which occupation appears FIRST
    # Wikipedia bios typically list primary occupation first
    # e.g., "is a British actor and musician" -> actor is first
    # =================================================================
    bio_start = bio_lower[:150]  # First sentence usually has primary occupation
    
    # Define occupation keywords and their categories
    occupation_map = {
        # Category: (keywords, priority - lower = check first)
        "influencers": (["youtuber", "youtube personality", "tiktok", "tiktoker", 
                        "internet personality", "social media personality", "influencer",
                        "vlogger", "streamer", "content creator"], 1),
        "athletes": (["footballer", "athlete", "football player", "basketball player",
                     "soccer player", "tennis player", "racing driver", "cricketer",
                     "rugby player", "boxer", "golfer", "swimmer", "olympic"], 2),
        "musicians": (["singer", "songwriter", "musician", "rapper", "vocalist",
                      "recording artist", "pop star", "rock star"], 3),
        # Note: "broadcaster" removed - handled separately below (TV broadcasters vs other)
        "tv_personalities": (["television presenter", "tv presenter", "television broadcaster",
                             "television host", "talk show host"], 4),
        "tv_actors": (["television actor", "tv actor"], 5),
        "movie_stars": (["actor", "actress", "film actor", "film actress"], 6),
    }
    
    # Special handling for "broadcaster" - only TV broadcasters go to tv_personalities
    # Radio broadcasters and generic broadcasters go to "other"
    if "broadcaster" in bio_start:
        # Check if it's specifically a TV broadcaster
        if any(tv_word in bio_start for tv_word in ["television", "tv "]):
            return "tv_personalities"
        # Radio presenter goes to other
        if "radio" in bio_start:
            return "other"
        # Generic broadcaster without TV context goes to other
        return "other"
    
    # Find which occupation appears FIRST in the bio
    first_occupation = None
    first_position = 999
    
    for category, (keywords, priority) in occupation_map.items():
        for kw in keywords:
            pos = bio_start.find(kw)
            if pos != -1 and pos < first_position:
                first_position = pos
                first_occupation = category
    
    # If we found a clear first occupation, use it
    if first_occupation and first_position < 100:
        return first_occupation
    
    # YouTubers/Influencers - fallback check
    if any(x in bio_start for x in ["youtuber", "youtube personality", "youtube star",
                                     "tiktok", "tiktoker", "internet personality",
                                     "social media personality", "influencer",
                                     "vlogger", "streamer", "twitch", "content creator"]):
        return "influencers"
    
    # Reality TV keywords (check before actors)
    if any(x in bio_lower for x in ["reality television", "reality tv", "reality show", "glamour model", 
                                      "media personality", "television personality", "socialite",
                                      "keeping up with", "big brother", "love island", "towie",
                                      "i'm a celebrity", "strictly come dancing contestant"]):
        return "reality_tv"
    
    # Royals - must specifically be about royal family, NOT just people with royal honors like "Sir"
    if any(x in bio_lower for x in ["member of the british royal family", "member of the royal family",
                                     "heir to the throne", "house of windsor", "buckingham palace", 
                                     "line of succession", "son of king", "daughter of queen",
                                     "grandson of queen", "granddaughter of queen"]):
        return "royals"
    
    # Athletes - full bio check
    if any(x in bio_lower for x in ["premier league", "f1", "formula one", "striker", "goalkeeper", 
                                     "midfielder", "defender", "bundesliga", "la liga", "serie a",
                                     "england national team", "world cup", "grand prix"]):
        return "athletes"
    
    # Musicians - full bio check
    if any(x in bio_lower for x in ["album", "grammy", "brit award", "concert tour", "music artist",
                                     "hip hop artist", "r&b", "mezzo-soprano", "soprano", "tenor"]):
        return "musicians"
    
    # Public Figures - politicians, business magnates, activists
    if any(x in bio_start for x in ["politician", "president", "prime minister", "senator", 
                                     "businessman", "businesswoman", "entrepreneur", "activist"]):
        return "public_figure"
    
    if any(x in bio_lower for x in ["congressman", "member of parliament", "political commentator",
                                     "business magnate", "billionaire", "ceo", "chief executive"]):
        return "public_figure"
    
    # TV Presenters - full bio check
    if any(x in bio_lower for x in ["chat show", "game show host", "news anchor", "news presenter"]):
        return "tv_personalities"
    
    # =================================================================
    # SMART FILM VS TV DETECTION
    # Count mentions of film/movie keywords vs TV keywords
    # If more TV mentions → tv_actors, if more film mentions → movie_stars
    # =================================================================
    
    # Keywords that indicate FILM work
    film_keywords = [
        "film", "films", "movie", "movies", "cinema", "box office", "blockbuster",
        "oscar", "academy award", "screen actors guild", "hollywood",
        "feature film", "motion picture", "theatrical release"
    ]
    
    # Keywords that indicate TV work  
    tv_keywords = [
        "television series", "tv series", "television show", "tv show",
        "sitcom", "soap opera", "miniseries", "tv movie", "television movie",
        "primetime emmy", "emmy award", "bafta tv", "golden globe for television",
        "streaming series", "netflix series", "hbo series", "bbc series", "amc series",
        "comedy series", "drama series", "television drama", "tv drama"
    ]
    
    # ICONIC TV SHOWS - if someone is known for these, they're primarily a TV actor
    # These shows defined their careers, so we give extra weight
    iconic_tv_shows = [
        "stranger things", "breaking bad", "game of thrones", "the crown", "downton abbey",
        "peaky blinders", "the office", "friends", "fleabag", "killing eve", "succession",
        "the sopranos", "the wire", "mad men", "lost", "grey's anatomy", "how i met your mother",
        "the big bang theory", "modern family", "schitt's creek", "ted lasso", "the mandalorian",
        "bridgerton", "squid game", "wednesday", "the witcher", "house of the dragon"
    ]
    
    # Count occurrences
    film_score = sum(bio_lower.count(kw) for kw in film_keywords)
    tv_score = sum(bio_lower.count(kw) for kw in tv_keywords)
    
    # Add bonus for iconic TV shows (2 points each - they define careers)
    for show in iconic_tv_shows:
        if show in bio_lower:
            tv_score += 2
    
    # If they're an actor/actress and we have clear TV vs film signals
    is_actor = any(x in bio_lower for x in ["actor", "actress"])
    
    if is_actor:
        if tv_score > film_score:
            return "tv_actors"
        elif film_score > tv_score:
            return "movie_stars"
        # If tied or no clear signal, check for specific indicators
        elif tv_score > 0:
            return "tv_actors"
        elif film_score > 0:
            return "movie_stars"
    
    # Fallback: TV actors check (legacy)
    if any(x in bio_lower for x in ["television series", "tv series", "sitcom", "soap opera"]):
        return "tv_actors"
    
    # Movie stars - full bio check
    if any(x in bio_lower for x in ["actor", "actress", "film", "movie", "cinema", "hollywood", 
                                     "oscar", "academy award", "golden globe",
                                     "box office", "marvel", "superhero", "spider-man"]):
        return "movie_stars"
    
    # Other (businesspeople, chefs, etc.)
    if any(x in bio_lower for x in ["chef", "presenter", "host", "businessman", "entrepreneur",
                                     "author", "journalist", "comedian"]):
        return "other"
    
    return "other"  # Default to other


def determine_tier_from_bio(bio: str, name: str = "") -> str:
    """
    Synchronous helper to determine celebrity tier using Recognition Score model.
    Uses bio-based metrics when async Wikipedia calls aren't available.
    
    Recognition Score thresholds:
    - 85+ = A-List
    - 65-84 = B-List
    - 45-64 = C-List
    - Below 45 = D-List
    """
    import re
    from datetime import datetime
    
    name_lower = name.lower() if name else ""
    bio_lower = bio.lower() if bio else ""
    
    # ===== Calculate Recognition Score components =====
    
    # 1. LONGEVITY (20%) - Extract years active from bio
    longevity_score = 10
    years_active = 0
    current_year = datetime.now().year
    
    career_patterns = [
        r"career spanning (\d+)",
        r"active since (\d{4})",
        r"began .* career in (\d{4})",
        r"started .* in (\d{4})",
        r"debut in (\d{4})",
        r"first .* in (\d{4})",
        r"since (\d{4})",
        r"\(born .* (\d{4})\)",
        r"(\d{4})[\s\-–]+present",
        r"(\d{4})–present"
    ]
    
    for pattern in career_patterns:
        match = re.search(pattern, bio_lower)
        if match:
            try:
                year_or_span = int(match.group(1))
                if year_or_span > 100:
                    years_active = max(years_active, current_year - year_or_span)
                else:
                    years_active = max(years_active, year_or_span)
            except:
                pass
    
    if years_active >= 40:
        longevity_score = 100
    elif years_active >= 30:
        longevity_score = 85
    elif years_active >= 20:
        longevity_score = 70
    elif years_active >= 15:
        longevity_score = 55
    elif years_active >= 10:
        longevity_score = 40
    elif years_active >= 5:
        longevity_score = 25
    
    # 2. AWARDS (20%) - Count award keywords
    awards_found = sum(1 for keyword in AWARD_KEYWORDS if keyword in bio_lower)
    
    if awards_found >= 8:
        awards_score = 100
    elif awards_found >= 6:
        awards_score = 90
    elif awards_found >= 4:
        awards_score = 75
    elif awards_found >= 3:
        awards_score = 60
    elif awards_found >= 2:
        awards_score = 45
    elif awards_found >= 1:
        awards_score = 30
    else:
        awards_score = 5
    
    # 3. COMMERCIAL (20%) - Count commercial impact keywords
    commercial_found = sum(1 for keyword in COMMERCIAL_KEYWORDS if keyword in bio_lower)
    
    if commercial_found >= 6:
        commercial_score = 100
    elif commercial_found >= 4:
        commercial_score = 80
    elif commercial_found >= 3:
        commercial_score = 60
    elif commercial_found >= 2:
        commercial_score = 45
    elif commercial_found >= 1:
        commercial_score = 25
    else:
        commercial_score = 5
    
    # 4. LANGUAGE ESTIMATE (25%) - Use bio length as proxy for global notability
    bio_length = len(bio) if bio else 0
    if bio_length >= 3000:
        language_score = 80  # Long detailed bio = likely many languages
    elif bio_length >= 2000:
        language_score = 65
    elif bio_length >= 1000:
        language_score = 50
    elif bio_length >= 500:
        language_score = 35
    else:
        language_score = 15
    
    # 5. PAGEVIEWS ESTIMATE (15%) - Use award/commercial indicators as proxy
    pageviews_score = max(30, min(awards_score, commercial_score))
    
    # ===== Calculate weighted total =====
    recognition_score = round(
        (longevity_score * 0.20) +
        (language_score * 0.25) +
        (awards_score * 0.20) +
        (commercial_score * 0.20) +
        (pageviews_score * 0.15)
    )
    
    # ===== Determine tier from score =====
    if recognition_score >= 85:
        return "A"
    elif recognition_score >= 65:
        return "B"
    elif recognition_score >= 45:
        return "C"
    else:
        return "D"


def get_category_from_bio(bio: str, name: str) -> str:
    """Synchronous wrapper for detect_category_from_bio"""
    return detect_category_from_bio(bio, name)


async def fetch_real_celebrity_news(name: str, max_articles: int = 10) -> List[dict]:
    """
    Fetch REAL news about a specific celebrity from RSS feeds.
    Searches ALL major entertainment news sources for mentions of the celebrity.
    Returns list of real news articles from the last 7 DAYS (weekly points system).
    """
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    # COMPREHENSIVE RSS feeds - ALL major UK & US entertainment sources
    rss_sources = [
        # UK TABLOIDS & SHOWBIZ
        ("https://www.dailymail.co.uk/tvshowbiz/index.rss", "Daily Mail UK"),
        ("https://www.dailymail.co.uk/usshowbiz/index.rss", "Daily Mail US"),
        ("https://www.thesun.co.uk/tvandshowbiz/feed/", "The Sun"),
        ("https://www.mirror.co.uk/3am/rss.xml", "Daily Mirror"),
        ("https://metro.co.uk/entertainment/feed/", "Metro"),
        ("https://www.express.co.uk/celebrity-news/feed", "Express"),
        ("https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml", "BBC News"),
        ("https://www.theguardian.com/lifeandstyle/celebrities/rss", "The Guardian"),
        ("https://www.independent.co.uk/topic/celebrities/rss", "The Independent"),
        ("https://www.ok.co.uk/celebrity-news/feed", "OK! Magazine"),
        ("https://www.hellomagazine.com/celebrities/rss/", "Hello!"),
        ("https://news.sky.com/feeds/rss/entertainment.xml", "Sky News"),
        
        # US ENTERTAINMENT & GOSSIP
        ("https://www.tmz.com/rss.xml", "TMZ"),
        ("https://people.com/feed/", "People"),
        ("https://www.usmagazine.com/feed/", "Us Weekly"),
        ("https://pagesix.com/feed/", "Page Six"),
        ("https://www.eonline.com/syndication/feeds/rssfeeds/topstories.xml", "E! News"),
        ("https://www.etonline.com/news/rss", "Entertainment Tonight"),
        ("https://www.justjared.com/feed/", "Just Jared"),
        ("https://www.buzzfeed.com/celebrity.xml", "BuzzFeed"),
        ("https://www.huffpost.com/section/entertainment/feed", "HuffPost"),
        ("https://news.yahoo.com/rss/entertainment", "Yahoo News"),
        ("https://www.nationalenquirer.com/feed/", "National Enquirer"),
        
        # HOLLYWOOD TRADE
        ("https://variety.com/feed/", "Variety"),
        ("https://www.hollywoodreporter.com/feed/", "Hollywood Reporter"),
        ("https://deadline.com/feed/", "Deadline"),
        ("https://www.vanityfair.com/rss/news", "Vanity Fair"),
        
        # MUSIC
        ("https://www.billboard.com/feed/", "Billboard"),
        ("https://www.rollingstone.com/feed/", "Rolling Stone"),
        ("https://www.nme.com/feed", "NME"),
        ("https://pitchfork.com/feed/feed-news/rss", "Pitchfork"),
        
        # GENERAL NEWS - ENTERTAINMENT SECTIONS
        ("https://rss.cnn.com/rss/cnn_showbiz.rss", "CNN"),
        ("https://feeds.foxnews.com/foxnews/entertainment", "Fox News"),
        ("https://www.cbsnews.com/latest/rss/entertainment", "CBS News"),
        ("https://abcnews.go.com/abcnews/entertainmentheadlines", "ABC News"),
        ("https://www.reuters.com/news/archive/entertainmentNews?view=feed&type=rss", "Reuters"),
        ("https://www.bloomberg.com/feeds/sitemap_news.xml", "Bloomberg"),
        
        # SPORTS (for athlete celebrities)
        ("https://news.sky.com/feeds/rss/sports.xml", "Sky Sports"),
        ("https://www.bbc.co.uk/sport/rss.xml", "BBC Sport"),
        ("https://www.espn.com/espn/rss/news", "ESPN"),
        ("https://www.goal.com/en/feeds/news", "Goal"),
    ]
    
    # Name variations to search for - IMPROVED MATCHING
    name_lower = name.lower().strip()
    name_parts = name_lower.split()
    
    # Build comprehensive search terms
    first_name = name_parts[0] if name_parts else ""
    last_name = name_parts[-1] if len(name_parts) > 1 else ""
    
    # Celebrity-specific aliases (news often uses nicknames)
    celebrity_news_aliases = {
        # US Celebrities
        "kanye west": ["kanye", "ye", "yeezy"],
        "dwayne johnson": ["the rock", "dwayne johnson", "rock"],
        "sean combs": ["diddy", "p diddy", "puff daddy", "sean combs"],
        "taylor swift": ["taylor swift", "swift", "t-swift"],
        "beyoncé": ["beyonce", "beyoncé", "queen bey"],
        "beyonce": ["beyonce", "beyoncé", "queen bey"],
        "jennifer lopez": ["j.lo", "jlo", "jennifer lopez", "j lo"],
        "kim kardashian": ["kim k", "kardashian", "kim kardashian"],
        # UK Celebrities
        "cheryl cole": ["cheryl", "cheryl cole", "cheryl tweedy"],
        "cheryl (singer)": ["cheryl", "cheryl cole", "cheryl tweedy"],
        "gemma collins": ["the gc", "gemma collins", "gemma"],
        "stacey solomon": ["stacey solomon", "stacey", "solomon"],
        "joe swash": ["joe swash", "swash"],
        "peter andre": ["peter andre", "andre"],
        "kerry katona": ["kerry katona", "katona"],
        # Footballers
        "cristiano ronaldo": ["ronaldo", "cr7", "cristiano"],
        "lionel messi": ["messi", "lionel"],
        "marcus rashford": ["rashford", "marcus rashford"],
        "david beckham": ["beckham", "beckhams", "david beckham"],
        # Musicians
        "drake": ["drake", "drizzy", "champagne papi"],
        "adele": ["adele"],
        "ed sheeran": ["ed sheeran", "sheeran"],
        "rihanna": ["rihanna", "riri", "fenty"],
        # Royals (to avoid false positives with common first names)
        "prince andrew, duke of york": ["prince andrew", "duke of york", "andrew york"],
        "andrew mountbatten-windsor": ["prince andrew", "duke of york"],
        # Reality TV - avoid "Princess Andre" matching wrong person
        "peter andre": ["peter andre"],  # Require full name only
    }
    
    # Start with full name as primary
    search_terms = [name_lower]
    
    # Add celebrity-specific aliases
    if name_lower in celebrity_news_aliases:
        search_terms.extend(celebrity_news_aliases[name_lower])
    
    # For multi-word names, add last name (most news uses last names)
    # E.g., "the Beckhams", "Swift's new album", "Kardashian drama"
    if len(name_parts) > 1:
        search_terms.append(last_name)
        
        # Also add first name for context matching
        if len(first_name) > 3:  # Skip short names like "Kim" alone
            search_terms.append(first_name)
    
    # Handle hyphenated and multi-part last names
    if len(name_parts) == 3:
        search_terms.append(f"{name_parts[1]} {name_parts[2]}")
    if len(name_parts) >= 4:
        search_terms.append(" ".join(name_parts[1:]))
    
    # Remove duplicates while preserving order
    search_terms = list(dict.fromkeys(search_terms))
    
    # Cutoff date - 7 DAYS ago (weekly points system)
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
    
    real_news = []
    seen_titles = set()  # Avoid duplicates
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Fetch all RSS feeds concurrently for speed
            async def fetch_rss(url, source):
                try:
                    response = await client.get(url, timeout=8.0, headers=headers, follow_redirects=True)
                    if response.status_code == 200:
                        return (source, response.text)
                except Exception as e:
                    logger.debug(f"RSS fetch failed for {source}: {e}")
                return None
            
            # Run all fetches in parallel
            tasks = [fetch_rss(url, source) for url, source in rss_sources]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if not result or isinstance(result, Exception):
                    continue
                source_name, content = result
                items = content.split("<item>")[1:50]  # Get up to 50 items per source for better coverage
                
                for item in items:
                    try:
                        # Extract title
                        title_start = item.find("<title>") + 7
                        title_end = item.find("</title>")
                        if title_start < 7 or title_end < 0:
                            continue
                        title = item[title_start:title_end].replace("<![CDATA[", "").replace("]]>", "").strip()
                        title = decode_html_entities(title)
                        title_lower = title.lower()
                        
                        # For name matching, we ONLY check the TITLE to avoid false positives
                        # from articles that merely mention a celebrity in passing in the description
                        search_text = title_lower
                        
                        # Check if celebrity is mentioned - STRICT FULL NAME MATCHING ONLY
                        celeb_mentioned = False
                        
                        import re
                        
                        # Common first/last names that cause false positives
                        common_names = {
                            'michael', 'jordan', 'james', 'john', 'david', 'peter', 'andrew',
                            'paul', 'mark', 'steve', 'chris', 'daniel', 'robert', 'william',
                            'george', 'thomas', 'charles', 'richard', 'jason', 'brian', 'kevin',
                            'jennifer', 'jessica', 'sarah', 'emily', 'emma', 'anna', 'kate',
                            'mary', 'elizabeth', 'victoria', 'charlotte', 'sophie', 'amy'
                        }
                        
                        # Method 1: EXACT full name match with word boundaries (REQUIRED for all)
                        # This is the primary and most reliable method
                        full_name_pattern = rf'\b{re.escape(name_lower)}\b'
                        if re.search(full_name_pattern, search_text):
                            celeb_mentioned = True
                        
                        # Method 2: Check celebrity-specific aliases (only if defined)
                        if not celeb_mentioned and name_lower in celebrity_news_aliases:
                            for alias in celebrity_news_aliases[name_lower]:
                                alias_pattern = rf'\b{re.escape(alias)}\b'
                                if re.search(alias_pattern, search_text):
                                    celeb_mentioned = True
                                    break
                        
                        # Method 3: For multi-word names with COMMON names, require EXACT full name
                        # No fuzzy matching for names like "Michael Jordan" - too many false positives
                        # This prevents "Michael B. Jordan" from matching "Michael Jordan"
                        if not celeb_mentioned and len(name_parts) >= 2:
                            first_name = name_parts[0]
                            last_name = name_parts[-1]
                            
                            # If EITHER name is common, we ONLY accept exact full name match
                            # which was already checked above - so skip fuzzy matching
                            if first_name in common_names or last_name in common_names:
                                # Already checked exact match above, don't do fuzzy
                                pass
                            else:
                                # For unusual names, allow first + last with small gap (no middle initial)
                                # Pattern: "FirstName LastName" with only spaces/hyphens between
                                pattern = rf'\b{re.escape(first_name)}[\s\-]+{re.escape(last_name)}\b'
                                if re.search(pattern, search_text):
                                    celeb_mentioned = True
                        
                        if not celeb_mentioned:
                            continue
                        
                        # Avoid duplicates
                        if title in seen_titles:
                            continue
                        seen_titles.add(title)
                        
                        # Extract publication date
                        pub_date = None
                        pub_date_str = ""
                        if "<pubDate>" in item:
                            date_start = item.find("<pubDate>") + 9
                            date_end = item.find("</pubDate>")
                            date_raw = item[date_start:date_end].strip()
                            try:
                                from email.utils import parsedate_to_datetime
                                pub_date = parsedate_to_datetime(date_raw)
                                pub_date_str = pub_date.strftime("%b %d, %Y")
                            except:
                                pub_date_str = datetime.now(timezone.utc).strftime("%b %d, %Y")
                        
                        # Skip if older than 7 days (weekly points system)
                        if pub_date and pub_date < cutoff_date:
                            continue
                        
                        # Extract article URL/link
                        article_url = ""
                        if "<link>" in item:
                            link_start = item.find("<link>") + 6
                            link_end = item.find("</link>")
                            if link_end > link_start:
                                article_url = item[link_start:link_end].replace("<![CDATA[", "").replace("]]>", "").strip()
                        # Some feeds use guid as link
                        if not article_url and '<guid isPermaLink="true">' in item:
                            guid_start = item.find('<guid isPermaLink="true">') + 25
                            guid_end = item.find("</guid>")
                            if guid_end > guid_start:
                                article_url = item[guid_start:guid_end].strip()
                        # Fallback to guid without attribute
                        if not article_url and "<guid>" in item:
                            guid_start = item.find("<guid>") + 6
                            guid_end = item.find("</guid>")
                            if guid_end > guid_start:
                                potential_url = item[guid_start:guid_end].strip()
                                if potential_url.startswith("http"):
                                    article_url = potential_url
                        
                        # Extract description/summary
                        summary = ""
                        if "<description>" in item:
                            d_start = item.find("<description>") + 13
                            d_end = item.find("</description>")
                            if d_end > d_start:
                                summary = item[d_start:d_end].replace("<![CDATA[", "").replace("]]>", "").strip()
                                summary = decode_html_entities(summary)
                                summary = re.sub(r'<[^>]+>', '', summary)
                                summary = summary[:200] + "..." if len(summary) > 200 else summary
                        
                        if not summary:
                            summary = title
                        
                        # Determine sentiment based on keywords
                        sentiment = "neutral"
                        positive_words = ["wins", "award", "celebrates", "engaged", "married", "baby", "pregnant", "success", "triumph", "praised", "honored", "birthday", "milestone"]
                        negative_words = ["arrested", "charged", "scandal", "controversy", "feud", "slams", "accused", "dies", "dead", "fired", "axed", "split", "divorce", "lawsuit"]
                        
                        if any(word in title_lower for word in positive_words):
                            sentiment = "positive"
                        elif any(word in title_lower for word in negative_words):
                            sentiment = "negative"
                        
                        real_news.append({
                            "title": title,
                            "summary": summary,
                            "source": source_name,
                            "url": article_url,
                            "date": pub_date_str or datetime.now(timezone.utc).strftime("%b %d, %Y"),
                            "is_scandal": sentiment == "negative",  # Keep for scoring but don't show label
                            "is_real": True
                        })
                        
                    except Exception as e:
                        continue
        
        # Sort by date (most recent first) and limit
        real_news.sort(key=lambda x: datetime.strptime(x.get("date", "Jan 1, 2020"), "%b %d, %Y"), reverse=True)
        return real_news[:max_articles]
        
    except Exception as e:
        logger.error(f"Error fetching real news for {name}: {e}")
        return []


async def generate_celebrity_news(name: str, category: str, real_news_context: str = None) -> List[dict]:
    """
    Fetch REAL news only from RSS feeds.
    No AI-generated news - only real articles with clickable links.
    """
    # Fetch REAL news from RSS feeds
    logger.info(f"Fetching real news for {name}...")
    real_news = await fetch_real_celebrity_news(name, max_articles=10)
    
    if real_news:
        logger.info(f"Found {len(real_news)} real news articles for {name}")
        return real_news[:5]
    
    # No real news found - return empty list (no AI generation)
    logger.info(f"No real news found for {name}")
    return []

def calculate_buzz_score(news: List[dict]) -> float:
    """Calculate buzz score based on news coverage"""
    if not news:
        return 10.0  # Base score
    
    score = 10.0
    for article in news:
        is_scandal = article.get("is_scandal", False)
        source = article.get("source", "").lower()
        
        # Base points for any mention
        if any(x in source for x in ["tmz", "daily mail", "sun"]):
            score += 3.0
        elif any(x in source for x in ["people", "entertainment weekly", "variety"]):
            score += 2.0
        elif any(x in source for x in ["bbc", "cnn", "guardian"]):
            score += 1.5
        else:
            score += 1.0
        
        # SCANDAL/CONTROVERSY BONUS = 25 points!
        if is_scandal:
            score += 25.0
    
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
    
    query_lower = q.lower().strip()
    
    # Get hot celebs from the CORRECT cache type (same as celebrity/search uses)
    hot_celebs_cache = await db.news_cache.find_one(
        {"type": "hot_celebs_from_news_v4"},
        {"_id": 0}
    )
    hot_celebs_list = hot_celebs_cache.get("hot_celebs", []) if hot_celebs_cache else []
    
    def get_hot_celeb_price(name):
        """Check if celeb is in hot list and return their premium price"""
        for hc in hot_celebs_list:
            hc_name = hc.get("name", "").lower()
            if hc_name == name.lower():
                return hc.get("price"), hc.get("tier"), True
            # Also check using are_same_celebrity for aliases
            if are_same_celebrity(hc.get("name", ""), name):
                return hc.get("price"), hc.get("tier"), True
        return None, None, False
    
    # PRIORITY 1: Check database for exact match first (most likely what user wants)
    exact_match = await db.celebrities.find_one(
        {"name": {"$regex": f"^{q}$", "$options": "i"}},
        {"_id": 0}
    )
    
    priority_suggestions = []
    if exact_match:
        tier = exact_match.get("tier", "D")
        # Use stored database price for consistency
        price = exact_match.get("price", get_base_price_for_tier(tier, exact_match["name"]))
        
        # Check if in hot celebs - use premium price
        hot_price, hot_tier, is_hot = get_hot_celeb_price(exact_match["name"])
        if hot_price:
            price = hot_price
            tier = hot_tier or tier
        
        # Get recognition score from stored metrics or tier_score
        recognition_score = exact_match.get("recognition_score")
        if recognition_score is None:
            # Fall back to tier_score if available
            tier_score = exact_match.get("tier_score", 0)
            if tier_score > 0:
                # Map tier_score to recognition_score (0-100 scale)
                recognition_score = min(100, max(0, tier_score))
            else:
                # Calculate from tier_metrics if available
                tier_metrics = exact_match.get("tier_metrics", {})
                if tier_metrics:
                    result = calculate_recognition_score_from_metrics(tier_metrics)
                    recognition_score = result.get("recognition_score", 50)
                else:
                    recognition_score = {"A": 85, "B": 70, "C": 50, "D": 30}.get(tier, 50)
        
        priority_suggestions.append({
            "name": exact_match["name"],
            "bio": exact_match.get("bio", "")[:100] + "..." if exact_match.get("bio") else "",
            "image": exact_match.get("image", ""),
            "tier": tier,
            "price": price,
            "estimated_price": price,
            "recognition_score": recognition_score,
            "is_exact_match": True,
            "is_hot": is_hot
        })
    
    # PRIORITY 2: Check database for partial matches (starts with query)
    if not exact_match:
        partial_matches = await db.celebrities.find(
            {"name": {"$regex": f"^{q}", "$options": "i"}},
            {"_id": 0}
        ).limit(5).to_list(5)
        
        for match in partial_matches:
            if not any(s.get("name") == match["name"] for s in priority_suggestions):
                tier = match.get("tier", "D")
                # Use stored database price for consistency
                price = match.get("price", get_base_price_for_tier(tier, match["name"]))
                
                # Check if in hot celebs - use premium price
                hot_price, hot_tier, is_hot = get_hot_celeb_price(match["name"])
                if hot_price:
                    price = hot_price
                    tier = hot_tier or tier
                
                # Get recognition score from stored metrics or tier_score
                recognition_score = match.get("recognition_score")
                if recognition_score is None:
                    tier_score = match.get("tier_score", 0)
                    if tier_score > 0:
                        recognition_score = min(100, max(0, tier_score))
                    else:
                        tier_metrics = match.get("tier_metrics", {})
                        if tier_metrics:
                            result = calculate_recognition_score_from_metrics(tier_metrics)
                            recognition_score = result.get("recognition_score", 50)
                        else:
                            recognition_score = {"A": 85, "B": 70, "C": 50, "D": 30}.get(tier, 50)
                
                priority_suggestions.append({
                    "name": match["name"],
                    "bio": match.get("bio", "")[:100] + "..." if match.get("bio") else "",
                    "image": match.get("image", ""),
                    "tier": tier,
                    "price": price,
                    "estimated_price": price,
                    "recognition_score": recognition_score,
                    "is_db_match": True,
                    "is_hot": is_hot
                })
    
    # PRIORITY 3: Check if query matches a known alias
    if query_lower in CELEBRITY_ALIASES:
        canonical_name = CELEBRITY_ALIASES[query_lower]
        if not any(s.get("name", "").lower() == canonical_name.lower() for s in priority_suggestions):
            wiki_info = await fetch_wikipedia_info(canonical_name)
            if wiki_info and wiki_info.get("name"):
                tier = determine_tier_from_bio(wiki_info.get("bio", ""), wiki_info["name"])
                price = get_dynamic_price(tier, 50, wiki_info["name"])
                priority_suggestions.append({
                    "name": wiki_info["name"],
                    "bio": wiki_info.get("bio", "")[:100] + "...",
                    "image": wiki_info.get("image", ""),
                    "tier": tier,
                    "price": price,
                    "estimated_price": price,
                    "is_alias_match": True
                })
    
    # Also check partial matches for common search terms
    alias_partial_matches = {
        "prince william": "William, Prince of Wales",
        "prince harry": "Prince Harry, Duke of Sussex", 
        "kate middleton": "Catherine, Princess of Wales",
        "king charles": "Charles III",
        "meghan markle": "Meghan, Duchess of Sussex",
        "the rock": "Dwayne Johnson",
        # Royal Children - William's kids
        "prince george": "Prince George of Wales",
        "george": "Prince George of Wales",
        "princess charlotte": "Princess Charlotte of Wales",
        "charlotte": "Princess Charlotte of Wales",
        "prince louis": "Prince Louis of Wales",
        "louis": "Prince Louis of Wales",
        # Royal Children - Harry's kids
        "prince archie": "Prince Archie of Sussex",
        "archie": "Prince Archie of Sussex",
        "princess lilibet": "Princess Lilibet of Sussex",
        "lilibet": "Princess Lilibet of Sussex",
    }
    
    for alias, canonical in alias_partial_matches.items():
        if alias.startswith(query_lower) or query_lower in alias:
            # Check if already in priority suggestions
            if not any(s.get("name") == canonical for s in priority_suggestions):
                wiki_info = await fetch_wikipedia_info(canonical)
                if wiki_info and wiki_info.get("name"):
                    tier = determine_tier_from_bio(wiki_info.get("bio", ""), wiki_info["name"])
                    price = get_dynamic_price(tier, 50, wiki_info["name"])
                    priority_suggestions.append({
                        "name": wiki_info["name"],
                        "bio": wiki_info.get("bio", "")[:100] + "...",
                        "image": wiki_info.get("image", ""),
                        "tier": tier,
                        "price": price,
                        "estimated_price": price,
                        "is_alias_match": True
                    })
    
    # Get Wikipedia autocomplete suggestions
    suggestions = await fetch_wikipedia_autocomplete(q)
    
    # Filter out any duplicates from Wikipedia results that are already in priority suggestions
    priority_names = {s["name"].lower() for s in priority_suggestions}
    filtered_suggestions = [s for s in suggestions if s.get("name", "").lower() not in priority_names]
    
    # Combine: priority first, then Wikipedia results
    all_suggestions = priority_suggestions + filtered_suggestions
    
    # Check for Brown Bread premium pricing on each suggestion
    for suggestion in all_suggestions:
        premium_price = await get_brown_bread_premium_by_name(suggestion.get("name", ""))
        if premium_price > 0:
            suggestion["estimated_price"] = premium_price
            suggestion["is_brown_bread_premium"] = True
    
    return {"suggestions": all_suggestions[:10]}  # Limit to 10 results

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


async def refresh_celeb_image_background(celeb_id: str, celeb_name: str):
    """Background task to refresh celebrity image without blocking the search response"""
    try:
        logger.info(f"Background: Refreshing Wikipedia image for {celeb_name}")
        wiki_info = await fetch_wikipedia_info(celeb_name)
        new_image = wiki_info.get("image", "")
        if new_image and "ui-avatars" not in new_image.lower():
            await db.celebrities.update_one(
                {"id": celeb_id},
                {"$set": {"image": new_image}}
            )
            logger.info(f"Background: Updated image for {celeb_name}")
        # Also update bio if it was placeholder
        celeb = await db.celebrities.find_one({"id": celeb_id}, {"_id": 0})
        if celeb and celeb.get("bio") == "Celebrity profile" and wiki_info.get("bio"):
            await db.celebrities.update_one(
                {"id": celeb_id},
                {"$set": {"bio": wiki_info["bio"][:500]}}
            )
    except Exception as e:
        logger.error(f"Background: Failed to refresh image for {celeb_name}: {e}")


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
    
    # FILTER OUT BANDS/GROUPS - Only allow individual celebrities
    banned_band_names = [
        "twenty one pilots", "21 pilots", "the 1975", "1975", "coldplay", "maroon 5",
        "one direction", "bts", "blackpink", "little mix", "fifth harmony",
        "backstreet boys", "nsync", "spice girls", "destiny's child", "jonas brothers",
        "imagine dragons", "fall out boy", "panic! at the disco", "panic at the disco",
        "green day", "blink-182", "blink 182", "arctic monkeys", "oasis", "blur",
        "take that", "westlife", "boyzone", "the beatles", "beatles", "rolling stones",
        "the rolling stones", "queen", "abba", "fleetwood mac", "the who", "pink floyd",
        "led zeppelin", "guns n roses", "nirvana", "pearl jam", "foo fighters",
        "red hot chili peppers", "u2", "radiohead", "the killers", "killers", "muse",
        "linkin park", "system of a down", "slipknot", "my chemical romance",
        "paramore", "all time low", "pierce the veil", "sleeping with sirens",
        "black veil brides", "bring me the horizon", "asking alexandria",
        "of mice & men", "a day to remember", "the wanted", "the vamps",
        "why don't we", "why dont we", "cnco", "prettymuch", "in real life",
        "brockhampton", "nct", "exo", "got7", "stray kids", "twice", "red velvet",
        "girls generation", "itzy", "aespa", "newjeans", "ive", "le sserafim",
        "nmixx", "(g)i-dle", "g idle", "mamamoo", "everglow", "loona", "dreamcatcher",
        "il divo", "florence and the machine", "florence + the machine",
        "onerepublic", "one republic", "jls", "mumford and sons", "mumford & sons"
    ]
    
    if name.lower() in banned_band_names:
        logger.info(f"Rejected band/group search: {name}")
        raise HTTPException(status_code=400, detail=f"'{name}' is a band/group. This game is for individual celebrities only.")
    
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
    
    logger.info(f"Search for '{name}': existing in DB = {existing is not None}")
    
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
            # Use database price - it's already correctly varied
            tier = "A" if (is_mega_star or is_royal) else existing.get("tier", "D")
            existing["tier"] = tier
            
            # Use the stored price from database (already has proper variation)
            db_price = existing.get("price", 3.0)
            
            # Check if this celeb qualifies for Brown Bread premium pricing
            new_price = await get_brown_bread_premium(existing, db_price)
            existing["price"] = new_price
        
        # Check if image is a placeholder - refresh in background (don't block response)
        current_image = existing.get("image", "")
        if "ui-avatars" in current_image.lower() or not current_image:
            # Schedule image refresh in background - don't await
            asyncio.create_task(refresh_celeb_image_background(existing.get("id"), celeb_name))
        
        # Regenerate news if empty, missing, or older than 24 hours
        # OPTIMIZATION: Skip for hot celebs - they already have recent news context
        should_refresh_news = False
        if hot_celeb_match:
            # Hot celebs have recent news - only refresh if completely empty
            if not existing.get("news") or len(existing.get("news", [])) == 0:
                should_refresh_news = True
        else:
            # Non-hot celebs - check 24 hour cache
            if not existing.get("news") or len(existing.get("news", [])) == 0:
                should_refresh_news = True
            elif existing.get("news_updated_at"):
                try:
                    news_time = datetime.fromisoformat(existing["news_updated_at"].replace("Z", "+00:00"))
                    if (datetime.now(timezone.utc) - news_time).total_seconds() > 86400:  # 24 hours
                        should_refresh_news = True
                except:
                    should_refresh_news = True
        
        if should_refresh_news:
            category = existing.get("category", "other")
            # Get real news context from hot celebs if available
            real_news_context = hot_celeb_match.get("hot_reason") if hot_celeb_match else None
            news = await generate_celebrity_news(celeb_name, category, real_news_context)
            existing["news"] = news
            # Update in database with timestamp
            await db.celebrities.update_one(
                {"id": existing.get("id")},
                {"$set": {"news": news, "news_updated_at": datetime.now(timezone.utc).isoformat()}}
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
    
    # REJECT if no Wikipedia page found (bio is default placeholder or wiki_url is empty)
    if not wiki_info.get("wiki_url") or wiki_info.get("bio") == "Celebrity profile":
        raise HTTPException(
            status_code=404, 
            detail=f"'{search.name}' doesn't have a Wikipedia page. Only celebrities with Wikipedia profiles are included in the game."
        )
    
    # Use override category if provided, otherwise detect from bio
    if override_category:
        category = override_category
    else:
        category = detect_category_from_bio(wiki_info.get("bio", ""), wiki_info["name"])
    
    # Calculate celebrity tier using new Wikipedia-based metrics system
    tier_result = None
    async with httpx.AsyncClient() as http_client:
        tier_result = await calculate_tier_from_wikipedia_data(wiki_info["name"], http_client)
        tier = tier_result["tier"]
        base_price = tier_result["price"]
    
    # Generate news - pass real news context if available from hot celebs
    real_news_context = hot_celeb_match.get("hot_reason") if hot_celeb_match else None
    news = await generate_celebrity_news(wiki_info["name"], category, real_news_context)
    
    # Buzz score starts at 0 - will accumulate weekly points based on news mentions
    # Resets every Monday
    buzz_score = 0
    
    # Final price using tier-based pricing
    price = base_price  # Use the calculated price from tier system
    
    # If this celeb is in Hot Celebs, use that price (includes news premium)
    if hot_celeb_match:
        price = hot_celeb_match["price"]
        tier = hot_celeb_match.get("tier", tier)
    
    # Check if celebrity is deceased (look for death indicators in bio)
    bio_lower = wiki_info.get("bio", "").lower()
    
    # Improved deceased detection patterns
    deceased_patterns = [
        # Past tense indicators
        "was a ", "was an ", 
        # Death phrases
        "died ", "passed away", "death of", "who died", "after his death", "after her death",
        "at the time of his death", "at the time of her death",
        # Date range patterns (birth-death years like "1950–2020")
        "1900–", "1901–", "1902–", "1903–", "1904–", "1905–", "1906–", "1907–", "1908–", "1909–",
        "1910–", "1911–", "1912–", "1913–", "1914–", "1915–", "1916–", "1917–", "1918–", "1919–",
        "1920–", "1921–", "1922–", "1923–", "1924–", "1925–", "1926–", "1927–", "1928–", "1929–",
        "1930–", "1931–", "1932–", "1933–", "1934–", "1935–", "1936–", "1937–", "1938–", "1939–",
        "1940–", "1941–", "1942–", "1943–", "1944–", "1945–", "1946–", "1947–", "1948–", "1949–",
        "1950–", "1951–", "1952–", "1953–", "1954–", "1955–", "1956–", "1957–", "1958–", "1959–",
        "1960–", "1961–", "1962–", "1963–", "1964–", "1965–", "1966–", "1967–", "1968–", "1969–",
        "1970–", "1971–", "1972–", "1973–", "1974–", "1975–", "1976–", "1977–", "1978–", "1979–",
        "1980–", "1981–", "1982–", "1983–", "1984–", "1985–", "1986–", "1987–", "1988–", "1989–",
        "1990–", "1991–", "1992–", "1993–", "1994–", "1995–", "1996–", "1997–", "1998–", "1999–",
        "2000–", "2001–", "2002–", "2003–", "2004–", "2005–", "2006–", "2007–", "2008–", "2009–",
        "2010–", "2011–", "2012–", "2013–", "2014–", "2015–", "2016–", "2017–", "2018–", "2019–",
        "2020–", "2021–", "2022–", "2023–", "2024–", "2025–", "2026–",
        # Alternative date formats
        " – ", "—", # en-dash and em-dash between dates
    ]
    
    is_deceased = any(pattern in bio_lower for pattern in deceased_patterns)
    
    # Also check for date range pattern like "(1950 – 2020)" or "(1950-2020)"
    import re
    date_range_pattern = r'\(\d{4}\s*[–—-]\s*\d{4}\)'
    if re.search(date_range_pattern, wiki_info.get("bio", "")):
        is_deceased = True
    
    # MOST RELIABLE: Use Wikidata P570 (date of death) if available
    if wiki_info.get("is_deceased"):
        is_deceased = True
    
    # Known deceased celebrities - always mark as deceased (fallback)
    known_deceased = [
        "amy winehouse", "michael jackson", "prince", "david bowie", "whitney houston",
        "robin williams", "heath ledger", "paul walker", "chadwick boseman", "kobe bryant",
        "aretha franklin", "elvis presley", "marilyn monroe", "john lennon", "george michael",
        "carrie fisher", "alan rickman", "princess diana", "freddie mercury", "bob marley",
        "tupac shakur", "notorious b.i.g.", "mac miller", "juice wrld", "xxxtentacion",
        "avicii", "chester bennington", "chris cornell", "kurt cobain", "jimi hendrix",
        "janis joplin", "jim morrison", "philip seymour hoffman", "brittany murphy",
        "james dean", "audrey hepburn", "grace kelly", "elizabeth taylor", "marlon brando",
        "frank sinatra", "dean martin", "gene wilder", "stan lee", "stephen hawking",
        "nelson mandela", "muhammad ali", "diego maradona", "pele", "queen elizabeth",
        "elizabeth ii", "prince philip", "matthew perry", "lisa marie presley", "tina turner",
        "sinead o'connor", "tony bennett", "olivia newton-john", "ray liotta", "bob saget",
        "betty white", "cory monteith", "natalie wood", "lucille ball", "johnny cash",
        "june carter cash", "waylon jennings", "patsy cline", "hank williams"
    ]
    celeb_name_lower = wiki_info["name"].lower()
    if any(known in celeb_name_lower for known in known_deceased):
        is_deceased = True
    
    # Known LIVING celebrities - override false positives from "was" detection
    known_living = [
        "willie colon", "ozzy osbourne", "eric dane", "james van der beek",
        "kate garraway", "dolly parton", "cher", "mick jagger", "keith richards",
        "paul mccartney", "ringo starr", "bob dylan", "elton john"
    ]
    if any(known in celeb_name_lower for known in known_living):
        is_deceased = False
    
    # Extract birth year - prefer wiki_info birth_year, fallback to bio extraction
    birth_year = wiki_info.get("birth_year", 0)
    if not birth_year:
        birth_year = extract_birth_year_from_bio(wiki_info.get("bio", ""))
    age = calculate_age(birth_year)
    
    # Check for Brown Bread premium pricing (for elderly celebrities) - only if not already in Hot Celebs
    if not hot_celeb_match:
        temp_celeb = {"name": wiki_info["name"], "age": age, "is_deceased": is_deceased}
        price = await get_brown_bread_premium(temp_celeb, price)
    
    # Celebrities to skip AI generation for (use initials placeholder instead)
    # Determine image - prefer Wikipedia, fallback to initials placeholder (no AI)
    celebrity_image = wiki_info.get("image", "")
    
    # Final fallback to placeholder with initials
    if not celebrity_image or "ui-avatars" in celebrity_image.lower():
        clean_name = wiki_info["name"].replace(' ', '+')
        celebrity_image = f"https://ui-avatars.com/api/?name={clean_name}&size=400&background=1a1a1a&color=FF0099&bold=true&format=png"
    
    # Create celebrity object
    celebrity = Celebrity(
        name=wiki_info["name"],
        bio=wiki_info["bio"][:500] if wiki_info["bio"] else "No biography available.",
        image=celebrity_image,
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
    
    # Add tier metrics from classification
    if tier_result:
        doc['tier_score'] = tier_result.get('score', 0)
        doc['tier_metrics'] = tier_result.get('metrics', {})
        doc['tier_reasoning'] = tier_result.get('reasoning', [])
    
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
async def get_celebrities_by_category(category: str, response: Response):
    """Get 8 random celebrities by category using MongoDB $sample for true randomness.
    Only includes celebrities with valid Wikipedia data (bio and wiki_url).
    """
    import random
    
    # Prevent any caching
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    # Get random sample from ALL celebrities in this category
    # MongoDB $sample provides true randomness from the entire collection
    # FILTER: Get random celebrities from the category
    # Prioritize those with Wikipedia images, but include all valid celebs
    pipeline = [
        {"$match": {
            "category": category,
            "name": {"$ne": None, "$exists": True},
            "wiki_url": {"$exists": True, "$ne": ""}
        }},
        {"$sample": {"size": 8}},  # Random sample of exactly 8
        {"$project": {"_id": 0}}
    ]
    
    selected = await db.celebrities.aggregate(pipeline).to_list(8)
    
    return {"celebrities": selected[:8]}

@api_router.get("/stats")
async def get_stats():
    """Get site statistics including player count and transfer window"""
    transfer_window = is_transfer_window_open()
    
    # Player count set to 0 for now (fresh start)
    player_count = 0
    
    return {
        "player_count": player_count,
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
        "transfer_window": "Opens every Sunday 12pm-12am GMT (before new week)"
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
        "Kelly Osbourne", "Sharon Osbourne", "Ozzy Osbourne", "Lisa Rinna", "Kyle Richards",
        "Tyra Banks", "Hilary Duff", "Lindsay Lohan", "Paris Hilton", "Nicole Richie",
        # Sports
        "Cristiano Ronaldo", "Lionel Messi", "Neymar", "Kylian Mbappé", "Erling Haaland",
        "Lewis Hamilton", "Max Verstappen", "Serena Williams", "Roger Federer", "Rafael Nadal",
        "LeBron James", "Tom Brady", "Patrick Mahomes", "Travis Kelce",
        "Simone Biles", "Usain Bolt", "Tiger Woods", "Conor McGregor", "Floyd Mayweather",
        "David Beckham", "Wayne Rooney", "Harry Kane", "Marcus Rashford", "Bukayo Saka",
        "Adam Peaty",
        # Actors - more
        "Michael B. Jordan", "Chadwick Boseman", "Idris Elba", "Daniel Kaluuya",
        "Robert Carradine", "Martha Plimpton", "Russell Brand",
        # Tech/Business
        "Elon Musk", "Jeff Bezos", "Mark Zuckerberg", "Bill Gates", "Kim Kardashian",
        "Kylie Jenner", "Kendall Jenner", "Kourtney Kardashian", "Khloé Kardashian",
        # TV Stars
        "Oprah Winfrey", "Ellen DeGeneres", "Jimmy Fallon", "Jimmy Kimmel", "Trevor Noah",
        "James Corden", "Graham Norton", "Jonathan Ross", "Alan Carr", "David Letterman",
        "Andy Cohen", "Nadiya Hussain", "Ferne McCann",
        # Recently in news (2024-2025)
        "Britney Spears", "Shia LaBeouf", "Mia Goth", "Barry Manilow", "Eric Dane",
        "Liza Minnelli", "Jessica Alba", "Scott Wolf", "Tyreek Hill", "Jonathan Owens",
        "Sam Fender", "Cillian Murphy", "Robert Pattinson", "Pedro Pascal", "Jenna Ortega",
        "Aubrey Plaza", "Glen Powell", "Jacob Elordi", "Barry Keoghan", "Paul Mescal",
        # More current celebs
        "Taylor Lautner", "Selena Gomez", "Hailey Bieber", "Gigi Hadid", "Bella Hadid",
        "Cara Delevingne", "Emily Ratajkowski", "Megan Fox", "Machine Gun Kelly", "Pete Davidson",
        "Kim Petras", "Sam Smith", "Lil Nas X", "Megan Thee Stallion", "Ice Spice",
        # Love Island / UK Reality
        "Molly-Mae Hague", "Tommy Fury", "Olivia Attwood", "Chris Hughes", "Kem Cetinay",
        "Dani Dyer", "Jack Fincham", "Amber Davies", "Georgia Steel", "Megan Barton-Hanson",
    ]
    
    # RSS feeds to scan for hot celebs - expanded list
    rss_sources = [
        # UK Sources
        ("https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml", "BBC News"),
        ("https://www.theguardian.com/lifeandstyle/celebrities/rss", "The Guardian"),
        ("https://www.mirror.co.uk/3am/rss.xml", "Daily Mirror"),
        ("https://www.thesun.co.uk/tvandshowbiz/feed/", "The Sun"),
        ("https://www.dailymail.co.uk/tvshowbiz/index.rss", "Daily Mail"),
        ("https://metro.co.uk/entertainment/feed/", "Metro"),
        ("https://www.express.co.uk/celebrity-news/feed", "Express"),
        ("https://www.independent.co.uk/topic/celebrities/rss", "The Independent"),
        # US Sources
        ("https://www.tmz.com/rss.xml", "TMZ"),
        ("https://people.com/feed/", "People"),
        ("https://pagesix.com/feed/", "Page Six"),
        ("https://www.etonline.com/news/rss", "Entertainment Tonight"),
        ("https://www.usmagazine.com/feed/", "Us Weekly"),
        ("https://www.hollywoodreporter.com/feed/", "Hollywood Reporter"),
        ("https://variety.com/feed/", "Variety"),
        ("https://www.buzzfeed.com/celebrity.xml", "BuzzFeed"),
        ("https://www.eonline.com/syndication/feeds/rssfeeds/topstories.xml", "E! News"),
        ("https://deadline.com/feed/", "Deadline"),
        # Music
        ("https://www.billboard.com/feed/", "Billboard"),
        ("https://www.rollingstone.com/feed/", "Rolling Stone"),
        ("https://www.nme.com/feed", "NME"),
        # General
        ("https://rss.cnn.com/rss/cnn_showbiz.rss", "CNN"),
        ("https://www.huffpost.com/section/entertainment/feed", "HuffPost"),
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
                    "headline": headline,
                    "headlines": [h["title"] for h in all_headlines if name_lower in h["title"].lower()][:5]  # Store up to 5 headlines
                }
        
        # Sort by mention count - ONLY include celebrities with 2+ mentions (lowered from 3)
        sorted_celebs = sorted(
            [(name, data) for name, data in celeb_mentions.items() if data["count"] >= 2],
            key=lambda x: x[1]["count"], 
            reverse=True
        )
        
        # Fetch details for top celebrities - need at least 15 with real photos
        hot_list = []
        
        for name, data in sorted_celebs:
            if len(hot_list) >= 18:  # Get a few extra in case some don't have photos
                break
            
            # SKIP: Michael Jordan (basketball) - too common a name, causes false matches
            # Use Michael B. Jordan for the actor instead
            if name.lower() == "michael jordan":
                continue
            
            # SKIP celebs with fewer than 2 actual headlines (requirement: minimum 2 news articles)
            actual_headlines = data.get("headlines", [])
            if len(actual_headlines) < 2:
                continue
            
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
                        
                        # First check if celeb exists in database to use their stored tier/price
                        db_celeb = await db.celebrities.find_one(
                            {"name": {"$regex": f"^{actual_name}$", "$options": "i"}}
                        )
                        
                        if db_celeb:
                            # Use database values for consistency
                            tier = db_celeb.get("tier", "C")
                            category = db_celeb.get("category", "other")
                            base_price = db_celeb.get("price", 3.0)
                        else:
                            # Calculate for new celebs
                            tier = determine_tier_from_bio(bio, actual_name)
                            category = get_category_from_bio(bio, actual_name)
                            base_price = get_base_price_for_tier(tier, actual_name)
                        
                        # Apply small NEWS PREMIUM based on mention count (max 20% boost)
                        mention_count = data["count"]
                        if mention_count >= 5:
                            news_multiplier = 1.15  # 5+ mentions = 15% price boost
                        elif mention_count >= 3:
                            news_multiplier = 1.10  # 3-4 mentions = 10% price boost
                        else:
                            news_multiplier = 1.05  # Small boost for being in news
                        
                        price = round(base_price * news_multiplier, 1)
                        
                        # Enforce £15M price cap
                        if price > 15:
                            price = 15.0
                        
                        # Show the headlines that put them on the banner
                        hot_reason = data["headline"][:80] + "..." if data["headline"] else "Trending in news"
                        
                        # Add trending indicator if high mentions
                        trending_tag = ""
                        if mention_count >= 5:
                            trending_tag = "🔥🔥🔥"
                        elif mention_count >= 3:
                            trending_tag = "🔥🔥"
                        
                        hot_list.append({
                            "name": actual_name,
                            "tier": tier,
                            "category": category,
                            "price": price,
                            "base_price": base_price,
                            "news_premium": news_multiplier > 1.0,
                            "trending_tag": trending_tag,
                            "hot_reason": hot_reason,
                            "news_headlines": actual_headlines[:3],
                            "recent_articles": actual_headlines[:5],  # Include actual articles
                            "image": image,
                            "mention_count": mention_count,
                            "article_count": len(actual_headlines)
                        })
                        
                        # Store in DB for consistency with autocomplete
                        actual_name = wiki_data.get("title", name)
                        # Cap price at £15M before storing
                        stored_price = min(price, 15.0)
                        # Always update celebrity with current price for consistency
                        await db.celebrities.update_one(
                            {"name": {"$regex": f"^{actual_name}$", "$options": "i"}},
                            {"$set": {
                                "name": actual_name,
                                "tier": tier,
                                "category": category,
                                "image": image,
                                "bio": bio[:500],
                                "price": stored_price,  # Update price to match hot celebs (capped)
                                "wiki_url": f"https://en.wikipedia.org/wiki/{actual_name.replace(' ', '_')}",
                                "updated_at": datetime.now(timezone.utc).isoformat()
                            }},
                            upsert=True
                        )
            except Exception as e:
                logger.error(f"Error fetching {name}: {e}")
                continue
        
        # NO FALLBACK TO STATIC LIST - Only show celebrities who are ACTUALLY in the news
        # If we don't have enough, that's fine - better to show fewer real results than fake ones
        # The frontend will handle showing a message if the list is empty
    
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
        "next_price_update": "Sunday 12pm GMT"
    }

# ==========================================
# PRICE WATCH FEATURE
# ==========================================

class PriceWatchCreate(BaseModel):
    celebrity_name: str
    target_price: float
    alert_type: str = "below"  # "below" or "above"

class PriceWatchUpdate(BaseModel):
    target_price: Optional[float] = None
    alert_type: Optional[str] = None
    is_active: Optional[bool] = None

@api_router.get("/price-watch/{team_id}")
async def get_price_watches(team_id: str):
    """Get all price watches for a team"""
    watches = await db.price_watches.find(
        {"team_id": team_id, "is_active": True},
        {"_id": 0}
    ).to_list(100)
    
    # Batch fetch all celebrities in one query (fix N+1 problem)
    if watches:
        celeb_names = [w['celebrity_name'] for w in watches]
        celebs = await db.celebrities.find(
            {"name": {"$in": celeb_names}},
            {"_id": 0, "name": 1, "price": 1, "tier": 1, "image": 1}
        ).to_list(100)
        celeb_map = {c['name'].lower(): c for c in celebs}
        
        # Enrich with current prices
        for watch in watches:
            celeb = celeb_map.get(watch['celebrity_name'].lower())
            if celeb:
                watch["current_price"] = celeb.get("price", 0)
                watch["tier"] = celeb.get("tier", "D")
                watch["image"] = celeb.get("image", "")
                
                # Check if target reached
                if watch["alert_type"] == "below":
                    watch["target_reached"] = celeb.get("price", 0) <= watch["target_price"]
                else:
                    watch["target_reached"] = celeb.get("price", 0) >= watch["target_price"]
            else:
                watch["current_price"] = 0
                watch["target_reached"] = False
    
    return {"watches": watches, "team_id": team_id}

@api_router.post("/price-watch/{team_id}")
async def create_price_watch(team_id: str, watch: PriceWatchCreate):
    """Create a new price watch for a celebrity"""
    # Verify team exists
    team = await db.teams.find_one({"id": team_id}, {"_id": 0})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check if celebrity exists
    celeb = await db.celebrities.find_one(
        {"name": {"$regex": f"^{watch.celebrity_name}$", "$options": "i"}},
        {"_id": 0, "name": 1, "price": 1, "tier": 1, "image": 1}
    )
    if not celeb:
        raise HTTPException(status_code=404, detail="Celebrity not found in database")
    
    # Check if watch already exists
    existing = await db.price_watches.find_one({
        "team_id": team_id,
        "celebrity_name": {"$regex": f"^{watch.celebrity_name}$", "$options": "i"},
        "is_active": True
    })
    if existing:
        raise HTTPException(status_code=400, detail="Price watch already exists for this celebrity")
    
    # Limit to 10 active watches per team
    watch_count = await db.price_watches.count_documents({"team_id": team_id, "is_active": True})
    if watch_count >= 10:
        raise HTTPException(status_code=400, detail="Maximum 10 active price watches allowed")
    
    # Create the watch
    watch_doc = {
        "id": str(uuid.uuid4()),
        "team_id": team_id,
        "celebrity_name": celeb["name"],  # Use canonical name
        "target_price": watch.target_price,
        "alert_type": watch.alert_type,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_active": True,
        "notified": False
    }
    
    await db.price_watches.insert_one(watch_doc)
    if "_id" in watch_doc:
        del watch_doc["_id"]
    
    # Add current price info
    watch_doc["current_price"] = celeb.get("price", 0)
    watch_doc["tier"] = celeb.get("tier", "D")
    watch_doc["image"] = celeb.get("image", "")
    watch_doc["target_reached"] = (
        celeb.get("price", 0) <= watch.target_price if watch.alert_type == "below" 
        else celeb.get("price", 0) >= watch.target_price
    )
    
    return {"watch": watch_doc, "message": f"Now watching {celeb['name']} for price {'drop' if watch.alert_type == 'below' else 'rise'} to £{watch.target_price}M"}

@api_router.delete("/price-watch/{team_id}/{watch_id}")
async def delete_price_watch(team_id: str, watch_id: str):
    """Delete a price watch"""
    result = await db.price_watches.delete_one({"id": watch_id, "team_id": team_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Price watch not found")
    return {"success": True, "message": "Price watch removed"}

@api_router.put("/price-watch/{team_id}/{watch_id}")
async def update_price_watch(team_id: str, watch_id: str, update: PriceWatchUpdate):
    """Update a price watch"""
    update_fields = {}
    if update.target_price is not None:
        update_fields["target_price"] = update.target_price
    if update.alert_type is not None:
        update_fields["alert_type"] = update.alert_type
    if update.is_active is not None:
        update_fields["is_active"] = update.is_active
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_fields["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.price_watches.update_one(
        {"id": watch_id, "team_id": team_id},
        {"$set": update_fields}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Price watch not found")
    
    return {"success": True, "message": "Price watch updated"}

@api_router.get("/price-watch/{team_id}/triggered")
async def get_triggered_watches(team_id: str):
    """Get all price watches that have hit their target"""
    watches = await db.price_watches.find(
        {"team_id": team_id, "is_active": True},
        {"_id": 0}
    ).to_list(100)
    
    triggered = []
    if watches:
        # Batch fetch all celebrities in one query (fix N+1 problem)
        celeb_names = [w['celebrity_name'] for w in watches]
        celebs = await db.celebrities.find(
            {"name": {"$in": celeb_names}},
            {"_id": 0, "name": 1, "price": 1, "tier": 1, "image": 1}
        ).to_list(100)
        celeb_map = {c['name'].lower(): c for c in celebs}
        
        for watch in watches:
            celeb = celeb_map.get(watch['celebrity_name'].lower())
            if celeb:
                current_price = celeb.get("price", 0)
                is_triggered = (
                    current_price <= watch["target_price"] if watch["alert_type"] == "below"
                    else current_price >= watch["target_price"]
                )
                if is_triggered:
                    watch["current_price"] = current_price
                    watch["tier"] = celeb.get("tier", "D")
                    watch["image"] = celeb.get("image", "")
                    watch["target_reached"] = True
                    triggered.append(watch)
    
    return {"triggered_watches": triggered, "count": len(triggered)}


async def get_hot_streaks(team_id: str):
    """Get hot streak notifications for team's celebrities
    
    A "hot streak" means a celebrity has been in the news for 3+ consecutive days.
    This indicates high buzz and potential price increases.
    """
    team = await db.teams.find_one({"id": team_id}, {"_id": 0})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    hot_streaks = []
    team_celebs = team.get("celebrities", [])
    
    if team_celebs:
        # Batch fetch all celebrities in one query (fix N+1 problem)
        celeb_ids = [c.get("celebrity_id") for c in team_celebs if c.get("celebrity_id")]
        celebs = await db.celebrities.find(
            {"id": {"$in": celeb_ids}},
            {"_id": 0}
        ).to_list(10)
        celeb_map = {c['id']: c for c in celebs}
        
        for celeb_data in team_celebs:
            celeb = celeb_map.get(celeb_data.get("celebrity_id"))
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
    """Get elderly celebrities (80+) for Brown Bread Watch - strategic picks for the bonus!
    
    SPECIAL PRICING: Top 3 oldest celebs can cost up to £15M (decreasing)
    - #1 oldest: £15M
    - #2 oldest: £13M  
    - #3 oldest: £11M
    - Rest: normal tier pricing (max £12M)
    """
    # Find living celebrities with known age >= 80 - get 10 for display
    elderly_celebs = await db.celebrities.find(
        {
            "is_deceased": False,
            "age": {"$gte": 80}
        },
        {"_id": 0}
    ).sort("age", -1).to_list(10)
    
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

@api_router.post("/celebrity/generate-image")
async def generate_celebrity_ai_image(data: dict):
    """Generate an AI image for a celebrity without a Wikipedia photo.
    
    Request body: {"name": "Celebrity Name", "description": "Optional description"}
    Returns: {"image": "data:image/png;base64,...", "cached": true/false}
    """
    name = data.get("name", "").strip()
    description = data.get("description", "")
    
    if not name:
        raise HTTPException(status_code=400, detail="Celebrity name required")
    
    # Check if already cached
    cached = await db.ai_images.find_one({"name": name.lower()}, {"_id": 0})
    if cached and cached.get("image"):
        return {"image": cached["image"], "cached": True, "name": name}
    
    # Generate new image
    image = await get_or_generate_celebrity_image(name, description)
    
    return {"image": image, "cached": False, "name": name}

@api_router.get("/celebrity/ai-image/{name}")
async def get_celebrity_ai_image(name: str):
    """Get or generate an AI image for a celebrity.
    
    Returns cached image if available, otherwise generates a new one.
    """
    # URL decode the name
    from urllib.parse import unquote
    name = unquote(name)
    
    if not name:
        raise HTTPException(status_code=400, detail="Celebrity name required")
    
    # Check cache first
    cached = await db.ai_images.find_one({"name": name.lower()}, {"_id": 0})
    if cached and cached.get("image"):
        return {"image": cached["image"], "cached": True, "name": name}
    
    # Generate new image
    image = await get_or_generate_celebrity_image(name, "")
    
    return {"image": image, "cached": False, "name": name}

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
    
    # News sources with RSS feeds - comprehensive list of UK and US outlets
    rss_sources = [
        # UK Priority Sources
        ("https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml", "BBC News", True),
        ("https://www.theguardian.com/lifeandstyle/celebrities/rss", "The Guardian", True),
        ("https://www.mirror.co.uk/3am/rss.xml", "Daily Mirror", True),
        ("https://www.thesun.co.uk/tvandshowbiz/feed/", "The Sun", True),
        ("https://www.dailymail.co.uk/tvshowbiz/index.rss", "Daily Mail", True),
        ("https://metro.co.uk/entertainment/feed/", "Metro", False),
        ("https://www.express.co.uk/celebrity-news/feed", "Daily Express", False),
        ("https://www.standard.co.uk/showbiz/rss", "Evening Standard", False),
        
        # US Entertainment Sources
        ("https://www.tmz.com/rss.xml", "TMZ", True),
        ("https://people.com/feed/", "People", True),
        ("https://pagesix.com/feed/", "Page Six", True),
        ("https://www.etonline.com/news/rss", "Entertainment Tonight", False),
        ("https://www.eonline.com/syndication/feeds/rssfeeds/topstories.xml", "E! News", False),
        ("https://www.usmagazine.com/feed/", "Us Weekly", False),
        ("https://www.hollywoodreporter.com/feed/", "Hollywood Reporter", False),
        ("https://variety.com/feed/", "Variety", False),
        ("https://deadline.com/feed/", "Deadline", False),
        ("https://www.billboard.com/feed/", "Billboard", False),
        ("https://www.rollingstone.com/feed/", "Rolling Stone", False),
        ("https://www.buzzfeed.com/celebrity.xml", "BuzzFeed", False),
        
        # General News with Entertainment
        ("https://feeds.reuters.com/reuters/entertainmentNews", "Reuters", False),
        ("https://rss.nytimes.com/services/xml/rss/nyt/Arts.xml", "New York Times", False),
        ("https://feeds.washingtonpost.com/rss/entertainment", "Washington Post", False),
        ("http://rss.cnn.com/rss/cnn_showbiz.rss", "CNN", False),
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
async def create_team(team_data: TeamCreate, request: Request):
    """Create a new team"""
    # Check for banned words
    if contains_banned_words(team_data.team_name):
        raise HTTPException(status_code=400, detail="Team name contains inappropriate language. Please choose another name.")
    
    current_points_week = get_monday_reset_week()
    
    # Check if user is authenticated
    user = await get_current_user(request)
    
    # If user is logged in, check if they already have a team
    if user:
        existing_team = await db.teams.find_one({"owner_user_id": user["user_id"]}, {"_id": 0})
        if existing_team:
            # Return existing team instead of creating new one
            return {"team": existing_team}
    
    team = UserTeam(
        team_name=team_data.team_name,
        last_transfer_reset=get_week_number()
    )
    doc = team.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['weekly_points'] = 0
    doc['points_week'] = current_points_week
    doc['total_points'] = 0
    
    # Link to user if authenticated
    if user:
        doc['owner_user_id'] = user["user_id"]
        doc['is_guest'] = False
    else:
        doc['is_guest'] = True
    
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
    
    # Check if weekly points reset needed (resets every Monday)
    current_points_week = get_monday_reset_week()
    if team.get("points_week") != current_points_week:
        # Reset weekly points to 0
        await db.teams.update_one(
            {"id": team_id},
            {"$set": {
                "weekly_points": 0,
                "points_week": current_points_week
            }}
        )
        team["weekly_points"] = 0
        team["points_week"] = current_points_week
    
    # Use weekly_points for display (defaults to 0 if not set)
    if "weekly_points" not in team:
        team["weekly_points"] = 0
    
    # Set total_points to weekly_points for display
    team["total_points"] = team.get("weekly_points", 0)
    
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
        previous_week_price=celebrity.get("previous_week_price", 0.0),  # Include price change data
        is_deceased=celebrity.get("is_deceased", False),  # Include deceased status for skull icon
        added_at=datetime.now(timezone.utc).isoformat()
    )
    
    new_budget = team.get("budget_remaining", 50) - price
    new_weekly_points = team.get("weekly_points", 0) + celeb_points
    new_brown_bread = team.get("brown_bread_bonus", 0) + brown_bread_bonus
    
    # Ensure points_week is set
    current_points_week = get_monday_reset_week()
    
    await db.teams.update_one(
        {"id": data.team_id},
        {
            "$push": {"celebrities": team_celeb.model_dump()},
            "$set": {
                "budget_remaining": new_budget,
                "weekly_points": new_weekly_points,
                "total_points": new_weekly_points,  # Keep in sync for display
                "brown_bread_bonus": new_brown_bread,
                "points_week": current_points_week
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
    """Transfer window: sell one celebrity and buy another (3 per week)
    
    IMPORTANT: When you sell, you get the CURRENT market price, not what you paid!
    So if you bought at £6M and they're now worth £15M, you get £15M back.
    """
    team = await db.teams.find_one({"id": data.team_id})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check transfer window
    current_week = get_week_number()
    if team.get("last_transfer_reset") != current_week:
        # Reset transfers for new week
        team["transfers_this_week"] = 0
    
    if team.get("transfers_this_week", 0) >= MAX_WEEKLY_TRANSFERS:
        raise HTTPException(status_code=400, detail=f"You've used all {MAX_WEEKLY_TRANSFERS} transfers this week! Wait until next week.")
    
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
    
    # Get CURRENT market price of celebrity being sold (not what they paid)
    sell_celeb_current = await db.celebrities.find_one({"id": data.sell_celebrity_id})
    if sell_celeb_current:
        current_sell_price = sell_celeb_current.get("price", sell_celeb["price"])
    else:
        current_sell_price = sell_celeb["price"]
    
    # Calculate budget after sale at CURRENT market price
    budget_after_sale = team.get("budget_remaining", 0) + current_sell_price
    
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
        is_deceased=buy_celeb.get("is_deceased", False),  # Include deceased status
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
    new_weekly_points = team.get("weekly_points", 0) - removed["buzz_score"]
    
    await db.teams.update_one(
        {"id": data.team_id},
        {
            "$pull": {"celebrities": {"celebrity_id": data.celebrity_id}},
            "$set": {
                "budget_remaining": new_budget,
                "weekly_points": max(0, new_weekly_points),
                "total_points": max(0, new_weekly_points)
            }
        }
    )
    
    updated_team = await db.teams.find_one({"id": data.team_id}, {"_id": 0})
    # Set total_points to weekly_points for display
    if updated_team:
        updated_team["total_points"] = updated_team.get("weekly_points", 0)
    return {"team": updated_team}


class TeamSubmit(BaseModel):
    team_id: str


@api_router.post("/team/submit")
async def submit_team(data: TeamSubmit):
    """Submit and lock team until next transfer window"""
    team = await db.teams.find_one({"id": data.team_id})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check minimum team size
    if len(team.get("celebrities", [])) < 5:
        raise HTTPException(status_code=400, detail="Need at least 5 celebrities to submit team")
    
    # Lock the team
    await db.teams.update_one(
        {"id": data.team_id},
        {"$set": {
            "is_locked": True,
            "locked_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    updated_team = await db.teams.find_one({"id": data.team_id}, {"_id": 0})
    return {"team": updated_team, "message": "Team submitted and locked until transfer window!"}


@api_router.get("/transfer-window-status")
async def get_transfer_window_status():
    """Check if transfer window is currently open (Sunday 12pm - 12am GMT)"""
    now = datetime.now(timezone.utc)
    is_sunday = now.weekday() == 6  # Sunday = 6
    is_open = is_sunday and 12 <= now.hour < 24  # 12pm to midnight
    
    # Calculate next transfer window (next Sunday 12pm)
    days_until_sunday = (6 - now.weekday()) % 7
    if days_until_sunday == 0:
        if now.hour >= 12:
            days_until_sunday = 7  # Next Sunday
    
    next_window = now + timedelta(days=days_until_sunday)
    next_window = next_window.replace(hour=12, minute=0, second=0, microsecond=0)
    
    return {
        "is_open": is_open,
        "next_window": next_window.isoformat(),
        "current_day": now.strftime("%A"),
        "message": "Transfer window open!" if is_open else f"Transfer window opens Sunday 12pm GMT"
    }


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
        
        # Check if weekly points need reset
        current_points_week = get_monday_reset_week()
        weekly_points = team.get("weekly_points", 0)
        if team.get("points_week") != current_points_week:
            weekly_points = 0  # Reset for display if new week
        
        leaderboard.append({
            "team_id": team["id"],
            "team_name": team.get("team_name", "Unknown"),
            "total_points": weekly_points,  # Use weekly points
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
    if len(league.get("team_ids", [])) >= league.get("max_teams", 10):
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

def get_current_week_str() -> str:
    """Get current ISO week string (e.g., '2026-W08')"""
    now = datetime.now(timezone.utc)
    return f"{now.year}-W{now.isocalendar()[1]:02d}"

def get_current_month_str() -> str:
    """Get current month string (e.g., '2026-02')"""
    now = datetime.now(timezone.utc)
    return f"{now.year}-{now.month:02d}"

@api_router.get("/league/{league_id}/weekly-leaderboard")
async def get_league_weekly_leaderboard(league_id: str):
    """Get weekly leaderboard for a specific league"""
    league = await db.leagues.find_one({"id": league_id}, {"_id": 0})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    current_week = get_current_week_str()
    team_ids = league.get("team_ids", [])
    teams = await db.teams.find({"id": {"$in": team_ids}}, {"_id": 0}).to_list(100)
    
    leaderboard = []
    for team in teams:
        # Get weekly points from league tracking or calculate from current points
        weekly_points = league.get("weekly_scores", {}).get(team["id"], team.get("total_points", 0))
        leaderboard.append({
            "team_id": team["id"],
            "team_name": team.get("team_name", "Unknown"),
            "team_color": team.get("team_color", "pink"),
            "team_icon": team.get("team_icon", "star"),
            "weekly_points": weekly_points,
            "celebrity_count": len(team.get("celebrities", [])),
            "badges": [b.get("id") for b in team.get("badges", [])],
            "is_owner": team["id"] == league.get("owner_team_id")
        })
    
    leaderboard.sort(key=lambda x: x["weekly_points"], reverse=True)
    
    return {
        "league_name": league["name"],
        "league_code": league["code"],
        "current_week": current_week,
        "leaderboard": leaderboard,
        "weekly_winner_history": league.get("weekly_winner_history", [])[-4:]  # Last 4 weeks
    }

@api_router.get("/league/{league_id}/monthly-leaderboard")
async def get_league_monthly_leaderboard(league_id: str):
    """Get monthly leaderboard for a specific league"""
    league = await db.leagues.find_one({"id": league_id}, {"_id": 0})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    current_month = get_current_month_str()
    team_ids = league.get("team_ids", [])
    teams = await db.teams.find({"id": {"$in": team_ids}}, {"_id": 0}).to_list(100)
    
    leaderboard = []
    for team in teams:
        # Get monthly accumulated points
        monthly_points = league.get("monthly_scores", {}).get(team["id"], 0)
        # If no monthly tracking yet, use current points as starting point
        if monthly_points == 0:
            monthly_points = team.get("total_points", 0)
        
        leaderboard.append({
            "team_id": team["id"],
            "team_name": team.get("team_name", "Unknown"),
            "team_color": team.get("team_color", "pink"),
            "team_icon": team.get("team_icon", "star"),
            "monthly_points": monthly_points,
            "weekly_wins_this_month": sum(1 for w in league.get("weekly_winner_history", []) 
                                          if w.get("team_id") == team["id"] and w.get("week", "").startswith(current_month[:4])),
            "badges": [b.get("id") for b in team.get("badges", [])],
            "is_owner": team["id"] == league.get("owner_team_id")
        })
    
    leaderboard.sort(key=lambda x: x["monthly_points"], reverse=True)
    
    return {
        "league_name": league["name"],
        "league_code": league["code"],
        "current_month": current_month,
        "leaderboard": leaderboard,
        "monthly_winner_history": league.get("monthly_winner_history", [])[-3:]  # Last 3 months
    }

@api_router.post("/league/{league_id}/record-weekly-scores")
async def record_weekly_scores(league_id: str):
    """Record current scores for the week and determine winner. Call this at end of week."""
    league = await db.leagues.find_one({"id": league_id})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    current_week = get_current_week_str()
    current_month = get_current_month_str()
    team_ids = league.get("team_ids", [])
    
    if not team_ids:
        raise HTTPException(status_code=400, detail="No teams in league")
    
    teams = await db.teams.find({"id": {"$in": team_ids}}, {"_id": 0}).to_list(100)
    
    if not teams:
        raise HTTPException(status_code=400, detail="No teams found")
    
    # Record weekly scores
    weekly_scores = {team["id"]: team.get("total_points", 0) for team in teams}
    
    # Find weekly winner
    winner = max(teams, key=lambda t: t.get("total_points", 0))
    winner_entry = {
        "week": current_week,
        "team_id": winner["id"],
        "team_name": winner.get("team_name", "Unknown"),
        "points": winner.get("total_points", 0)
    }
    
    # Update monthly scores (accumulate weekly points)
    monthly_scores = league.get("monthly_scores", {})
    for team_id, points in weekly_scores.items():
        monthly_scores[team_id] = monthly_scores.get(team_id, 0) + points
    
    # Update league
    await db.leagues.update_one(
        {"id": league_id},
        {
            "$set": {
                "current_week": current_week,
                "weekly_scores": weekly_scores,
                "current_month": current_month,
                "monthly_scores": monthly_scores
            },
            "$push": {"weekly_winner_history": winner_entry}
        }
    )
    
    # Award weekly winner badge
    badge = {
        "id": "weekly_winner",
        "earned_at": datetime.now(timezone.utc).isoformat(),
        "league_id": league_id,
        "week": current_week
    }
    
    await db.teams.update_one(
        {"id": winner["id"]},
        {
            "$push": {"badges": badge},
            "$inc": {"weekly_wins": 1}
        }
    )
    
    # Check for streak badges
    winner_history = league.get("weekly_winner_history", []) + [winner_entry]
    recent_winners = [w.get("team_id") for w in winner_history[-4:]]
    
    # Check for 4-week undefeated streak
    if len(recent_winners) >= 4 and all(w == winner["id"] for w in recent_winners[-4:]):
        existing_badges = await db.teams.find_one({"id": winner["id"]}, {"badges": 1})
        has_undefeated = any(b.get("id") == "undefeated" for b in existing_badges.get("badges", []))
        if not has_undefeated:
            undefeated_badge = {
                "id": "undefeated",
                "earned_at": datetime.now(timezone.utc).isoformat(),
                "league_id": league_id
            }
            await db.teams.update_one(
                {"id": winner["id"]},
                {"$push": {"badges": undefeated_badge}}
            )
    
    # Check for League Legend (3+ wins total in this league)
    updated_team = await db.teams.find_one({"id": winner["id"]})
    league_wins = sum(1 for w in winner_history if w.get("team_id") == winner["id"])
    if league_wins >= 3:
        has_legend = any(b.get("id") == "league_champion" and b.get("league_id") == league_id 
                        for b in updated_team.get("badges", []))
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
        "message": f"Weekly scores recorded! Winner: {winner.get('team_name')}",
        "weekly_winner": winner_entry,
        "weekly_scores": weekly_scores
    }

@api_router.post("/league/{league_id}/record-monthly-winner")
async def record_monthly_winner(league_id: str):
    """Record monthly winner and award badge. Call at end of month."""
    league = await db.leagues.find_one({"id": league_id})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    current_month = get_current_month_str()
    monthly_scores = league.get("monthly_scores", {})
    
    if not monthly_scores:
        raise HTTPException(status_code=400, detail="No monthly scores recorded")
    
    # Find monthly winner
    winner_id = max(monthly_scores, key=monthly_scores.get)
    winner_team = await db.teams.find_one({"id": winner_id}, {"_id": 0})
    
    if not winner_team:
        raise HTTPException(status_code=400, detail="Winner team not found")
    
    winner_entry = {
        "month": current_month,
        "team_id": winner_id,
        "team_name": winner_team.get("team_name", "Unknown"),
        "points": monthly_scores[winner_id]
    }
    
    # Update league and reset monthly scores
    await db.leagues.update_one(
        {"id": league_id},
        {
            "$set": {"monthly_scores": {}},
            "$push": {"monthly_winner_history": winner_entry}
        }
    )
    
    # Award monthly winner badge
    badge = {
        "id": "monthly_winner",
        "earned_at": datetime.now(timezone.utc).isoformat(),
        "league_id": league_id,
        "month": current_month
    }
    
    await db.teams.update_one(
        {"id": winner_id},
        {"$push": {"badges": badge}}
    )
    
    return {
        "message": f"Monthly winner recorded! {winner_team.get('team_name')} wins {current_month}!",
        "monthly_winner": winner_entry
    }

@api_router.get("/league/{league_id}/stats")
async def get_league_stats(league_id: str):
    """Get comprehensive league statistics"""
    league = await db.leagues.find_one({"id": league_id}, {"_id": 0})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    team_ids = league.get("team_ids", [])
    teams = await db.teams.find({"id": {"$in": team_ids}}, {"_id": 0}).to_list(100)
    
    # Calculate stats
    total_points = sum(t.get("total_points", 0) for t in teams)
    total_celebs = sum(len(t.get("celebrities", [])) for t in teams)
    
    # Most decorated team (most badges)
    most_badges_team = max(teams, key=lambda t: len(t.get("badges", [])), default=None)
    
    # Weekly winner frequency
    weekly_history = league.get("weekly_winner_history", [])
    winner_counts = {}
    for w in weekly_history:
        tid = w.get("team_id")
        winner_counts[tid] = winner_counts.get(tid, 0) + 1
    
    return {
        "league_name": league["name"],
        "league_code": league["code"],
        "member_count": len(team_ids),
        "max_teams": league.get("max_teams", 10),
        "total_points_all_teams": total_points,
        "total_celebrities_drafted": total_celebs,
        "weeks_played": len(weekly_history),
        "months_completed": len(league.get("monthly_winner_history", [])),
        "most_decorated_team": {
            "team_name": most_badges_team.get("team_name") if most_badges_team else None,
            "badge_count": len(most_badges_team.get("badges", [])) if most_badges_team else 0
        } if most_badges_team else None,
        "weekly_winner_frequency": winner_counts,
        "owner_team_id": league.get("owner_team_id"),
        "created_at": league.get("created_at")
    }

# ==================== LEAGUE CHAT ENDPOINTS ====================

@api_router.get("/league/{league_id}/chat")
async def get_league_chat(league_id: str, limit: int = 50):
    """Get recent chat messages for a league"""
    league = await db.leagues.find_one({"id": league_id}, {"_id": 0, "id": 1})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Get recent messages
    messages = await db.league_chat.find(
        {"league_id": league_id},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    # Reverse to get chronological order
    messages.reverse()
    
    return {"messages": messages}

@api_router.post("/league/{league_id}/chat")
async def send_league_chat(league_id: str, data: LeagueChatSend):
    """Send a chat message to a league"""
    league = await db.leagues.find_one({"id": league_id}, {"_id": 0, "team_ids": 1})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Verify team is in league
    if data.team_id not in league.get("team_ids", []):
        raise HTTPException(status_code=403, detail="Team not in this league")
    
    # Get team info
    team = await db.teams.find_one(
        {"id": data.team_id},
        {"_id": 0, "team_name": 1, "team_color": 1}
    )
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Basic profanity filter (reuse existing)
    message = data.message.strip()
    if len(message) > 500:
        message = message[:500]
    
    # Filter profanity
    filtered_message = message
    for word in BANNED_WORDS:
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        filtered_message = pattern.sub("*" * len(word), filtered_message)
    
    # Create message
    chat_message = {
        "id": str(uuid.uuid4()),
        "league_id": league_id,
        "team_id": data.team_id,
        "team_name": team.get("team_name", "Unknown"),
        "team_color": team.get("team_color", "pink"),
        "message": filtered_message,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    await db.league_chat.insert_one(chat_message)
    
    return {"message": "Message sent", "chat_message": chat_message}

@api_router.delete("/league/{league_id}/chat/{message_id}")
async def delete_league_chat(league_id: str, message_id: str, team_id: str):
    """Delete a chat message (only by sender or league owner)"""
    league = await db.leagues.find_one({"id": league_id}, {"_id": 0, "owner_team_id": 1})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    message = await db.league_chat.find_one(
        {"id": message_id, "league_id": league_id},
        {"_id": 0, "team_id": 1}
    )
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Only sender or league owner can delete
    if message.get("team_id") != team_id and league.get("owner_team_id") != team_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this message")
    
    await db.league_chat.delete_one({"id": message_id})
    
    return {"message": "Message deleted"}

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


# ==================== ADMIN ENDPOINTS ====================

@api_router.post("/admin/recategorize-all")
async def recategorize_all_celebrities():
    """
    Admin endpoint to recategorize all celebrities in the database.
    Re-runs the detect_category_from_bio function on each celebrity
    and updates any that have changed.
    """
    # Get all celebrities
    all_celebs = await db.celebrities.find({}).to_list(1000)
    
    updated = []
    unchanged = []
    errors = []
    
    for celeb in all_celebs:
        try:
            name = celeb.get("name", "")
            bio = celeb.get("bio", "")
            old_category = celeb.get("category", "other")
            
            # Detect the correct category
            new_category = detect_category_from_bio(bio, name)
            
            if new_category != old_category:
                # Update the celebrity
                await db.celebrities.update_one(
                    {"_id": celeb["_id"]},
                    {"$set": {"category": new_category}}
                )
                updated.append({
                    "name": name,
                    "old_category": old_category,
                    "new_category": new_category
                })
            else:
                unchanged.append(name)
        except Exception as e:
            errors.append({"name": celeb.get("name", "unknown"), "error": str(e)})
    
    return {
        "success": True,
        "summary": {
            "total_processed": len(all_celebs),
            "updated_count": len(updated),
            "unchanged_count": len(unchanged),
            "error_count": len(errors)
        },
        "updated": updated,
        "errors": errors if errors else None
    }


@api_router.post("/admin/regenerate-news")
async def regenerate_all_news(force_all: bool = False):
    """
    Admin endpoint to regenerate news for all celebrities.
    By default only regenerates for celebrities with empty/missing news.
    Set force_all=True to regenerate for ALL celebrities.
    """
    # Get all celebrities
    all_celebs = await db.celebrities.find({}).to_list(1000)
    
    regenerated = []
    skipped = []
    errors = []
    
    for celeb in all_celebs:
        try:
            name = celeb.get("name", "")
            category = celeb.get("category", "other")
            existing_news = celeb.get("news", [])
            
            # Skip if already has news and not forcing regeneration
            if not force_all and existing_news and len(existing_news) > 0:
                skipped.append(name)
                continue
            
            # Generate new news (2 months coverage)
            news = await generate_celebrity_news(name, category)
            
            if news and len(news) > 0:
                # Update the celebrity with new news
                await db.celebrities.update_one(
                    {"_id": celeb["_id"]},
                    {"$set": {"news": news}}
                )
                regenerated.append({
                    "name": name,
                    "news_count": len(news),
                    "first_headline": news[0].get("title", "")[:60] if news else ""
                })
            else:
                errors.append({"name": name, "error": "News generation returned empty"})
                
        except Exception as e:
            errors.append({"name": celeb.get("name", "unknown"), "error": str(e)})
    
    return {
        "success": True,
        "summary": {
            "total_processed": len(all_celebs),
            "regenerated_count": len(regenerated),
            "skipped_count": len(skipped),
            "error_count": len(errors)
        },
        "regenerated": regenerated,
        "skipped": skipped[:10] if len(skipped) > 10 else skipped,  # Only show first 10 skipped
        "errors": errors if errors else None
    }


@api_router.get("/admin/news-summary")
async def get_news_summary():
    """
    Admin endpoint to see which celebrities have news and which don't.
    """
    all_celebs = await db.celebrities.find({}, {"_id": 0, "name": 1, "news": 1}).to_list(1000)
    
    with_news = []
    without_news = []


@api_router.post("/admin/refresh-placeholder-images")
async def refresh_placeholder_images(limit: int = 50):
    """
    Admin endpoint to refresh images for celebrities with placeholder avatars.
    Fetches real Wikipedia images for celebrities that have ui-avatars placeholders.
    If Wikipedia doesn't have an image, tries AI generation.
    """
    # Find celebrities with placeholder images
    cursor = db.celebrities.find({
        "$or": [
            {"image": {"$regex": "ui-avatars", "$options": "i"}},
            {"image": ""},
            {"image": None}
        ]
    }, {"_id": 0}).limit(limit)
    
    celebs_to_update = await cursor.to_list(length=limit)
    
    updated = []
    failed = []
    
    for celeb in celebs_to_update:
        name = celeb.get("name", "")
        try:
            wiki_info = await fetch_wikipedia_info(name)
            new_image = wiki_info.get("image", "")
            
            if new_image and "ui-avatars" not in new_image.lower():
                # Update in database with Wikipedia image
                update_data = {"image": new_image}
                
                # Also update bio if it was placeholder
                if celeb.get("bio") == "Celebrity profile" and wiki_info.get("bio"):
                    update_data["bio"] = wiki_info["bio"][:500]
                
                await db.celebrities.update_one(
                    {"id": celeb.get("id")},
                    {"$set": update_data}
                )
                updated.append({
                    "name": name,
                    "old_image": celeb.get("image", "")[:50],
                    "new_image": new_image[:80],
                    "source": "wikipedia"
                })
            else:
                # Try AI image generation
                try:
                    ai_image = await get_or_generate_celebrity_image(name, celeb.get("bio", ""))
                    if ai_image:
                        update_data = {"image": ai_image}
                        if celeb.get("bio") == "Celebrity profile" and wiki_info.get("bio"):
                            update_data["bio"] = wiki_info["bio"][:500]
                        
                        await db.celebrities.update_one(
                            {"id": celeb.get("id")},
                            {"$set": update_data}
                        )
                        updated.append({
                            "name": name,
                            "old_image": celeb.get("image", "")[:50],
                            "new_image": "AI-generated",
                            "source": "ai"
                        })
                    else:
                        failed.append({
                            "name": name,
                            "reason": "Both Wikipedia and AI generation failed"
                        })
                except Exception as ai_error:
                    failed.append({
                        "name": name,
                        "reason": f"AI generation error: {str(ai_error)[:50]}"
                    })
        except Exception as e:
            failed.append({
                "name": name,
                "reason": str(e)
            })
    
    return {
        "message": f"Processed {len(celebs_to_update)} celebrities",
        "updated_count": len(updated),
        "failed_count": len(failed),
        "updated": updated,
        "failed": failed
    }


@api_router.post("/admin/populate-category/{category}")
async def populate_category(category: str, count: int = 20):
    """
    Admin endpoint to pre-populate celebrities in a category from the pool.
    Fetches 'count' new celebrities that aren't already in the database.
    """
    import random
    
    pool = CELEBRITY_POOLS.get(category, [])
    if not pool:
        return {"error": f"No pool found for category: {category}"}
    
    # Shuffle pool
    random.shuffle(pool)
    
    added = []
    skipped = []
    errors = []
    
    for name in pool:
        if len(added) >= count:
            break
        
        # Check if already exists
        existing = await db.celebrities.find_one(
            {"name": {"$regex": f"^{name}$", "$options": "i"}}
        )
        
        if existing:
            skipped.append(name)
            continue
        
        # Fetch new celebrity
        try:
            search = CelebritySearch(name=name)
            result = await search_celebrity(search, override_category=category)
            if result and result.get("name"):
                added.append(result.get("name"))
        except Exception as e:
            errors.append({"name": name, "error": str(e)})
    
    return {
        "success": True,
        "category": category,
        "added_count": len(added),
        "added": added,
        "skipped_count": len(skipped),
        "errors": errors if errors else None
    }
    
    for celeb in all_celebs:
        name = celeb.get("name", "Unknown")
        news = celeb.get("news", [])
        
        if news and len(news) > 0:
            with_news.append({
                "name": name,
                "news_count": len(news),
                "latest_headline": news[0].get("title", "")[:50] if news else ""
            })
        else:
            without_news.append(name)
    
    return {
        "total_celebrities": len(all_celebs),
        "with_news": len(with_news),
        "without_news": len(without_news),
        "celebrities_without_news": sorted(without_news),
        "celebrities_with_news": sorted(with_news, key=lambda x: x["name"])
    }


@api_router.get("/admin/category-summary")
async def get_category_summary():
    """
    Admin endpoint to get a summary of all celebrities by category.
    """
    all_celebs = await db.celebrities.find({}, {"_id": 0, "name": 1, "category": 1}).to_list(1000)
    
    by_category = {}
    for celeb in all_celebs:
        cat = celeb.get("category", "unknown")
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(celeb.get("name"))
    
    # Sort names within each category
    for cat in by_category:
        by_category[cat] = sorted(by_category[cat])
    
    return {
        "total_celebrities": len(all_celebs),
        "categories": {cat: {"count": len(names), "celebrities": names} for cat, names in sorted(by_category.items())}
    }


@api_router.post("/admin/weekly-price-reset")
async def weekly_price_reset():
    """
    Admin endpoint to perform weekly price reset.
    This should be called every Monday to:
    1. Store current price as previous_week_price
    2. Calculate new price based on accumulated buzz_score
    3. Reset buzz_score to 0 for the new week
    
    Returns summary of price changes.
    """
    logger.info("Starting weekly price reset...")
    
    # Get all celebrities
    all_celebs = await db.celebrities.find({}, {"_id": 0}).to_list(2000)
    
    price_changes = []
    increased = 0
    decreased = 0
    unchanged = 0
    
    for celeb in all_celebs:
        celeb_id = celeb.get("id")
        name = celeb.get("name", "")
        tier = celeb.get("tier", "D")
        buzz_score = celeb.get("buzz_score", 0)
        current_price = celeb.get("price", 5.0)
        
        # Calculate new price based on buzz score
        new_price = get_dynamic_price(tier, buzz_score, name)
        
        # Determine price change
        price_diff = new_price - current_price
        
        if price_diff > 0:
            increased += 1
            change_direction = "up"
        elif price_diff < 0:
            decreased += 1
            change_direction = "down"
        else:
            unchanged += 1
            change_direction = "unchanged"
        
        # Update celebrity in database
        await db.celebrities.update_one(
            {"id": celeb_id},
            {
                "$set": {
                    "previous_week_price": current_price,
                    "price": new_price,
                    "buzz_score": 0  # Reset buzz score for new week
                }
            }
        )
        
        # Record price history if there was a change
        if price_diff != 0:
            await record_price_history(celeb_id, name, new_price, tier, buzz_score)
            
            price_changes.append({
                "name": name,
                "tier": tier,
                "old_price": current_price,
                "new_price": new_price,
                "change": round(price_diff, 1),
                "direction": change_direction,
                "buzz_score_before_reset": buzz_score
            })
    
    # Sort by absolute change magnitude
    price_changes.sort(key=lambda x: abs(x["change"]), reverse=True)
    
    logger.info(f"Weekly price reset complete: {increased} up, {decreased} down, {unchanged} unchanged")
    
    return {
        "success": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_celebrities": len(all_celebs),
            "prices_increased": increased,
            "prices_decreased": decreased,
            "prices_unchanged": unchanged
        },
        "top_changes": price_changes[:20],  # Return top 20 biggest changes
        "all_changes": price_changes
    }


@api_router.get("/admin/price-change-preview")
async def preview_price_changes():
    """
    Preview what would happen if weekly price reset ran now.
    Doesn't modify any data.
    """
    # Get all celebrities
    all_celebs = await db.celebrities.find({}, {"_id": 0}).to_list(2000)
    
    preview = []
    
    for celeb in all_celebs:
        name = celeb.get("name", "")
        tier = celeb.get("tier", "D")
        buzz_score = celeb.get("buzz_score", 0)
        current_price = celeb.get("price", 5.0)
        previous_week_price = celeb.get("previous_week_price", 0)
        
        # Calculate what new price would be
        projected_price = get_dynamic_price(tier, buzz_score, name)
        price_diff = projected_price - current_price
        
        if price_diff != 0:
            preview.append({
                "name": name,
                "tier": tier,
                "current_price": current_price,
                "previous_week_price": previous_week_price,
                "projected_price": projected_price,
                "projected_change": round(price_diff, 1),
                "direction": "up" if price_diff > 0 else "down",
                "current_buzz_score": buzz_score
            })
    
    # Sort by absolute change
    preview.sort(key=lambda x: abs(x["projected_change"]), reverse=True)
    
    return {
        "preview_count": len(preview),
        "would_increase": len([p for p in preview if p["direction"] == "up"]),
        "would_decrease": len([p for p in preview if p["direction"] == "down"]),
        "top_changes": preview[:20],
        "all_projected_changes": preview
    }


@api_router.get("/admin/scheduler-status")
async def get_scheduler_status():
    """
    Admin endpoint to check the status of scheduled tasks.
    Returns info about the weekly price reset job.
    """
    jobs = scheduler.get_jobs()
    job_info = []
    
    for job in jobs:
        job_info.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })
    
    # Get last execution from database
    last_execution = await db.scheduled_tasks.find_one(
        {"task": "weekly_price_reset"},
        {"_id": 0},
        sort=[("executed_at", -1)]
    )
    
    return {
        "scheduler_running": scheduler.running,
        "jobs": job_info,
        "last_weekly_reset": last_execution
    }


@api_router.post("/admin/trigger-weekly-reset")
async def trigger_weekly_reset_manually():
    """
    Admin endpoint to manually trigger the weekly price reset.
    Use this if the scheduled task needs to be run outside of its normal schedule.
    """
    logger.info("Manual trigger of weekly price reset requested")
    
    # Run the scheduled task immediately
    await scheduled_weekly_price_reset()
    
    return {
        "success": True,
        "message": "Weekly price reset triggered manually",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# ==================== WIKIDATA CELEBRITY UPDATE ====================

# Map Wikidata occupation QIDs to our categories
OCCUPATION_TO_CATEGORY = {
    # Movie Stars
    "Q33999": "movie_stars",  # actor
    "Q10800557": "movie_stars",  # film actor
    "Q3455803": "movie_stars",  # film director
    "Q28389": "movie_stars",  # screenwriter
    # TV Actors
    "Q10798782": "tv_actors",  # television actor
    "Q5716684": "tv_actors",  # television presenter (also check TV personalities)
    # TV Personalities
    "Q18814623": "tv_personalities",  # television personality
    "Q2526255": "tv_personalities",  # film director - might need disambiguation
    "Q947873": "tv_personalities",  # presenter
    "Q1607826": "tv_personalities",  # news presenter
    # Musicians
    "Q177220": "musicians",  # singer
    "Q639669": "musicians",  # musician
    "Q488205": "musicians",  # singer-songwriter
    "Q36834": "musicians",  # composer
    "Q753110": "musicians",  # songwriter
    "Q183945": "musicians",  # record producer
    "Q10816969": "musicians",  # rapper
    "Q806349": "musicians",  # bandleader
    "Q55960555": "musicians",  # recording artist
    # Athletes
    "Q937857": "athletes",  # association football player
    "Q11774891": "athletes",  # sports manager
    "Q2309784": "athletes",  # sport cyclist
    "Q10833314": "athletes",  # tennis player
    "Q13381753": "athletes",  # athletics competitor
    "Q10843263": "athletes",  # baseball player
    "Q3665646": "athletes",  # basketball player
    "Q14089670": "athletes",  # racing driver
    "Q11338576": "athletes",  # boxer
    "Q15117302": "athletes",  # swimmer
    "Q19204627": "athletes",  # American football player
    "Q4009406": "athletes",  # gymnast
    "Q628099": "athletes",  # golfer
    # Reality TV
    "Q44508716": "reality_tv",  # influencer
    "Q27533925": "reality_tv",  # reality television participant
    "Q19595175": "reality_tv",  # internet celebrity
    # Royals - These are usually identified by description
    "Q116": "royals",  # monarch
    "Q2478141": "royals",  # aristocrat
    "Q36180": "royals",  # writer (might need context)
    # Public Figure
    "Q82955": "public_figure",  # politician
    "Q131524": "public_figure",  # entrepreneur
    "Q372436": "public_figure",  # statesperson
    "Q40348": "public_figure",  # lawyer
    # Other
    "Q3499072": "other",  # chef
    "Q245068": "other",  # comedian
    "Q36180": "other",  # writer
    "Q1930187": "other",  # journalist
    "Q49757": "other",  # poet
    "Q214917": "other",  # playwright
    "Q121594": "other",  # professor
}

async def fetch_wikidata_info(name: str, client: httpx.AsyncClient, headers: dict) -> dict:
    """
    Fetch celebrity info from Wikidata: image (P18), occupation (P106), and description.
    Returns dict with image_url, occupations list, and suggested_category.
    """
    result = {"image_url": None, "occupations": [], "suggested_category": None, "description": ""}
    
    try:
        # Step 1: Search for the entity
        search_params = {
            'action': 'wbsearchentities',
            'search': name,
            'language': 'en',
            'type': 'item',
            'limit': 5,
            'format': 'json'
        }
        
        search_response = await client.get(
            'https://www.wikidata.org/w/api.php',
            params=search_params,
            headers=headers,
            timeout=10.0
        )
        
        if search_response.status_code != 200:
            return result
        
        search_data = search_response.json()
        search_results = search_data.get('search', [])
        
        if not search_results:
            return result
        
        # Find the best match - prefer results with descriptions indicating they're entertainers/public figures
        best_match = None
        priority_keywords = ['singer', 'actor', 'actress', 'footballer', 'model', 'personality', 
                           'television', 'musician', 'athlete', 'boxer', 'presenter', 'celebrity',
                           'british', 'american', 'reality', 'royal', 'prince', 'princess', 'duke', 'duchess']
        
        for sr in search_results:
            desc = sr.get('description', '').lower()
            # Skip if description suggests wrong person (e.g., basketball player for UK reality star)
            if 'basketball' in desc and 'british' not in desc:
                continue
            if 'baseball' in desc and 'british' not in desc:
                continue
            
            # Prefer matches with relevant descriptions
            if any(kw in desc for kw in priority_keywords):
                best_match = sr
                break
        
        if not best_match:
            best_match = search_results[0]
        
        qid = best_match.get('id')
        result['description'] = best_match.get('description', '')
        
        # Step 2: Get entity details (image + occupation)
        entity_params = {
            'action': 'wbgetentities',
            'ids': qid,
            'props': 'claims',
            'format': 'json'
        }
        
        entity_response = await client.get(
            'https://www.wikidata.org/w/api.php',
            params=entity_params,
            headers=headers,
            timeout=10.0
        )
        
        if entity_response.status_code != 200:
            return result
        
        entity_data = entity_response.json()
        entity = entity_data.get('entities', {}).get(qid, {})
        claims = entity.get('claims', {})
        
        # Extract image (P18)
        if 'P18' in claims:
            img_file = claims['P18'][0]['mainsnak']['datavalue']['value']
            img_file_encoded = img_file.replace(' ', '_')
            result['image_url'] = f"https://commons.wikimedia.org/wiki/Special:FilePath/{img_file_encoded}?width=400"
        
        # Extract occupations (P106) and map to category
        if 'P106' in claims:
            for occ_claim in claims['P106']:
                try:
                    occ_qid = occ_claim['mainsnak']['datavalue']['value']['id']
                    result['occupations'].append(occ_qid)
                    
                    # Check if this occupation maps to a category
                    if occ_qid in OCCUPATION_TO_CATEGORY and not result['suggested_category']:
                        result['suggested_category'] = OCCUPATION_TO_CATEGORY[occ_qid]
                except (KeyError, TypeError):
                    pass
        
        # Also check description for category hints
        desc_lower = result['description'].lower()
        if not result['suggested_category']:
            if any(kw in desc_lower for kw in ['prince', 'princess', 'duke', 'duchess', 'king', 'queen', 'royal']):
                result['suggested_category'] = 'royals'
            elif any(kw in desc_lower for kw in ['reality television', 'reality tv', 'love island', 'towie']):
                result['suggested_category'] = 'reality_tv'
            elif any(kw in desc_lower for kw in ['television personality', 'tv personality', 'presenter', 'host']):
                result['suggested_category'] = 'tv_personalities'
            elif any(kw in desc_lower for kw in ['singer', 'musician', 'rapper', 'songwriter']):
                result['suggested_category'] = 'musicians'
            elif any(kw in desc_lower for kw in ['film actor', 'actress', 'movie']):
                result['suggested_category'] = 'movie_stars'
            elif any(kw in desc_lower for kw in ['television actor', 'tv actor']):
                result['suggested_category'] = 'tv_actors'
            elif any(kw in desc_lower for kw in ['footballer', 'tennis', 'boxer', 'athlete', 'racing driver', 'cricketer']):
                result['suggested_category'] = 'athletes'
            elif any(kw in desc_lower for kw in ['politician', 'businessman', 'entrepreneur', 'activist']):
                result['suggested_category'] = 'public_figure'
            elif any(kw in desc_lower for kw in ['chef', 'comedian', 'author', 'writer', 'model']):
                result['suggested_category'] = 'other'
        
    except Exception as e:
        logger.warning(f"Error fetching Wikidata for {name}: {e}")
    
    return result


@api_router.post("/admin/update-celebrity-data")
async def update_celebrity_data_from_wikidata(batch_size: int = 20, delay_seconds: float = 1.0):
    """
    Update celebrities with missing images and recategorize based on Wikidata.
    Uses Wikidata API with rate limiting to avoid blocks.
    
    Args:
        batch_size: Number of celebrities to process per batch (default 20)
        delay_seconds: Delay between API calls (default 1.0 second)
    """
    headers = {
        'User-Agent': 'CelebrityBuzzIndex/1.0 (https://celebbuzzindex.com; admin@celebbuzzindex.com)',
        'Accept': 'application/json'
    }
    
    # Find celebrities needing updates (missing real image AND not already checked)
    celebs_needing_update = await db.celebrities.find(
        {
            'image': {'$regex': 'ui-avatars', '$options': 'i'},
            'wikidata_checked': {'$ne': True}  # Skip already checked ones
        },
        {'_id': 0, 'id': 1, 'name': 1, 'category': 1, 'image': 1}
    ).limit(batch_size).to_list(batch_size)
    
    if not celebs_needing_update:
        return {
            "success": True,
            "message": "No celebrities need updating",
            "updated": 0,
            "remaining": 0
        }
    
    # Count remaining (not yet checked)
    remaining_count = await db.celebrities.count_documents(
        {
            'image': {'$regex': 'ui-avatars', '$options': 'i'},
            'wikidata_checked': {'$ne': True}
        }
    )
    
    updated = 0
    skipped = 0
    errors = []
    
    async with httpx.AsyncClient() as client:
        for celeb in celebs_needing_update:
            celeb_id = celeb.get('id')
            name = celeb.get('name')
            old_category = celeb.get('category')
            
            try:
                # Fetch data from Wikidata
                wiki_data = await fetch_wikidata_info(name, client, headers)
                
                update_fields = {'wikidata_checked': True}  # Mark as checked
                
                # Update image if found
                if wiki_data['image_url']:
                    update_fields['image'] = wiki_data['image_url']
                
                # Update category if we got a suggestion and it differs
                if wiki_data['suggested_category'] and wiki_data['suggested_category'] != old_category:
                    update_fields['category'] = wiki_data['suggested_category']
                
                # Always update (to mark as checked even if no image found)
                await db.celebrities.update_one(
                    {'id': celeb_id},
                    {'$set': update_fields}
                )
                
                if wiki_data['image_url']:
                    updated += 1
                    logger.info(f"Updated {name}: image=True, category={wiki_data['suggested_category']}")
                else:
                    skipped += 1
                    logger.info(f"Marked {name} as checked: no image found on Wikidata")
                
                # Rate limiting delay
                await asyncio.sleep(delay_seconds)
                
            except Exception as e:
                errors.append({"name": name, "error": str(e)})
                logger.error(f"Error updating {name}: {e}")
    
    return {
        "success": True,
        "message": f"Processed {len(celebs_needing_update)} celebrities",
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
        "remaining": remaining_count - len(celebs_needing_update)
    }


@api_router.get("/admin/celebrity-update-status")
async def get_celebrity_update_status():
    """
    Get the current status of celebrity data (how many have images, categories breakdown).
    """
    total = await db.celebrities.count_documents({})
    
    with_wiki_image = await db.celebrities.count_documents({
        'image': {'$regex': 'wikimedia|wikipedia|commons', '$options': 'i'}
    })
    
    with_placeholder = await db.celebrities.count_documents({
        'image': {'$regex': 'ui-avatars', '$options': 'i'}
    })
    
    # Count how many still need checking
    not_checked = await db.celebrities.count_documents({
        'image': {'$regex': 'ui-avatars', '$options': 'i'},
        'wikidata_checked': {'$ne': True}
    })
    
    # Count how many need bio/category fix
    needs_bio_fix = await db.celebrities.count_documents({
        'bio': {'$regex': 'is a celebrity', '$options': 'i'},
        'bio_fixed': {'$ne': True}
    })
    
    # Category breakdown
    pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    category_counts = await db.celebrities.aggregate(pipeline).to_list(20)
    
    return {
        "total_celebrities": total,
        "with_real_images": with_wiki_image,
        "with_placeholder_images": with_placeholder,
        "not_yet_checked": not_checked,
        "needs_bio_category_fix": needs_bio_fix,
        "categories": {c['_id']: c['count'] for c in category_counts if c['_id']}
    }


def extract_category_from_description(description: str) -> str:
    """
    Extract category from the FIRST occupation mentioned in a Wikipedia description.
    E.g., "American singer-songwriter and actress" -> musicians (singer is first)
    """
    desc_lower = description.lower()
    
    import re
    
    # Check for ACTUAL royalty - must be a member of a royal family
    # This should NOT match honorary titles like "Queen of Pop", "Queen of Country", etc.
    # Look for patterns that indicate actual royal titles
    royal_patterns = [
        r'\bprince of wales\b', r'\bprincess of wales\b', 
        r'\bduke of (?:cambridge|sussex|york|edinburgh|kent|gloucester)\b',
        r'\bduchess of (?:cambridge|sussex|york|edinburgh|kent|cornwall)\b',
        r'\bking of (?:england|britain|uk|united kingdom|the united kingdom)\b',
        r'\bqueen of (?:england|britain|uk|united kingdom|the united kingdom)\b',
        r'\broyal family\b', r'\bbritish royal\b', r'\broyal household\b',
        r'\bheir to the throne\b', r'\bline of succession\b',
        r'\bmember of the british royal family\b',
        r'\bhouse of windsor\b', r'\bmountbatten-windsor\b',
    ]
    for pattern in royal_patterns:
        if re.search(pattern, desc_lower):
            return 'royals'
    
    # Also check if it starts with a royal title (for Wikipedia pages of royals)
    if desc_lower.startswith(('prince ', 'princess ', 'duke ', 'duchess ')):
        return 'royals'
    
    # Extended pattern to capture the occupation word after "is a/an [nationality]"
    # First, let's extract everything after "is a/an" up to the first comma or period
    is_a_pattern = r'is (?:a|an) ([^,\.]+)'
    match = re.search(is_a_pattern, desc_lower)
    
    occupation_phrase = None
    if match:
        occupation_phrase = match.group(1).strip()
    
    # Define direct occupation mappings
    occupation_to_category = {
        # Musicians
        'singer': 'musicians', 'singer-songwriter': 'musicians', 'rapper': 'musicians', 
        'musician': 'musicians', 'songwriter': 'musicians', 'composer': 'musicians', 
        'vocalist': 'musicians', 'saxophonist': 'musicians', 'drummer': 'musicians', 
        'guitarist': 'musicians', 'pianist': 'musicians', 'dj': 'musicians',
        # Athletes
        'footballer': 'athletes', 'professional footballer': 'athletes',
        'boxer': 'athletes', 'cricketer': 'athletes', 'golfer': 'athletes', 
        'swimmer': 'athletes', 'gymnast': 'athletes', 'athlete': 'athletes', 
        'sprinter': 'athletes', 'olympian': 'athletes', 'tennis player': 'athletes',
        'racing driver': 'athletes', 'formula one': 'athletes',
        'basketball player': 'athletes', 'baseball player': 'athletes',
        # Actors
        'actor': 'movie_stars', 'actress': 'movie_stars', 'filmmaker': 'movie_stars',
        'director': 'movie_stars', 'screenwriter': 'movie_stars', 'film actor': 'movie_stars',
        'film actress': 'movie_stars',
        # TV
        'presenter': 'tv_personalities', 'television presenter': 'tv_personalities',
        'host': 'tv_personalities', 'broadcaster': 'tv_personalities', 
        'newsreader': 'tv_personalities', 'news anchor': 'tv_personalities',
        'television actor': 'tv_actors', 'television actress': 'tv_actors',
        # Other professions
        'chef': 'other', 'celebrity chef': 'other', 'restaurateur': 'other',
        'dancer': 'other', 'choreographer': 'other',
        'comedian': 'other', 'comic': 'other', 'stand-up': 'other',
        'author': 'other', 'writer': 'other', 'novelist': 'other',
        'model': 'other', 'supermodel': 'other',
        'journalist': 'other', 'youtuber': 'other', 'influencer': 'other',
        # Public figures
        'politician': 'public_figure', 'businessman': 'public_figure', 
        'businesswoman': 'public_figure', 'entrepreneur': 'public_figure',
        'activist': 'public_figure', 'lawyer': 'public_figure',
        # Ambiguous - need context
        'personality': None, 'television': None, 'media': None, 'reality': None,
        'celebrity': None, 'former': None,
    }
    
    # Parse the occupation phrase to find actual occupation keywords
    # E.g., "English former professional footballer" -> footballer
    # E.g., "American singer-songwriter and actress" -> singer-songwriter
    # E.g., "British reality television personality and boxer" -> check both
    
    if occupation_phrase:
        # Check for direct occupation matches in the phrase
        for occ, cat in occupation_to_category.items():
            if cat and occ in occupation_phrase:
                return cat
    
    # IMPORTANT: For fallback checks, use only the FIRST SENTENCE to avoid
    # false positives from mentions of other people (e.g., "sex tape with singer Ray J")
    first_sentence = description.split('.')[0].lower() if description else desc_lower
    
    # Check first sentence for TV personality FIRST (before musicians/actors)
    # This handles cases like Kim Kardashian where "singer" appears later referring to someone else
    if 'media personality' in first_sentence or 'television personality' in first_sentence:
        return 'reality_tv'
    if 'socialite' in first_sentence:
        return 'reality_tv'
    if 'reality television' in first_sentence or 'reality tv' in first_sentence:
        return 'reality_tv'
    
    # Athletes (strong indicators - boxer, footballer are rarely mentioned for others)
    if 'boxer' in first_sentence or 'boxing' in first_sentence:
        return 'athletes'
    if 'footballer' in first_sentence or 'football player' in first_sentence:
        return 'athletes'
    if 'racing driver' in first_sentence or 'formula one' in first_sentence:
        return 'athletes'
    if 'tennis player' in first_sentence or 'cricketer' in first_sentence or 'golfer' in first_sentence:
        return 'athletes'
    if 'basketball player' in first_sentence or 'baseball player' in first_sentence:
        return 'athletes'
    if 'swimmer' in first_sentence or 'gymnast' in first_sentence or 'olympian' in first_sentence:
        return 'athletes'
    
    # Musicians - check in first sentence only
    if 'singer' in first_sentence or 'songwriter' in first_sentence:
        return 'musicians'
    if 'rapper' in first_sentence or 'musician' in first_sentence:
        return 'musicians'
    
    # Chefs and comedians
    if 'chef' in first_sentence or 'restaurateur' in first_sentence:
        return 'other'
    if 'comedian' in first_sentence or 'stand-up' in first_sentence or 'comic' in first_sentence:
        return 'other'
    
    # Actors
    if 'actor' in first_sentence or 'actress' in first_sentence:
        return 'movie_stars'
    
    # TV categories
    if 'television presenter' in first_sentence or 'tv presenter' in first_sentence:
        return 'tv_personalities'
    if 'television actor' in first_sentence or 'television actress' in first_sentence:
        return 'tv_actors'
    
    # Public figures
    if 'politician' in first_sentence:
        return 'public_figure'
    if 'businessman' in first_sentence or 'businesswoman' in first_sentence or 'entrepreneur' in first_sentence:
        return 'public_figure'
    
    # Other
    if 'model' in first_sentence or 'author' in first_sentence or 'writer' in first_sentence:
        return 'other'
    if 'journalist' in first_sentence or 'presenter' in first_sentence:
        return 'tv_personalities'
    
    # Default for "personality" with no clear occupation
    if 'personality' in first_sentence:
        return 'reality_tv'
    
    return None


async def fetch_wikipedia_bio(name: str, client: httpx.AsyncClient, headers: dict) -> dict:
    """
    Fetch the actual Wikipedia extract (bio) for a celebrity.
    Returns dict with bio text and suggested category based on first occupation.
    """
    result = {"bio": None, "suggested_category": None}
    
    try:
        # Search Wikipedia for the page
        search_url = "https://en.wikipedia.org/w/api.php"
        search_params = {
            'action': 'query',
            'list': 'search',
            'srsearch': name,
            'srlimit': 3,
            'format': 'json'
        }
        
        search_response = await client.get(search_url, params=search_params, headers=headers, timeout=10.0)
        if search_response.status_code != 200:
            return result
        
        search_data = search_response.json()
        search_results = search_data.get('query', {}).get('search', [])
        
        if not search_results:
            return result
        
        # Get the page title (prefer exact match)
        page_title = None
        name_lower = name.lower()
        for sr in search_results:
            if sr.get('title', '').lower() == name_lower:
                page_title = sr['title']
                break
        if not page_title:
            page_title = search_results[0]['title']
        
        # Now get the extract for this page
        extract_params = {
            'action': 'query',
            'titles': page_title,
            'prop': 'extracts',
            'exintro': 'true',
            'explaintext': 'true',
            'format': 'json'
        }
        
        extract_response = await client.get(search_url, params=extract_params, headers=headers, timeout=10.0)
        if extract_response.status_code != 200:
            return result
        
        extract_data = extract_response.json()
        pages = extract_data.get('query', {}).get('pages', {})
        
        for page_id, page_info in pages.items():
            if page_id != '-1':
                extract = page_info.get('extract', '')
                if extract:
                    # Get first 2-3 sentences for bio
                    sentences = extract.split('. ')
                    bio = '. '.join(sentences[:3])
                    if not bio.endswith('.'):
                        bio += '.'
                    result['bio'] = bio
                    
                    # Extract category from the first sentence (contains occupation)
                    first_sentence = sentences[0] if sentences else ''
                    result['suggested_category'] = extract_category_from_description(first_sentence)
                    break
        
    except Exception as e:
        logger.warning(f"Error fetching Wikipedia bio for {name}: {e}")
    
    return result


@api_router.post("/admin/fix-celebrity-bios")
async def fix_celebrity_bios_and_categories(batch_size: int = 30, delay_seconds: float = 0.4):
    """
    Fix celebrities with generic "is a celebrity" bios by fetching real Wikipedia extracts.
    Also recategorizes based on the FIRST occupation mentioned (e.g., singer -> musicians).
    """
    headers = {
        'User-Agent': 'CelebrityBuzzIndex/1.0 (https://celebbuzzindex.com; admin@celebbuzzindex.com)',
        'Accept': 'application/json'
    }
    
    # Find celebrities needing bio fix
    celebs_needing_fix = await db.celebrities.find(
        {
            '$or': [
                {'bio': {'$regex': 'is a celebrity', '$options': 'i'}},
                {'bio': {'$exists': False}},
                {'bio': ''}
            ],
            'bio_fixed': {'$ne': True}
        },
        {'_id': 0, 'id': 1, 'name': 1, 'category': 1, 'bio': 1}
    ).limit(batch_size).to_list(batch_size)
    
    if not celebs_needing_fix:
        return {
            "success": True,
            "message": "No celebrities need bio fixing",
            "updated": 0,
            "remaining": 0
        }
    
    # Count remaining
    remaining_count = await db.celebrities.count_documents({
        '$or': [
            {'bio': {'$regex': 'is a celebrity', '$options': 'i'}},
            {'bio': {'$exists': False}},
            {'bio': ''}
        ],
        'bio_fixed': {'$ne': True}
    })
    
    updated = 0
    recategorized = 0
    skipped = 0
    details = []
    
    async with httpx.AsyncClient() as client:
        for celeb in celebs_needing_fix:
            celeb_id = celeb.get('id')
            name = celeb.get('name')
            old_category = celeb.get('category')
            
            try:
                wiki_data = await fetch_wikipedia_bio(name, client, headers)
                
                update_fields = {'bio_fixed': True}
                
                if wiki_data['bio']:
                    update_fields['bio'] = wiki_data['bio']
                    
                    # Update category if we got a suggestion
                    if wiki_data['suggested_category'] and wiki_data['suggested_category'] != old_category:
                        update_fields['category'] = wiki_data['suggested_category']
                        recategorized += 1
                        details.append({
                            "name": name,
                            "old_category": old_category,
                            "new_category": wiki_data['suggested_category'],
                            "bio_preview": wiki_data['bio'][:80] + "..."
                        })
                    
                    await db.celebrities.update_one({'id': celeb_id}, {'$set': update_fields})
                    updated += 1
                    logger.info(f"Fixed bio for {name}: {wiki_data['suggested_category']}")
                else:
                    # Mark as checked even if no bio found
                    await db.celebrities.update_one({'id': celeb_id}, {'$set': update_fields})
                    skipped += 1
                
                await asyncio.sleep(delay_seconds)
                
            except Exception as e:
                logger.error(f"Error fixing bio for {name}: {e}")
    
    return {
        "success": True,
        "message": f"Processed {len(celebs_needing_fix)} celebrities",
        "updated": updated,
        "recategorized": recategorized,
        "skipped": skipped,
        "remaining": remaining_count - len(celebs_needing_fix),
        "details": details[:20]  # Show first 20 changes
    }


@api_router.post("/admin/reclassify-tiers")
async def reclassify_celebrity_tiers(batch_size: int = 50, delay_seconds: float = 0.5):
    """
    Reclassify all celebrity tiers using the new Wikipedia-based metrics system.
    
    Metrics used:
    - Number of Wikipedia language editions (global recognition)
    - Years active (career longevity)
    - Awards mentioned in bio
    - Career indicators (reality TV vs mainstream)
    
    This is a background-safe operation that processes in batches.
    """
    # Get all celebrities that need reclassification
    all_celebs = await db.celebrities.find(
        {},
        {"_id": 0, "id": 1, "name": 1, "tier": 1, "price": 1}
    ).to_list(2000)
    
    if not all_celebs:
        return {"message": "No celebrities to reclassify", "processed": 0}
    
    # Process in background
    processed = 0
    tier_changes = {"A_to_B": 0, "A_to_C": 0, "A_to_D": 0, "B_to_A": 0, "B_to_C": 0, "B_to_D": 0,
                    "C_to_A": 0, "C_to_B": 0, "C_to_D": 0, "D_to_A": 0, "D_to_B": 0, "D_to_C": 0}
    sample_changes = []
    
    headers = {
        "User-Agent": "CelebrityBuzzIndex/1.0 (https://celebrity-buzz-index.com) httpx/0.27"
    }
    
    async with httpx.AsyncClient() as http_client:
        for celeb in all_celebs[:batch_size]:
            celeb_id = celeb.get("id")
            name = celeb.get("name", "")
            old_tier = celeb.get("tier", "D")
            old_price = celeb.get("price", 1.0)
            
            try:
                # Calculate new tier using Wikipedia metrics
                result = await calculate_tier_from_wikipedia_data(name, http_client)
                new_tier = result["tier"]
                new_price = result["price"]
                
                # Track changes
                if old_tier != new_tier:
                    change_key = f"{old_tier}_to_{new_tier}"
                    if change_key in tier_changes:
                        tier_changes[change_key] += 1
                    
                    if len(sample_changes) < 20:
                        sample_changes.append({
                            "name": name,
                            "old_tier": old_tier,
                            "new_tier": new_tier,
                            "old_price": old_price,
                            "new_price": new_price,
                            "score": result["score"],
                            "reasoning": result["reasoning"][:3]
                        })
                
                # Update celebrity
                await db.celebrities.update_one(
                    {"id": celeb_id},
                    {
                        "$set": {
                            "tier": new_tier,
                            "price": new_price,
                            "tier_score": result["score"],
                            "tier_metrics": result["metrics"],
                            "tier_updated_at": datetime.now(timezone.utc).isoformat()
                        }
                    }
                )
                
                processed += 1
                
                # Rate limiting
                await asyncio.sleep(delay_seconds)
                
            except Exception as e:
                logger.error(f"Error reclassifying {name}: {e}")
    
    return {
        "success": True,
        "message": f"Reclassified {processed} celebrities",
        "processed": processed,
        "remaining": len(all_celebs) - batch_size,
        "tier_changes": tier_changes,
        "sample_changes": sample_changes
    }


@api_router.get("/admin/test-tier-calculation/{name}")
async def test_tier_calculation(name: str):
    """
    Test the tier calculation for a specific celebrity.
    Returns detailed metrics and reasoning.
    """
    async with httpx.AsyncClient() as http_client:
        result = await calculate_tier_from_wikipedia_data(name, http_client)
        
        # Also get current DB values for comparison
        celeb = await db.celebrities.find_one(
            {"name": {"$regex": f"^{name}$", "$options": "i"}},
            {"_id": 0, "tier": 1, "price": 1, "category": 1}
        )
        
        return {
            "name": name,
            "current_db_values": celeb or "Not in database",
            "calculated_tier": result["tier"],
            "calculated_price": result["price"],
            "total_score": result["score"],
            "metrics": result["metrics"],
            "reasoning": result["reasoning"]
        }


# Auth routes are now in /routes/auth.py


# Include routers
app.include_router(api_router)
app.include_router(auth_router)

# ==================== SCHEDULED TASKS ====================

# Initialize the scheduler
scheduler = AsyncIOScheduler(timezone="UTC")

async def scheduled_weekly_price_reset():
    """
    Scheduled task to run weekly price reset every Monday at midnight UTC.
    This updates all celebrity prices based on their accumulated buzz scores.
    """
    logger.info("🕐 Starting scheduled weekly price reset...")
    
    try:
        # Get all celebrities
        all_celebs = await db.celebrities.find({}, {"_id": 0}).to_list(2000)
        
        increased = 0
        decreased = 0
        unchanged = 0
        
        for celeb in all_celebs:
            celeb_id = celeb.get("id")
            name = celeb.get("name", "")
            tier = celeb.get("tier", "D")
            buzz_score = celeb.get("buzz_score", 0)
            current_price = celeb.get("price", 5.0)
            
            # Calculate new price based on buzz score
            new_price = get_dynamic_price(tier, buzz_score, name)
            
            # Determine price change
            price_diff = new_price - current_price
            
            if price_diff > 0:
                increased += 1
            elif price_diff < 0:
                decreased += 1
            else:
                unchanged += 1
            
            # Update celebrity in database
            await db.celebrities.update_one(
                {"id": celeb_id},
                {
                    "$set": {
                        "previous_week_price": current_price,
                        "price": new_price,
                        "buzz_score": 0  # Reset buzz score for new week
                    }
                }
            )
            
            # Record price history if there was a change
            if price_diff != 0:
                await record_price_history(celeb_id, name, new_price, tier, buzz_score)
        
        logger.info(f"✅ Weekly price reset complete: {increased} up, {decreased} down, {unchanged} unchanged")
        
        # Store the reset log in database for auditing
        await db.scheduled_tasks.insert_one({
            "task": "weekly_price_reset",
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_celebrities": len(all_celebs),
                "prices_increased": increased,
                "prices_decreased": decreased,
                "prices_unchanged": unchanged
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Weekly price reset failed: {e}")

# Schedule the weekly price reset for every Monday at 00:00 UTC
scheduler.add_job(
    scheduled_weekly_price_reset,
    CronTrigger(day_of_week='mon', hour=0, minute=0),
    id='weekly_price_reset',
    name='Weekly Celebrity Price Reset',
    replace_existing=True
)

# ==================== DAILY POINTS UPDATE ====================
async def scheduled_daily_points_update():
    """
    Scheduled task to update team points daily based on celebrity news coverage.
    Runs every day at 23:00 UTC (before midnight to capture day's news).
    """
    logger.info("🕐 Starting scheduled daily points update...")
    
    try:
        # Get all teams with celebrities
        teams = await db.teams.find(
            {"celebrities": {"$exists": True, "$ne": []}},
            {"_id": 0}
        ).to_list(1000)
        
        updated_teams = 0
        total_points_awarded = 0
        
        for team in teams:
            team_id = team.get("id")
            team_points = 0
            
            for celeb in team.get("celebrities", []):
                celeb_id = celeb.get("celebrity_id")
                
                # Get current celebrity data
                celeb_data = await db.celebrities.find_one(
                    {"id": celeb_id},
                    {"_id": 0, "buzz_score": 1, "news": 1}
                )
                
                if celeb_data:
                    # Points from buzz score
                    buzz_points = celeb_data.get("buzz_score", 0)
                    
                    # Bonus for news coverage (each news article = extra points)
                    news_count = len(celeb_data.get("news", []))
                    news_bonus = news_count * 2  # 2 points per news article
                    
                    team_points += buzz_points + news_bonus
            
            # Update team's total points
            if team_points > 0:
                await db.teams.update_one(
                    {"id": team_id},
                    {"$inc": {"total_points": team_points}}
                )
                updated_teams += 1
                total_points_awarded += team_points
        
        logger.info(f"✅ Daily points update: {updated_teams} teams, {total_points_awarded:.1f} points awarded")
        
        # Log the task
        await db.scheduled_tasks.insert_one({
            "task": "daily_points_update",
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "teams_updated": updated_teams,
                "total_points_awarded": total_points_awarded
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Daily points update failed: {e}")

# Schedule daily points update at 23:00 UTC
scheduler.add_job(
    scheduled_daily_points_update,
    CronTrigger(hour=23, minute=0),
    id='daily_points_update',
    name='Daily Team Points Update',
    replace_existing=True
)

# ==================== WEEKLY LEAGUE SCORING ====================
async def scheduled_weekly_league_scoring():
    """
    Scheduled task to record weekly league scores and award winners.
    Runs every Sunday at 23:59 UTC (end of game week).
    """
    logger.info("🏆 Starting scheduled weekly league scoring...")
    
    try:
        # Get all leagues
        leagues = await db.leagues.find({}, {"_id": 0}).to_list(500)
        
        leagues_processed = 0
        badges_awarded = 0
        
        for league in leagues:
            league_id = league.get("id")
            team_ids = league.get("team_ids", [])
            
            if not team_ids:
                continue
            
            # Get all teams in league
            teams = await db.teams.find(
                {"id": {"$in": team_ids}},
                {"_id": 0}
            ).to_list(100)
            
            if not teams:
                continue
            
            current_week = get_current_week_str()
            current_month = get_current_month_str()
            
            # Record weekly scores
            weekly_scores = {team["id"]: team.get("total_points", 0) for team in teams}
            
            # Find winner
            winner = max(teams, key=lambda t: t.get("total_points", 0))
            winner_entry = {
                "week": current_week,
                "team_id": winner["id"],
                "team_name": winner.get("team_name", "Unknown"),
                "points": winner.get("total_points", 0)
            }
            
            # Update monthly scores (accumulate)
            monthly_scores = league.get("monthly_scores", {})
            for team_id, points in weekly_scores.items():
                monthly_scores[team_id] = monthly_scores.get(team_id, 0) + points
            
            # Update league
            await db.leagues.update_one(
                {"id": league_id},
                {
                    "$set": {
                        "current_week": current_week,
                        "weekly_scores": weekly_scores,
                        "current_month": current_month,
                        "monthly_scores": monthly_scores
                    },
                    "$push": {"weekly_winner_history": winner_entry}
                }
            )
            
            # Award weekly winner badge
            badge = {
                "id": "weekly_winner",
                "earned_at": datetime.now(timezone.utc).isoformat(),
                "league_id": league_id,
                "week": current_week
            }
            
            await db.teams.update_one(
                {"id": winner["id"]},
                {
                    "$push": {"badges": badge},
                    "$inc": {"weekly_wins": 1}
                }
            )
            badges_awarded += 1
            
            # Check for League Legend badge (3+ wins in this league)
            updated_history = league.get("weekly_winner_history", []) + [winner_entry]
            league_wins = sum(1 for w in updated_history if w.get("team_id") == winner["id"])
            
            if league_wins >= 3:
                updated_team = await db.teams.find_one({"id": winner["id"]})
                has_legend = any(
                    b.get("id") == "league_champion" and b.get("league_id") == league_id 
                    for b in updated_team.get("badges", [])
                )
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
                    badges_awarded += 1
            
            leagues_processed += 1
        
        logger.info(f"✅ Weekly league scoring: {leagues_processed} leagues, {badges_awarded} badges awarded")
        
        await db.scheduled_tasks.insert_one({
            "task": "weekly_league_scoring",
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "leagues_processed": leagues_processed,
                "badges_awarded": badges_awarded
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Weekly league scoring failed: {e}")

# Schedule weekly league scoring for Sunday at 23:59 UTC
scheduler.add_job(
    scheduled_weekly_league_scoring,
    CronTrigger(day_of_week='sun', hour=23, minute=59),
    id='weekly_league_scoring',
    name='Weekly League Scoring & Awards',
    replace_existing=True
)

# ==================== MONTHLY LEAGUE WINNER ====================
async def scheduled_monthly_league_winner():
    """
    Scheduled task to record monthly league winners.
    Runs on the 1st of each month at 00:30 UTC.
    """
    logger.info("🌟 Starting scheduled monthly league winner recording...")
    
    try:
        # Get all leagues
        leagues = await db.leagues.find({}, {"_id": 0}).to_list(500)
        
        monthly_winners = 0
        
        for league in leagues:
            league_id = league.get("id")
            monthly_scores = league.get("monthly_scores", {})
            
            if not monthly_scores:
                continue
            
            # Find monthly winner
            winner_id = max(monthly_scores, key=monthly_scores.get)
            winner_team = await db.teams.find_one({"id": winner_id}, {"_id": 0})
            
            if not winner_team:
                continue
            
            # Get previous month
            now = datetime.now(timezone.utc)
            last_month = now.replace(day=1) - timedelta(days=1)
            month_str = f"{last_month.year}-{last_month.month:02d}"
            
            winner_entry = {
                "month": month_str,
                "team_id": winner_id,
                "team_name": winner_team.get("team_name", "Unknown"),
                "points": monthly_scores[winner_id]
            }
            
            # Update league - reset monthly scores
            await db.leagues.update_one(
                {"id": league_id},
                {
                    "$set": {"monthly_scores": {}},
                    "$push": {"monthly_winner_history": winner_entry}
                }
            )
            
            # Award monthly winner badge
            badge = {
                "id": "monthly_winner",
                "earned_at": datetime.now(timezone.utc).isoformat(),
                "league_id": league_id,
                "month": month_str
            }
            
            await db.teams.update_one(
                {"id": winner_id},
                {"$push": {"badges": badge}}
            )
            
            monthly_winners += 1
        
        logger.info(f"✅ Monthly league winners: {monthly_winners} winners crowned")
        
        await db.scheduled_tasks.insert_one({
            "task": "monthly_league_winner",
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "monthly_winners": monthly_winners
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Monthly league winner recording failed: {e}")

# Schedule monthly winner recording for 1st of each month at 00:30 UTC
scheduler.add_job(
    scheduled_monthly_league_winner,
    CronTrigger(day=1, hour=0, minute=30),
    id='monthly_league_winner',
    name='Monthly League Winner Awards',
    replace_existing=True
)

@app.on_event("startup")
async def start_scheduler():
    """Start the scheduler when the app starts"""
    scheduler.start()
    logger.info("📅 Scheduler started - Weekly price reset scheduled for Monday 00:00 UTC")

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
    scheduler.shutdown()
    logger.info("📅 Scheduler stopped")
    client.close()
