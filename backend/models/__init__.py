"""
Pydantic models for the Celebrity Buzz Index API
"""
from .celebrity import Celebrity, CelebritySearch, NewsArticle
from .team import Team, TeamCreate, TeamCustomize, AddToTeam, TransferRequest
from .league import League, LeagueCreate, LeagueJoin
from .auth import MagicLinkRequest, MagicLinkVerify, GoogleAuthCallback, GuestConvert

__all__ = [
    "Celebrity", "CelebritySearch", "NewsArticle",
    "Team", "TeamCreate", "TeamCustomize", "AddToTeam", "TransferRequest",
    "League", "LeagueCreate", "LeagueJoin",
    "MagicLinkRequest", "MagicLinkVerify", "GoogleAuthCallback", "GuestConvert"
]
