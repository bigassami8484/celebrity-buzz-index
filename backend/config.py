"""
Application configuration and database setup
"""
import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("server")

# Environment variables
MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME", "celeb_buzz")
EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")

# Database client (initialized on startup)
client = None
db = None

def init_db():
    """Initialize database connection"""
    global client, db
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    return db

def get_db():
    """Get database instance"""
    global db
    if db is None:
        init_db()
    return db
