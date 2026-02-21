"""Application settings and constants"""
import os

# API URLs
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "noreply@celebritybuzz.com")

# Team customization options
TEAM_COLORS = [
    {"id": "pink", "name": "Hot Pink", "hex": "#FF0099"},
    {"id": "cyan", "name": "Electric Cyan", "hex": "#00F0FF"},
    {"id": "gold", "name": "Gold", "hex": "#FFD700"},
    {"id": "purple", "name": "Royal Purple", "hex": "#8B5CF6"},
    {"id": "red", "name": "Fire Red", "hex": "#EF4444"},
    {"id": "green", "name": "Emerald", "hex": "#10B981"},
    {"id": "orange", "name": "Sunset Orange", "hex": "#F97316"},
    {"id": "white", "name": "Pearl White", "hex": "#FFFFFF"},
]

TEAM_ICONS = [
    {"id": "star", "name": "Star", "emoji": "⭐"},
    {"id": "crown", "name": "Crown", "emoji": "👑"},
    {"id": "fire", "name": "Fire", "emoji": "🔥"},
    {"id": "lightning", "name": "Lightning", "emoji": "⚡"},
    {"id": "rocket", "name": "Rocket", "emoji": "🚀"},
    {"id": "diamond", "name": "Diamond", "emoji": "💎"},
    {"id": "skull", "name": "Skull", "emoji": "💀"},
    {"id": "ghost", "name": "Ghost", "emoji": "👻"},
    {"id": "alien", "name": "Alien", "emoji": "👽"},
    {"id": "robot", "name": "Robot", "emoji": "🤖"},
    {"id": "unicorn", "name": "Unicorn", "emoji": "🦄"},
    {"id": "dragon", "name": "Dragon", "emoji": "🐉"},
]

# Badge definitions
BADGES = {
    "weekly_winner": {
        "id": "weekly_winner",
        "name": "Weekly Winner",
        "description": "Won the weekly league competition",
        "icon": "🏆",
        "tier": "gold"
    },
    "league_champion": {
        "id": "league_champion",
        "name": "League Legend",
        "description": "Won 3+ weekly competitions in a single league",
        "icon": "👑",
        "tier": "platinum"
    },
    "first_blood": {
        "id": "first_blood",
        "name": "First Blood",
        "description": "First celebrity picked after game launch",
        "icon": "🩸",
        "tier": "rare"
    },
    "brown_bread_collector": {
        "id": "brown_bread_collector",
        "name": "Grim Reaper",
        "description": "Collected 3+ Brown Bread bonuses",
        "icon": "💀",
        "tier": "silver"
    },
    "scandal_magnet": {
        "id": "scandal_magnet",
        "name": "Scandal Magnet",
        "description": "Had 5+ celebrities involved in controversies",
        "icon": "🔥",
        "tier": "bronze"
    },
    "royal_watcher": {
        "id": "royal_watcher",
        "name": "Royal Watcher",
        "description": "Had 3+ royals in team at once",
        "icon": "👸",
        "tier": "silver"
    },
    "full_house": {
        "id": "full_house",
        "name": "Full House",
        "description": "Filled all 10 team slots",
        "icon": "🏠",
        "tier": "bronze"
    },
}

# Celebrity tier configuration
TIER_CONFIG = {
    "A": {
        "base_price": 10.0,
        "min_price": 9.0,
        "max_price": 12.0,
        "points_multiplier": 1.0,
        "buzz_adjustment": 10,
    },
    "B": {
        "base_price": 6.5,
        "min_price": 5.0,
        "max_price": 8.0,
        "points_multiplier": 1.2,
        "buzz_adjustment": 5,
    },
    "C": {
        "base_price": 3.0,
        "min_price": 2.0,
        "max_price": 4.0,
        "points_multiplier": 1.5,
        "buzz_adjustment": 0,
    },
    "D": {
        "base_price": 1.0,
        "min_price": 0.5,
        "max_price": 1.5,
        "points_multiplier": 2.0,
        "buzz_adjustment": -5,
    },
}

# Profanity filter - banned words list
BANNED_WORDS = [
    "fuck", "fucking", "fucker", "fucked", "fucks",
    "shit", "shitty", "bullshit",
    "cunt", "cunts",
    "bitch", "bitches", "bitchy",
    "ass", "asshole", "arsehole", "arse",
    "dick", "dicks", "dickhead",
    "cock", "cocks",
    "wanker", "wankers",
    "twat", "twats",
    "piss", "pissed", "pisser",
    "nigger", "nigga", "niggas",
    "faggot", "fag", "fags",
    "retard", "retarded",
    "slut", "sluts", "slutty", "whore", "whores",
    "spastic", "mong", "mongol",
    "nazi", "hitler",
    "rape", "rapist",
    "pedo", "pedophile", "paedo",
    "bastard", "bastards",
    "bollocks", "bellend",
    "tosser", "knobhead", "wankstain",
    "motherfucker", "motherfucking",
    "goddamn", "goddam",
    "jackass",
]
