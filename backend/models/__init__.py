"""Pydantic models for the Celebrity Buzz Index API"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

# ==================== USER MODELS ====================

class MagicLinkRequest(BaseModel):
    email: str

class MagicLinkVerify(BaseModel):
    token: str

class GuestConvert(BaseModel):
    guest_team_id: str

class SessionExchange(BaseModel):
    session_id: str

# ==================== TEAM MODELS ====================

class TeamCreate(BaseModel):
    team_name: str = "My Buzz Team"

class AddToTeam(BaseModel):
    team_id: str
    celebrity_id: str

class TeamCustomize(BaseModel):
    team_id: str
    team_name: Optional[str] = None
    team_color: Optional[str] = None
    team_icon: Optional[str] = None

class TeamCelebrity(BaseModel):
    celebrity_id: str
    name: str
    image: str
    category: str
    price: float
    buzz_score: float
    tier: str = "D"
    added_at: str = ""

class UserTeam(BaseModel):
    id: str = ""
    team_name: str = "My Buzz Team"
    budget_remaining: float = 50.0
    total_points: float = 0.0
    brown_bread_bonus: float = 0.0
    celebrities: List[TeamCelebrity] = []
    badges: List[dict] = []
    weekly_wins: int = 0
    created_at: datetime = None
    team_color: str = "pink"
    team_icon: str = "star"
    owner_user_id: Optional[str] = None
    is_guest: bool = True
    transfers_this_week: int = 0
    last_transfer_reset: str = ""
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.id:
            self.id = f"team_{uuid.uuid4().hex[:12]}"
        if not self.created_at:
            from datetime import timezone
            self.created_at = datetime.now(timezone.utc)

class TransferRequest(BaseModel):
    team_id: str
    sell_celebrity_id: str
    buy_celebrity_id: str

# ==================== LEAGUE MODELS ====================

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
    owner_team_id: str
    team_ids: List[str] = []
    max_teams: int = 20
    created_at: datetime = None
    
    def __init__(self, **data):
        import random
        import string
        from datetime import timezone
        super().__init__(**data)
        if not self.id:
            self.id = f"league_{uuid.uuid4().hex[:8]}"
        if not self.code:
            self.code = ''.join(random.choices(string.ascii_uppercase, k=6))
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc)

# ==================== CELEBRITY MODELS ====================

class CelebritySearch(BaseModel):
    name: str

class Celebrity(BaseModel):
    id: str = ""
    name: str
    bio: str = ""
    image: str = ""
    category: str = "other"
    tier: str = "D"
    price: float = 1.0
    buzz_score: float = 10.0
    news: List[dict] = []
    wiki_url: str = ""
    is_deceased: bool = False
    age: Optional[int] = None
    times_picked: int = 0
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.id:
            self.id = f"celeb_{uuid.uuid4().hex[:12]}"

# ==================== PRICE HISTORY MODELS ====================

class PriceHistoryEntry(BaseModel):
    celebrity_id: str
    celebrity_name: str
    price: float
    tier: str
    buzz_score: float
    recorded_at: str
