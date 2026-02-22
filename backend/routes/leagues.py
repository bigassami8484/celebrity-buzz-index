"""
League Routes

This file provides a template for league routes that can be migrated from server.py.

Current league endpoints in server.py:
- POST /api/league/create - Create a private league
- POST /api/league/join - Join a league with code
- GET /api/league/{league_id} - Get league details
- GET /api/league/{league_id}/leaderboard - Get league leaderboard
- POST /api/league/{league_id}/leave - Leave a league
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional

# from config import db
# from models.league import LeagueCreate, LeagueJoin

league_router = APIRouter(prefix="/api", tags=["leagues"])

# Template for route migration:
#
# @league_router.post("/league/create")
# async def create_league(data: LeagueCreate):
#     """Create a private league"""
#     pass
