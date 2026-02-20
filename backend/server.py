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
from emergentintegrations.llm.chat import LlmChat, UserMessage

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

class UserTeam(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    team_name: str = "My Team"
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
        async with httpx.AsyncClient() as client:
            # Use Wikipedia search API for better results with descriptions
            url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&srlimit=20&format=json"
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
                    "jean", "is paris", "this is", "agreement", "métro", "metro"
                ]
                
                results = []
                seen_base_names = set()
                
                for item in search_results:
                    title = item.get("title", "")
                    snippet = item.get("snippet", "").lower()
                    title_lower = title.lower()
                    
                    # Skip if title contains non-person keywords
                    if any(kw in title_lower for kw in non_person_title_keywords):
                        continue
                    
                    # Skip if title has parentheses UNLESS it's a role descriptor like (musician), (actor)
                    if "(" in title:
                        # Allow if parentheses contain role descriptors
                        paren_content = title.split("(")[1].split(")")[0].lower() if ")" in title else ""
                        allowed_roles = ["musician", "actor", "actress", "singer", "rapper", "footballer",
                                        "politician", "presenter", "comedian", "director", "writer",
                                        "athlete", "businessman", "model", "chef", "host", "dancer"]
                        if not any(role in paren_content for role in allowed_roles):
                            continue
                    
                    # Skip titles with colons (usually shows, specials, etc.)
                    if ":" in title:
                        continue
                    
                    # Skip titles starting with "The" (usually shows, bands, etc.)
                    if title_lower.startswith("the "):
                        continue
                    
                    # Skip if same word repeated (like "Paris Paris", "Simon Simon")
                    words = title.split()
                    if len(words) >= 2 and words[0].lower() == words[1].lower():
                        continue
                    
                    # Skip single word or too many words
                    if len(words) < 1 or len(words) > 4:
                        continue
                    
                    # Allow single-word names if they have accents (like Beyoncé, Rihanna)
                    # For multi-word names, check capitalization
                    if len(words) > 1:
                        # Name should look like a proper name (each word capitalized)
                        if not all(word[0].isupper() for word in words if word and word[0].isalpha()):
                            continue
                    
                    # Check for duplicates - use first two words as base name
                    words = title.split()
                    base_name = " ".join(words[:2]).lower() if len(words) >= 2 else title.lower()
                    if base_name in seen_base_names:
                        continue
                    seen_base_names.add(base_name)
                    
                    # Get full page summary for this person
                    try:
                        summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}"
                        summary_response = await client.get(summary_url, timeout=3.0, headers=headers)
                        if summary_response.status_code == 200:
                            summary_data = summary_response.json()
                            desc = summary_data.get("extract", "")
                            image = summary_data.get("thumbnail", {}).get("source", "")
                            page_type = summary_data.get("type", "")
                            
                            # Skip if not a standard article (could be disambiguation)
                            if page_type != "standard":
                                continue
                            
                            # Check description for person keywords
                            desc_lower = desc.lower()
                            
                            # Skip if description STARTS with non-person phrases (albums, films, etc.)
                            skip_start_phrases = [
                                "is a fictional character", "is a character in",
                                "is an album", "is the album", "is a studio album",
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
                                "was a television", "was a film", "was a band"
                            ]
                            
                            # Check if description starts with any skip phrase
                            should_skip = False
                            for phrase in skip_start_phrases:
                                if desc_lower.startswith(phrase) or f" {phrase}" in desc_lower[:100]:
                                    should_skip = True
                                    break
                            if should_skip:
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
                    except:
                        continue
                        
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

def get_price_for_tier(tier: str) -> int:
    """Get price based on celebrity tier"""
    prices = {
        "A": 18,  # £18M for A-list
        "B": 12,  # £12M for B-list
        "C": 7,   # £7M for C-list
        "D": 3    # £3M for D-list
    }
    return prices.get(tier, 5)

