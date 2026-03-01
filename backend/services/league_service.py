"""
League Services - Business logic for league operations.
Contains functions for creating, joining, and managing private leagues.
"""
import logging
import random
import string
from typing import List, Optional
from datetime import datetime, timezone

from config.database import db

logger = logging.getLogger(__name__)


def generate_league_code() -> str:
    """Generate a unique 6-character league code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


async def create_league(name: str, creator_team_id: str) -> dict:
    """
    Create a new private league.
    
    Args:
        name: Name for the league
        creator_team_id: Team ID of the league creator
        
    Returns:
        The created league document
    """
    import uuid
    
    league_id = str(uuid.uuid4())
    code = generate_league_code()
    
    # Ensure code is unique
    while await db.leagues.find_one({"code": code}):
        code = generate_league_code()
    
    league = {
        "id": league_id,
        "name": name,
        "code": code,
        "creator_team_id": creator_team_id,
        "member_team_ids": [creator_team_id],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_active": True
    }
    
    await db.leagues.insert_one(league)
    if '_id' in league:
        del league['_id']
    
    return league


async def get_league_by_id(league_id: str) -> Optional[dict]:
    """Get a league by its ID."""
    return await db.leagues.find_one({"id": league_id}, {"_id": 0})


async def get_league_by_code(code: str) -> Optional[dict]:
    """Get a league by its invite code."""
    return await db.leagues.find_one({"code": code.upper()}, {"_id": 0})


async def join_league(code: str, team_id: str) -> dict:
    """
    Join a league with an invite code.
    
    Args:
        code: The league's invite code
        team_id: The team joining the league
        
    Returns:
        The updated league document
        
    Raises:
        ValueError: If code is invalid or team already a member
    """
    league = await get_league_by_code(code)
    if not league:
        raise ValueError("Invalid league code")
    
    if team_id in league.get("member_team_ids", []):
        raise ValueError("Already a member of this league")
    
    await db.leagues.update_one(
        {"id": league["id"]},
        {"$push": {"member_team_ids": team_id}}
    )
    
    return await get_league_by_id(league["id"])


async def leave_league(league_id: str, team_id: str) -> bool:
    """
    Leave a league.
    
    Returns:
        True if successfully left, False otherwise
    """
    league = await get_league_by_id(league_id)
    if not league:
        raise ValueError("League not found")
    
    if team_id not in league.get("member_team_ids", []):
        raise ValueError("Not a member of this league")
    
    await db.leagues.update_one(
        {"id": league_id},
        {"$pull": {"member_team_ids": team_id}}
    )
    
    return True


async def get_team_leagues(team_id: str) -> List[dict]:
    """Get all leagues a team is a member of."""
    cursor = db.leagues.find(
        {"member_team_ids": team_id},
        {"_id": 0}
    )
    
    results = []
    async for doc in cursor:
        results.append(doc)
    return results


async def get_league_leaderboard(league_id: str) -> List[dict]:
    """Get the leaderboard for a specific league."""
    league = await get_league_by_id(league_id)
    if not league:
        raise ValueError("League not found")
    
    member_ids = league.get("member_team_ids", [])
    
    pipeline = [
        {"$match": {"id": {"$in": member_ids}}},
        {"$sort": {"total_points": -1}},
        {"$project": {
            "_id": 0,
            "id": 1,
            "team_name": 1,
            "team_icon": 1,
            "team_color": 1,
            "total_points": 1,
            "weekly_points": 1,
            "celebrity_count": {"$size": "$celebrities"}
        }}
    ]
    
    results = []
    async for doc in db.teams.aggregate(pipeline):
        results.append(doc)
    return results
