"""
Team Services - Business logic for team operations.
Contains functions for creating, managing, and updating teams.
"""
import logging
import uuid
from typing import List, Optional
from datetime import datetime, timezone

from config.database import db
from data.constants import STARTING_BUDGET, MAX_TEAM_SIZE, BANNED_WORDS

logger = logging.getLogger(__name__)


def contains_banned_words(text: str) -> bool:
    """Check if text contains any banned words."""
    text_lower = text.lower()
    for word in BANNED_WORDS:
        if word in text_lower:
            return True
    return False


def get_week_number() -> str:
    """Get the current week number string."""
    now = datetime.now(timezone.utc)
    return f"{now.year}-W{now.isocalendar()[1]:02d}"


def get_monday_reset_week() -> str:
    """Get the week string based on Monday resets."""
    now = datetime.now(timezone.utc)
    return f"{now.year}-W{now.isocalendar()[1]:02d}"


async def create_team(team_name: str, user_id: Optional[str] = None) -> dict:
    """
    Create a new team.
    
    Args:
        team_name: Name for the team
        user_id: Optional user ID to link the team to
        
    Returns:
        The created team document
    """
    if contains_banned_words(team_name):
        raise ValueError("Team name contains inappropriate language")
    
    team_id = str(uuid.uuid4())
    current_week = get_monday_reset_week()
    
    team = {
        "id": team_id,
        "team_name": team_name,
        "team_color": "pink",
        "team_icon": "star",
        "budget_remaining": STARTING_BUDGET,
        "total_points": 0.0,
        "weekly_points": 0.0,
        "brown_bread_bonus": 0.0,
        "celebrities": [],
        "transfers_this_week": 0,
        "last_transfer_reset": get_week_number(),
        "points_week": current_week,
        "badges": [],
        "weekly_wins": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_guest": user_id is None,
        "owner_user_id": user_id
    }
    
    await db.teams.insert_one(team)
    # Remove MongoDB's _id before returning
    if '_id' in team:
        del team['_id']
    
    return team


async def get_team_by_id(team_id: str) -> Optional[dict]:
    """Get a team by its ID."""
    return await db.teams.find_one({"id": team_id}, {"_id": 0})


async def get_team_by_user_id(user_id: str) -> Optional[dict]:
    """Get a team by the owner's user ID."""
    return await db.teams.find_one({"owner_user_id": user_id}, {"_id": 0})


async def add_celebrity_to_team(team_id: str, celebrity: dict) -> dict:
    """
    Add a celebrity to a team.
    
    Args:
        team_id: The team's ID
        celebrity: The celebrity document to add
        
    Returns:
        The updated team document
        
    Raises:
        ValueError: If team is full or can't afford the celebrity
    """
    team = await get_team_by_id(team_id)
    if not team:
        raise ValueError("Team not found")
    
    # Check team size
    if len(team.get("celebrities", [])) >= MAX_TEAM_SIZE:
        raise ValueError("Team is full (max 10 celebrities)")
    
    # Check budget
    price = celebrity.get("price", 0)
    if team.get("budget_remaining", 0) < price:
        raise ValueError(f"Not enough budget. Need £{price}M, have £{team['budget_remaining']}M")
    
    # Check if celebrity already in team
    celeb_id = celebrity.get("id")
    for c in team.get("celebrities", []):
        if c.get("celebrity_id") == celeb_id:
            raise ValueError("Celebrity already in team")
    
    # Create team celebrity entry
    team_celeb = {
        "celebrity_id": celeb_id,
        "name": celebrity.get("name"),
        "image": celebrity.get("image", ""),
        "category": celebrity.get("category", ""),
        "price": price,
        "buzz_score": celebrity.get("buzz_score", 0),
        "tier": celebrity.get("tier", "D"),
        "previous_week_price": celebrity.get("previous_week_price", 0),
        "is_deceased": celebrity.get("is_deceased", False),
        "added_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Update team
    new_budget = team["budget_remaining"] - price
    
    await db.teams.update_one(
        {"id": team_id},
        {
            "$push": {"celebrities": team_celeb},
            "$set": {"budget_remaining": new_budget}
        }
    )
    
    return await get_team_by_id(team_id)


async def remove_celebrity_from_team(team_id: str, celebrity_id: str) -> dict:
    """
    Remove a celebrity from a team.
    
    Returns:
        The updated team document
    """
    team = await get_team_by_id(team_id)
    if not team:
        raise ValueError("Team not found")
    
    # Find the celebrity to remove
    celeb_to_remove = None
    for c in team.get("celebrities", []):
        if c.get("celebrity_id") == celebrity_id:
            celeb_to_remove = c
            break
    
    if not celeb_to_remove:
        raise ValueError("Celebrity not in team")
    
    # Refund the price
    refund = celeb_to_remove.get("price", 0)
    new_budget = team["budget_remaining"] + refund
    
    # Update team
    await db.teams.update_one(
        {"id": team_id},
        {
            "$pull": {"celebrities": {"celebrity_id": celebrity_id}},
            "$set": {"budget_remaining": new_budget}
        }
    )
    
    return await get_team_by_id(team_id)


async def get_leaderboard(limit: int = 50) -> List[dict]:
    """Get the team leaderboard sorted by total points."""
    pipeline = [
        {"$match": {"celebrities": {"$exists": True, "$ne": []}}},
        {"$sort": {"total_points": -1}},
        {"$limit": limit},
        {"$project": {
            "_id": 0,
            "id": 1,
            "team_name": 1,
            "team_icon": 1,
            "team_color": 1,
            "total_points": 1,
            "celebrity_count": {"$size": "$celebrities"}
        }}
    ]
    
    results = []
    async for doc in db.teams.aggregate(pipeline):
        results.append(doc)
    return results


async def customize_team(
    team_id: str,
    team_name: Optional[str] = None,
    team_color: Optional[str] = None,
    team_icon: Optional[str] = None
) -> dict:
    """Customize team name, color, and icon."""
    team = await get_team_by_id(team_id)
    if not team:
        raise ValueError("Team not found")
    
    update = {}
    
    if team_name:
        if contains_banned_words(team_name):
            raise ValueError("Team name contains inappropriate language")
        update["team_name"] = team_name
    
    if team_color:
        update["team_color"] = team_color
    
    if team_icon:
        update["team_icon"] = team_icon
    
    if update:
        await db.teams.update_one({"id": team_id}, {"$set": update})
    
    return await get_team_by_id(team_id)
