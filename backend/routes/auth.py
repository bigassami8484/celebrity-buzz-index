"""
Authentication Routes

Handles user authentication, sessions, magic links, and OAuth.
Endpoints:
- GET /api/auth/me - Get current user info
- POST /api/auth/magic-link/send - Send magic link email
- POST /api/auth/magic-link/verify - Verify magic link token
- POST /api/auth/google/callback - Google OAuth callback
- POST /api/auth/guest/convert - Convert guest to registered user
- POST /api/auth/logout - Logout user
- POST /api/auth/session - Exchange Emergent Auth session
"""

from fastapi import APIRouter, HTTPException, Request, Response
from typing import Optional
import uuid
import logging
import httpx
import resend
from datetime import datetime, timezone, timedelta

from config.database import db, RESEND_API_KEY, SENDER_EMAIL, FRONTEND_URL
from models.auth import MagicLinkRequest, MagicLinkVerify, GuestConvert

# Configure logging
logger = logging.getLogger(__name__)

# Setup Resend for magic links
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

# Create router
auth_router = APIRouter(prefix="/api/auth", tags=["auth"])


# ==================== HELPER FUNCTIONS ====================

async def get_current_user(request: Request) -> Optional[dict]:
    """Get current user from session token in cookie or Authorization header"""
    session_token = None
    
    # Check Authorization header first
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        session_token = auth_header[7:]
    
    # Fallback to cookie
    if not session_token:
        session_token = request.cookies.get("session_token")
    
    if not session_token:
        return None
    
    # Find session
    session = await db.user_sessions.find_one(
        {"session_token": session_token, "expires_at": {"$gt": datetime.now(timezone.utc).isoformat()}},
        {"_id": 0}
    )
    
    if not session:
        return None
    
    # Find user
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    return user


def create_session_token() -> str:
    """Generate a secure session token"""
    return str(uuid.uuid4()) + "-" + str(uuid.uuid4())


