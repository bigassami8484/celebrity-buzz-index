"""
Celebrity-related Pydantic models
"""
from pydantic import BaseModel, Field
from typing import List, Optional

class NewsArticle(BaseModel):
    title: str
    summary: str = ""
    source: str = ""
    date: str = ""
    sentiment: str = "neutral"
    is_real: bool = False

class Celebrity(BaseModel):
    id: str = ""
    name: str
    bio: str = ""
    image: str = ""
    category: str = "other"
    wiki_url: str = ""
    buzz_score: float = 0.0
    price: float = 1.0
    previous_week_price: float = 0.0
    tier: str = "D"
    news: List[dict] = []
    page_views: int = 0
    is_deceased: bool = False
    birth_year: int = 0
    age: int = 0
    times_picked: int = 0

class CelebritySearch(BaseModel):
    name: str
