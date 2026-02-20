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
from datetime import datetime, timezone
import httpx
import json
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
    news: List[dict] = []
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

class UserTeam(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    team_name: str = "My Team"
    budget_remaining: int = 50
    total_points: float = 0.0
    celebrities: List[TeamCelebrity] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TeamCreate(BaseModel):
    team_name: str = "My Team"

class AddToTeam(BaseModel):
    team_id: str
    celebrity_id: str

class LeaderboardEntry(BaseModel):
    team_id: str
    team_name: str
    total_points: float
    celebrity_count: int

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

# ==================== HELPER FUNCTIONS ====================

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
                return {
                    "name": data.get("title", name),
                    "bio": bio,
                    "image": data.get("thumbnail", {}).get("source", ""),
                    "wiki_url": data.get("content_urls", {}).get("desktop", {}).get("page", "")
                }
            else:
                logger.error(f"Wikipedia returned status {response.status_code}: {response.text[:200]}")
    except Exception as e:
        logger.error(f"Wikipedia fetch error for {name}: {type(e).__name__}: {e}")
    return {"name": name, "bio": "Celebrity profile", "image": "", "wiki_url": ""}

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
        
        # Sentiment modifier
        if sentiment == "positive":
            score += 0.5
        elif sentiment == "negative":
            score += 1.0  # Controversy = more buzz
    
    return round(min(score, 100.0), 1)

def calculate_price(buzz_score: float) -> int:
    """Calculate celebrity price based on buzz score"""
    if buzz_score >= 50:
        return 15
    elif buzz_score >= 35:
        return 12
    elif buzz_score >= 25:
        return 10
    elif buzz_score >= 15:
        return 7
    else:
        return 5

# ==================== API ROUTES ====================

@api_router.get("/")
async def root():
    return {"message": "Celebrity Buzz Index API", "version": "1.0"}

@api_router.get("/categories")
async def get_categories():
    """Get all celebrity categories"""
    return {"categories": CATEGORIES}

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
    
    # Generate news
    news = await generate_celebrity_news(wiki_info["name"], category)
    
    # Calculate buzz score
    buzz_score = calculate_buzz_score(news)
    price = calculate_price(buzz_score)
    
    # Create celebrity object
    celebrity = Celebrity(
        name=wiki_info["name"],
        bio=wiki_info["bio"][:500] if wiki_info["bio"] else "No biography available.",
        image=wiki_info["image"] or f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}&size=400&background=FF0099&color=fff",
        category=category,
        wiki_url=wiki_info["wiki_url"],
        buzz_score=buzz_score,
        price=price,
        news=news
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

@api_router.post("/team/create")
async def create_team(team_data: TeamCreate):
    """Create a new team"""
    team = UserTeam(team_name=team_data.team_name)
    doc = team.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.teams.insert_one(doc)
    if '_id' in doc:
        del doc['_id']
    return {"team": doc}

@api_router.get("/team/{team_id}")
async def get_team(team_id: str):
    """Get team by ID"""
    team = await db.teams.find_one({"id": team_id}, {"_id": 0})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
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
    
    # Add to team
    team_celeb = TeamCelebrity(
        celebrity_id=celebrity["id"],
        name=celebrity["name"],
        image=celebrity["image"],
        category=celebrity["category"],
        price=price,
        buzz_score=celebrity["buzz_score"]
    )
    
    new_budget = team.get("budget_remaining", 50) - price
    new_points = team.get("total_points", 0) + celebrity["buzz_score"]
    
    await db.teams.update_one(
        {"id": data.team_id},
        {
            "$push": {"celebrities": team_celeb.model_dump()},
            "$set": {
                "budget_remaining": new_budget,
                "total_points": new_points
            }
        }
    )
    
    updated_team = await db.teams.find_one({"id": data.team_id}, {"_id": 0})
    return {"team": updated_team}

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
            "celebrity_count": len(team.get("celebrities", []))
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