async def create_user_session(user_id: str) -> str:
    """Create a new session for user"""
    session_token = create_session_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    
    session = {
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.user_sessions.insert_one(session)
    return session_token


# ==================== ROUTES ====================

@auth_router.get("/me")
async def get_me(request: Request):
    """Get current user info"""
    user = await get_current_user(request)
    if not user:
        return {"user": None, "is_authenticated": False}
    
    # Get user's team
    team = await db.teams.find_one({"owner_user_id": user["user_id"]}, {"_id": 0})
    
    return {
        "user": user,
        "team": team,
        "is_authenticated": True
    }


@auth_router.post("/magic-link/send")
async def send_magic_link(request: MagicLinkRequest):
    """Send magic link email for passwordless login"""
    email = request.email.lower().strip()
    
    # Generate magic link token
    token = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    # Store magic link
    await db.magic_links.update_one(
        {"email": email},
        {"$set": {
            "email": email,
            "token": token,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "used": False
        }},
        upsert=True
    )
    
    # Send email
    magic_link_url = f"{FRONTEND_URL}?auth_token={token}"
    
    if RESEND_API_KEY:
        try:
            resend.Emails.send({
                "from": SENDER_EMAIL,
                "to": email,
                "subject": "Sign in to Celebrity Buzz Index",
                "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #FF0099; margin-bottom: 20px;">Celebrity Buzz Index</h1>
                    <p style="font-size: 16px; color: #333;">Click the link below to sign in:</p>
                    <a href="{magic_link_url}" style="display: inline-block; background: linear-gradient(90deg, #FF0099, #00F0FF); color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; font-weight: bold;">
                        Sign In to Celebrity Buzz Index
                    </a>
                    <p style="font-size: 14px; color: #666; margin-top: 20px;">This link expires in 1 hour.</p>
                    <p style="font-size: 12px; color: #999;">If you didn't request this email, you can safely ignore it.</p>
                </div>
                """
            })
            logger.info(f"Magic link sent to {email}")
        except Exception as e:
            logger.error(f"Failed to send magic link: {e}")
            # In development, return the token for testing
            return {"success": True, "message": "Magic link sent! Check your email.", "dev_token": token}
    else:
        # No Resend API key - return token for testing
        logger.warning("No RESEND_API_KEY set - returning token for testing")
        return {"success": True, "message": "Magic link generated (email not sent - dev mode)", "dev_token": token}
    
    return {"success": True, "message": "Magic link sent! Check your email."}


@auth_router.post("/magic-link/verify")
async def verify_magic_link(request: MagicLinkVerify, response: Response):
    """Verify magic link token and create session"""
    token = request.token
    
    # Find magic link
    magic_link = await db.magic_links.find_one(
        {"token": token, "used": False, "expires_at": {"$gt": datetime.now(timezone.utc).isoformat()}},
        {"_id": 0}
    )
    
    if not magic_link:
        raise HTTPException(status_code=400, detail="Invalid or expired magic link")
    
    email = magic_link["email"]
    
    # Mark magic link as used
    await db.magic_links.update_one({"token": token}, {"$set": {"used": True}})
    
    # Find or create user
    user = await db.users.find_one({"email": email}, {"_id": 0})
    
    if not user:
        # Create new user
        user_id = str(uuid.uuid4())
        user = {
            "user_id": user_id,
            "email": email,
            "name": email.split("@")[0],
            "picture": f"https://ui-avatars.com/api/?name={email.split('@')[0]}&background=FF0099&color=fff",
            "is_guest": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user)
        if '_id' in user:
            del user['_id']
    
    # Create session
    session_token = await create_user_session(user["user_id"])
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=30 * 24 * 60 * 60  # 30 days
    )
    
    return {
        "success": True,
        "user": user,
        "session_token": session_token
    }


@auth_router.post("/google/callback")
async def google_auth_callback(request: Request, response: Response):
    """Handle Google OAuth callback"""
    body = await request.json()
    google_token = body.get("credential") or body.get("token")
    
    if not google_token:
        raise HTTPException(status_code=400, detail="No Google token provided")
    
    # Verify Google token
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={google_token}",
                timeout=10.0
            )
            
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail="Invalid Google token")
            
            google_user = resp.json()
    except Exception as e:
        logger.error(f"Google token verification failed: {e}")
        raise HTTPException(status_code=400, detail="Failed to verify Google token")
    
    email = google_user.get("email", "").lower()
    name = google_user.get("name", email.split("@")[0])
    picture = google_user.get("picture", "")
    
    if not email:
        raise HTTPException(status_code=400, detail="No email in Google token")
    
    # Find or create user
    user = await db.users.find_one({"email": email}, {"_id": 0})
    
    if not user:
        user_id = str(uuid.uuid4())
        user = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture or f"https://ui-avatars.com/api/?name={name}&background=FF0099&color=fff",
            "is_guest": False,
            "google_id": google_user.get("sub"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user)
        if '_id' in user:
            del user['_id']
    
    # Create session
    session_token = await create_user_session(user["user_id"])
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=30 * 24 * 60 * 60
    )
    
    return {
        "success": True,
        "user": user,
        "session_token": session_token
    }


@auth_router.post("/guest/convert")
async def convert_guest_to_user(request: Request, body: GuestConvert, response: Response):
    """Link a guest team to an authenticated user"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    guest_team_id = body.guest_team_id
    
    # Find guest team
    guest_team = await db.teams.find_one({"id": guest_team_id}, {"_id": 0})
    if not guest_team:
        raise HTTPException(status_code=404, detail="Guest team not found")
    
    # Check if user already has a team
    existing_team = await db.teams.find_one({"owner_user_id": user["user_id"]}, {"_id": 0})
    
    if existing_team:
        # Merge guest team celebrities into existing team
        guest_celebs = guest_team.get("celebrities", [])
        existing_celebs = existing_team.get("celebrities", [])
        
        # Add guest celebs that aren't already in team
        existing_celeb_ids = {c["id"] for c in existing_celebs}
        for celeb in guest_celebs:
            if celeb["id"] not in existing_celeb_ids and len(existing_celebs) < 10:
                existing_celebs.append(celeb)
        
        # Update team
        await db.teams.update_one(
            {"id": existing_team["id"]},
            {"$set": {"celebrities": existing_celebs}}
        )
        
        # Delete guest team
        await db.teams.delete_one({"id": guest_team_id})
        
        return {"success": True, "team": existing_team, "merged": True}
    else:
        # Transfer ownership of guest team to user
        await db.teams.update_one(
            {"id": guest_team_id},
            {"$set": {
                "owner_user_id": user["user_id"],
                "is_guest": False
            }}
        )
        
        guest_team["owner_user_id"] = user["user_id"]
        guest_team["is_guest"] = False
        
        return {"success": True, "team": guest_team, "merged": False}


@auth_router.post("/logout")
async def logout(request: Request, response: Response):
    """Log out user by deleting session"""
    session_token = request.cookies.get("session_token")
    auth_header = request.headers.get("Authorization", "")
    
    if auth_header.startswith("Bearer "):
        session_token = auth_header[7:]
    
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    
    response.delete_cookie("session_token")
    
    return {"success": True, "message": "Logged out"}


@auth_router.post("/session")
async def exchange_session(request: Request, response: Response):
    """
    Exchange Emergent Auth session_id for user session.
    This endpoint receives session_id from frontend after Google OAuth redirect.
    REMINDER: The redirect URL on frontend MUST NOT be hardcoded - use window.location.origin
    """
    body = await request.json()
    session_id = body.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="No session_id provided")
    
    # Call Emergent Auth to get user data
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": session_id},
                timeout=15.0
            )
            
            if resp.status_code != 200:
                logger.error(f"Emergent Auth session-data error: {resp.status_code} - {resp.text}")
                raise HTTPException(status_code=400, detail="Invalid session_id")
            
            auth_data = resp.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Auth service timeout")
    except Exception as e:
        logger.error(f"Emergent Auth session exchange failed: {e}")
        raise HTTPException(status_code=400, detail="Failed to exchange session")
    
    email = auth_data.get("email", "").lower()
    name = auth_data.get("name", email.split("@")[0])
    picture = auth_data.get("picture", "")
    
    if not email:
        raise HTTPException(status_code=400, detail="No email in auth data")
    
    # Find or create user
    user = await db.users.find_one({"email": email}, {"_id": 0})
    
    if not user:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        user = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture or f"https://ui-avatars.com/api/?name={name}&background=FF0099&color=fff",
            "is_guest": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user)
        if '_id' in user:
            del user['_id']
    else:
        # Update user info if needed
        update_fields = {}
        if name and name != user.get("name"):
            update_fields["name"] = name
        if picture and picture != user.get("picture"):
            update_fields["picture"] = picture
        
        if update_fields:
            await db.users.update_one({"email": email}, {"$set": update_fields})
            user.update(update_fields)
    
    # Create session
    session_token = await create_user_session(user["user_id"])
    
    # Set httpOnly cookie with path="/", secure=True, samesite="none"
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60  # 7 days
    )
    
    return {
        "success": True,
        "user": user,
        "session_token": session_token
    }
