"""
Database configuration and connection.
This module provides the shared MongoDB connection for all routes.
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB Connection
MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME", "celebrity_buzz")

if not MONGO_URL:
    raise ValueError("MONGO_URL environment variable is required")

# Create MongoDB client
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Environment variables for auth
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "")
EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")

async def close_db():
    """Close database connection"""
    client.close()
