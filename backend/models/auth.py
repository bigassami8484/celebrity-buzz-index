"""
Authentication-related Pydantic models
"""
from pydantic import BaseModel, EmailStr
from typing import Optional

class MagicLinkRequest(BaseModel):
    email: EmailStr

class MagicLinkVerify(BaseModel):
    token: str
    email: EmailStr

class GoogleAuthCallback(BaseModel):
    credential: str
    team_id: Optional[str] = None

class GuestConvert(BaseModel):
    team_id: str
    user_id: str
