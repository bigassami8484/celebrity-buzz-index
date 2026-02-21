"""Database configuration and connection"""
import os
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB Connection
MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME", "celebrity_buzz")

if not MONGO_URL:
    raise ValueError("MONGO_URL environment variable is required")

# Create MongoDB client
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Export collections for easy access
celebrities_collection = db.celebrities
teams_collection = db.teams
leagues_collection = db.leagues
users_collection = db.users
user_sessions_collection = db.user_sessions
magic_links_collection = db.magic_links
news_cache_collection = db.news_cache
trending_cache_collection = db.trending_cache
price_history_collection = db.price_history

async def close_db():
    """Close database connection"""
    client.close()
