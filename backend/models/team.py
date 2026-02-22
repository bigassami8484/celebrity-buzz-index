"""
Team-related Pydantic models
"""
from pydantic import BaseModel, Field
from typing import List, Optional

class TeamCreate(BaseModel):
    name: str = "My Dream Team"
    user_id: Optional[str] = None

class TeamCustomize(BaseModel):
    team_id: str
    emoji: str = ""
    color: str = ""

class AddToTeam(BaseModel):
    team_id: str
    celebrity_id: str

class TransferRequest(BaseModel):
    team_id: str
    out_celebrity_id: str
    in_celebrity_id: str

class Team(BaseModel):
    id: str = ""
    name: str = "My Dream Team"
    user_id: Optional[str] = None
    celebrities: List[dict] = []
    budget: float = 50.0
    total_points: int = 0
    weekly_points: int = 0
    emoji: str = "⭐"
    color: str = "#FF0099"
    transfers_remaining: int = 2
