"""
League-related Pydantic models
"""
from pydantic import BaseModel
from typing import List, Optional

class LeagueCreate(BaseModel):
    name: str
    team_id: str

class LeagueJoin(BaseModel):
    code: str
    team_id: str

class League(BaseModel):
    id: str = ""
    name: str
    code: str = ""
    creator_team_id: str = ""
    members: List[str] = []
