"""
Celebrity Services - Business logic for celebrity operations.
Contains functions for searching, fetching, and managing celebrity data.
"""
import logging
import re
import httpx
from typing import List, Optional
from datetime import datetime, timezone

from config.database import db
from data import CELEBRITY_ALIASES
from utils.helpers import normalize_text

logger = logging.getLogger(__name__)


async def get_celebrity_by_id(celebrity_id: str) -> Optional[dict]:
    """Get a celebrity by their ID."""
    return await db.celebrities.find_one({"id": celebrity_id}, {"_id": 0})


async def get_celebrity_by_name(name: str) -> Optional[dict]:
    """Get a celebrity by their name (case-insensitive)."""
    return await db.celebrities.find_one(
        {"name": {"$regex": f"^{re.escape(name.strip())}$", "$options": "i"}},
        {"_id": 0}
    )


async def get_celebrities_by_category(category: str, limit: int = 8) -> List[dict]:
    """
    Get random celebrities from a specific category.
    Returns a random sample of celebrities from the specified category.
    """
    pipeline = [
        {"$match": {"category": category}},
        {"$sample": {"size": limit}},
        {"$project": {"_id": 0}}
    ]
    results = []
    async for doc in db.celebrities.aggregate(pipeline):
        results.append(doc)
    return results


async def search_celebrity_in_db(query: str) -> Optional[dict]:
    """
    Search for a celebrity in the database.
    Supports exact matches and alias lookups.
    """
    query_lower = query.lower().strip()
    
    # Check for known aliases first
    canonical_name = CELEBRITY_ALIASES.get(query_lower)
    search_name = canonical_name if canonical_name else query.strip()
    
    # Try exact match (case-insensitive)
    celeb = await db.celebrities.find_one(
        {"name": {"$regex": f"^{re.escape(search_name)}$", "$options": "i"}},
        {"_id": 0}
    )
    
    if celeb:
        return celeb
    
    # Try prefix match
    celeb = await db.celebrities.find_one(
        {"name": {"$regex": f"^{re.escape(search_name)}( |$)", "$options": "i"}},
        {"_id": 0}
    )
    
    return celeb


async def get_top_picked_celebrities(limit: int = 10) -> List[dict]:
    """Get the most frequently picked celebrities."""
    pipeline = [
        {"$match": {"times_picked": {"$gt": 0}}},
        {"$sort": {"times_picked": -1}},
        {"$limit": limit},
        {"$project": {"_id": 0, "name": 1, "image": 1, "tier": 1, "price": 1, "times_picked": 1}}
    ]
    results = []
    async for doc in db.celebrities.aggregate(pipeline):
        results.append(doc)
    return results


async def get_brown_bread_watch(limit: int = 10) -> List[dict]:
    """
    Get elderly celebrities for the "Brown Bread Watch" feature.
    Returns celebrities sorted by age (oldest first).
    """
    pipeline = [
        {"$match": {
            "is_deceased": False,
            "age": {"$gte": 70}
        }},
        {"$sort": {"age": -1}},
        {"$limit": limit},
        {"$project": {"_id": 0}}
    ]
    results = []
    async for doc in db.celebrities.aggregate(pipeline):
        # Calculate risk level based on age
        age = doc.get("age", 0)
        if age >= 90:
            risk_level = "critical"
        elif age >= 85:
            risk_level = "high"
        elif age >= 80:
            risk_level = "elevated"
        else:
            risk_level = "moderate"
        
        doc["risk_level"] = risk_level
        doc["is_premium"] = age >= 85
        results.append(doc)
    
    return results


async def update_celebrity(celebrity_id: str, update_data: dict) -> bool:
    """Update a celebrity's data."""
    result = await db.celebrities.update_one(
        {"id": celebrity_id},
        {"$set": update_data}
    )
    return result.modified_count > 0


async def increment_times_picked(celebrity_id: str) -> None:
    """Increment the times_picked counter for a celebrity."""
    await db.celebrities.update_one(
        {"id": celebrity_id},
        {"$inc": {"times_picked": 1}}
    )


async def get_all_categories() -> List[dict]:
    """Get all celebrity categories with counts."""
    pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$project": {"category": "$_id", "count": 1, "_id": 0}},
        {"$sort": {"count": -1}}
    ]
    results = []
    async for doc in db.celebrities.aggregate(pipeline):
        if doc.get("category"):
            results.append(doc)
    return results


async def record_price_history(
    celebrity_id: str,
    celebrity_name: str,
    price: float,
    tier: str,
    buzz_score: float
) -> None:
    """Record a price history entry for a celebrity."""
    entry = {
        "celebrity_id": celebrity_id,
        "celebrity_name": celebrity_name,
        "price": price,
        "tier": tier,
        "buzz_score": buzz_score,
        "recorded_at": datetime.now(timezone.utc).isoformat()
    }
    await db.price_history.insert_one(entry)


async def get_price_history(celebrity_id: str, limit: int = 30) -> List[dict]:
    """Get price history for a celebrity."""
    cursor = db.price_history.find(
        {"celebrity_id": celebrity_id},
        {"_id": 0}
    ).sort("recorded_at", -1).limit(limit)
    
    results = []
    async for doc in cursor:
        results.append(doc)
    return results
