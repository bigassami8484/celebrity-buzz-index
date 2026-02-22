"""
Application constants - banned words, pricing config, etc.
"""

# Banned words for team names (racist, offensive)
BANNED_WORDS = [
    # Racial slurs
    "nigger", "nigga", "faggot", "fag", "retard", "spic", "chink", "gook", 
    "kike", "wetback", "beaner", "coon", "darkie", "paki", "raghead", 
    "cracker", "honky", "nazi", "hitler", "kkk", "n1gger", "n1gga",
    "racist", "racism", "white power", "white supremacy", "heil", 
    "holocaust", "aryan", "fuhrer", "reich",
    "slave", "slavery", "lynch", "lynching", "genocide",
    # Common swear words
    "fuck", "fucking", "fucked", "fucker", "fck", "f*ck", "fu*k",
    "shit", "shite", "sh1t", "bullshit", "horseshit",
    "cunt", "c*nt", "cnt",
    "bitch", "b1tch", "btch",
    "ass", "arse", "asshole", "arsehole", "a$$",
    "dick", "d1ck", "dickhead",
    "cock", "c0ck", "cockhead",
    "wanker", "wank", "tosser",
    "twat", "tw4t",
    "bastard", "bstrd",
    "piss", "pissed",
    "damn", "dammit", "goddamn",
    "whore", "slut", "slag", "skank",
    "bollocks", "balls",
    # Leet speak variations
    "f4g", "r3tard", "b1tch", "sh1t", "a55", "d1ck"
]

# High-profile celebrities with boosted base prices (controversial/newsworthy)
CONTROVERSIAL_CELEBS = {
    "prince andrew": 12,
    "meghan markle": 10,
    "prince harry": 10,
    "katie price": 8,
    "kanye west": 12,
    "elon musk": 15,
    "donald trump": 15,
    "boris johnson": 10,
}

# Starting budget for teams
STARTING_BUDGET = 50.0

# Maximum team size
MAX_TEAM_SIZE = 10

# Transfers allowed per week during transfer window
MAX_WEEKLY_TRANSFERS = 3

# Price tiers based on celebrity tier
PRICE_TIERS = {
    "A": {"min": 8.0, "max": 20.0},
    "B": {"min": 4.0, "max": 8.0},
    "C": {"min": 2.0, "max": 4.0},
    "D": {"min": 1.0, "max": 2.0},
}

# Team customization options
TEAM_EMOJIS = ["⭐", "🔥", "💎", "🏆", "👑", "🎯", "🚀", "💫", "🌟", "⚡", "🎭", "🎬", "🎤", "⚽", "🎪"]
TEAM_COLORS = [
    "#FF0099",  # Hot pink (default)
    "#00D4FF",  # Cyan
    "#FFD700",  # Gold
    "#FF4500",  # Orange red
    "#9400D3",  # Violet
    "#00FF7F",  # Spring green
    "#FF1493",  # Deep pink
    "#4169E1",  # Royal blue
    "#FF6347",  # Tomato
    "#7B68EE",  # Medium slate blue
]

# Categories
CATEGORIES = [
    "movie_stars",
    "tv_actors", 
    "musicians",
    "athletes",
    "royals",
    "reality_tv",
    "public_figure",
    "influencers",
    "comedians"
]
