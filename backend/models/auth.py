"""
Authentication-related Pydantic models.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime, timezone


class User(BaseModel):
    """User model"""
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    is_guest: bool = False
    guest_team_id: Optional[str] = None
    google_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserSession(BaseModel):
    """User session model"""
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MagicLinkRequest(BaseModel):
    """Request model for sending magic link"""
    email: EmailStr


class MagicLinkVerify(BaseModel):
    """Request model for verifying magic link"""
    token: str


class GuestConvert(BaseModel):
    """Request model for converting guest to registered user"""
    guest_team_id: str


class SessionExchange(BaseModel):
    """Request model for exchanging Emergent Auth session"""
    session_id: str