async def calculate_celebrity_tier(bio: str, name: str) -> tuple:
    """Calculate celebrity tier based on bio content and return (tier, price)"""
    bio_lower = bio.lower()
    
    # A-list: Major awards, billions in earnings, legendary status
    a_list_score = sum(1 for ind in A_LIST_INDICATORS if ind in bio_lower)
    if a_list_score >= 2:
        return ("A", 18)
    
    # B-list: Award-winning, millions, chart-topping
    b_list_score = sum(1 for ind in B_LIST_INDICATORS if ind in bio_lower)
    if a_list_score >= 1 or b_list_score >= 2:
        return ("B", 12)
    
    # C-list: Known for appearances, contestants
    c_list_score = sum(1 for ind in C_LIST_INDICATORS if ind in bio_lower)
    if b_list_score >= 1 or c_list_score >= 1:
        return ("C", 7)
    
    # D-list: Everyone else
    return ("D", 3)

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

def calculate_price(buzz_score: float, tier: str, name: str = "") -> int:
    """Calculate celebrity price based on buzz score, tier, and controversy"""
    base_price = get_price_for_tier(tier)
    
    # Controversial celeb boost
    controversy_boost = get_controversial_price_boost(name)
    if controversy_boost > 0:
        base_price = max(base_price, controversy_boost)
    
    # Buzz modifier: high buzz adds to price
    if buzz_score >= 40:
        return base_price + 4
    elif buzz_score >= 30:
        return base_price + 2
    elif buzz_score >= 20:
        return base_price + 1
    return base_price

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
    """Get trending celebrities across all categories"""
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
    """Get site statistics including player count"""
    team_count = await db.teams.count_documents({})
    celeb_count = await db.celebrities.count_documents({})
    
    return {
        "player_count": team_count,
        "celebrity_count": celeb_count,
        "transfer_window": get_week_number()
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
    """Get elderly celebrities for Brown Bread Watch - strategic picks for the bonus!"""
    # Find living celebrities with known age >= 60
    elderly_celebs = await db.celebrities.find(
        {
            "is_deceased": False,
            "age": {"$gte": 60}
        },
        {"_id": 0}
    ).sort("age", -1).to_list(20)
    
    # Add risk level to each
    watch_list = []
    for celeb in elderly_celebs:
        age = celeb.get("age", 0)
        risk = get_brown_bread_risk(age)
        watch_list.append({
            **celeb,
            "risk_level": risk
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
    
    # News sources with RSS feeds - UK and US publications
    rss_sources = [
        ("https://www.dailymail.co.uk/tvshowbiz/index.rss", "Daily Mail"),
        ("https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml", "BBC News"),
        ("https://www.theguardian.com/lifeandstyle/celebrities/rss", "The Guardian"),
        ("https://www.tmz.com/rss.xml", "TMZ"),
        ("https://people.com/feed/", "People"),
        ("https://eonline.com/syndication/feeds/rssfeeds/topstories.xml", "E! News"),
        ("https://www.usmagazine.com/feed/", "US Weekly"),
        ("https://pagesix.com/feed/", "Page Six"),
    ]
    
    try:
        async with httpx.AsyncClient() as client:
            for rss_url, source_name in rss_sources:
                try:
                    response = await client.get(rss_url, timeout=10.0, headers=headers)
                    if response.status_code == 200:
                        # Parse RSS (simple parsing)
                        content = response.text
                        # Extract items using simple string parsing
                        items = content.split("<item>")[1:6]  # Get first 5 items
                        
                        for item in items:
                            try:
                                # Extract title
                                title_start = item.find("<title>") + 7
                                title_end = item.find("</title>")
                                title = item[title_start:title_end].replace("<![CDATA[", "").replace("]]>", "").strip()
                                
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
                                import re
                                description = re.sub(r'<[^>]+>', '', description)[:200]
                                
                                if title and len(title) > 10:
                                    # Try to extract celebrity name from title
                                    celebrity = title.split(":")[0] if ":" in title else title.split(" - ")[0] if " - " in title else "Celebrity"
                                    celebrity = celebrity[:50]
                                    
                                    news_items.append({
                                        "celebrity": celebrity,
                                        "headline": title[:150],
                                        "summary": description[:200] if description else title,
                                        "source": source_name,
                                        "url": link,
                                        "category": "other"
                                    })
                            except Exception as e:
                                logger.error(f"Error parsing RSS item: {e}")
                                continue
                except Exception as e:
                    logger.error(f"Error fetching RSS from {source_name}: {e}")
                    continue
        
        # Limit to 8 items
        news_items = news_items[:8]
        
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
    team = await db.teams.find_one({"id": data.team_id})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    celebrity = await db.celebrities.find_one({"id": data.celebrity_id})
    if not celebrity:
        raise HTTPException(status_code=404, detail="Celebrity not found")
    
    # Check if already in team
    for c in team.get("celebrities", []):
        if c["celebrity_id"] == data.celebrity_id:
            raise HTTPException(status_code=400, detail="Celebrity already in team")
    
    # Check budget
    price = celebrity.get("price", 5)
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
        leaderboard.append({
            "team_id": team["id"],
            "team_name": team.get("team_name", "Unknown"),
            "total_points": team.get("total_points", 0),
            "celebrity_count": len(team.get("celebrities", [])),
            "brown_bread_bonus": team.get("brown_bread_bonus", 0)
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

@api_router.get("/league/{league_id}")
async def get_league(league_id: str):
    """Get league details"""
    league = await db.leagues.find_one({"id": league_id}, {"_id": 0})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    return {"league": league}

@api_router.get("/league/code/{code}")
async def get_league_by_code(code: str):
    """Get league by invite code"""
    league = await db.leagues.find_one({"code": code.upper()}, {"_id": 0})
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

# ==================== BROWN BREAD MINI GAME ENDPOINTS ====================

@api_router.post("/minigame/bet")
async def place_brown_bread_bet(data: PlaceBet):
    """Place a bet on which celebrity will 'go brown bread' next"""
    # Verify team exists
    team = await db.teams.find_one({"id": data.team_id})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Verify celebrity exists and is on the watch list (elderly, alive)
    celebrity = await db.celebrities.find_one({"id": data.celebrity_id})
    if not celebrity:
        raise HTTPException(status_code=404, detail="Celebrity not found")
    
    if celebrity.get("is_deceased"):
        raise HTTPException(status_code=400, detail="Can't bet on someone already brown bread!")
    
    if celebrity.get("age", 0) < 60:
        raise HTTPException(status_code=400, detail="Celebrity must be on the Brown Bread Watch (60+)")
    
    # Check if already has an active bet on this celeb
    existing_bet = await db.bets.find_one({
        "team_id": data.team_id,
        "celebrity_id": data.celebrity_id,
        "resolved": False
    })
    if existing_bet:
        raise HTTPException(status_code=400, detail="Already have an active bet on this celebrity!")
    
    # Check bet amount (min 5, max 50)
    bet_amount = max(5, min(50, data.bet_amount))
    
    # Create bet
    bet = BrownBreadBet(
        team_id=data.team_id,
        celebrity_id=data.celebrity_id,
        celebrity_name=celebrity["name"],
        bet_amount=bet_amount
    )
    
    doc = bet.model_dump()
    doc['placed_at'] = doc['placed_at'].isoformat()
    await db.bets.insert_one(doc)
    
    if '_id' in doc:
        del doc['_id']
    
    return {"bet": doc, "message": f"Bet placed on {celebrity['name']}! 💀"}

@api_router.get("/minigame/bets/{team_id}")
async def get_team_bets(team_id: str):
    """Get all bets for a team"""
    bets = await db.bets.find(
        {"team_id": team_id},
        {"_id": 0}
    ).sort("placed_at", -1).to_list(50)
    
    return {"bets": bets}

@api_router.get("/minigame/leaderboard")
async def get_minigame_leaderboard():
    """Get leaderboard for the brown bread mini game"""
    # Aggregate wins by team
    pipeline = [
        {"$match": {"resolved": True, "won": True}},
        {"$group": {
            "_id": "$team_id",
            "wins": {"$sum": 1},
            "total_winnings": {"$sum": {"$multiply": ["$bet_amount", 10]}}  # 10x payout
        }},
        {"$sort": {"wins": -1}},
        {"$limit": 20}
    ]
    
    results = await db.bets.aggregate(pipeline).to_list(20)
    
    # Get team names
    leaderboard = []
    for result in results:
        team = await db.teams.find_one({"id": result["_id"]}, {"_id": 0, "team_name": 1})
        if team:
            leaderboard.append({
                "team_id": result["_id"],
                "team_name": team.get("team_name", "Unknown"),
                "wins": result["wins"],
                "total_winnings": result["total_winnings"]
            })
    
    return {"leaderboard": leaderboard}

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
