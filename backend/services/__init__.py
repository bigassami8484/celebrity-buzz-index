"""
Services module - Business logic separated from routes

This module contains service classes that encapsulate business logic
for different domains of the application.

Services:
- celebrity_service: Celebrity search, fetch, and management
- team_service: Team creation, management, and leaderboards
- league_service: Private league operations
"""

from .celebrity_service import (
    get_celebrity_by_id,
    get_celebrity_by_name,
    get_celebrities_by_category,
    search_celebrity_in_db,
    get_top_picked_celebrities,
    get_brown_bread_watch,
    update_celebrity,
    increment_times_picked,
    get_all_categories,
    record_price_history,
    get_price_history,
)

from .team_service import (
    create_team,
    get_team_by_id,
    get_team_by_user_id,
    add_celebrity_to_team,
    remove_celebrity_from_team,
    get_leaderboard,
    customize_team,
    contains_banned_words,
)

from .league_service import (
    create_league,
    get_league_by_id,
    get_league_by_code,
    join_league,
    leave_league,
    get_team_leagues,
    get_league_leaderboard,
)

__all__ = [
    # Celebrity services
    "get_celebrity_by_id",
    "get_celebrity_by_name", 
    "get_celebrities_by_category",
    "search_celebrity_in_db",
    "get_top_picked_celebrities",
    "get_brown_bread_watch",
    "update_celebrity",
    "increment_times_picked",
    "get_all_categories",
    "record_price_history",
    "get_price_history",
    # Team services
    "create_team",
    "get_team_by_id",
    "get_team_by_user_id",
    "add_celebrity_to_team",
    "remove_celebrity_from_team",
    "get_leaderboard",
    "customize_team",
    "contains_banned_words",
    # League services
    "create_league",
    "get_league_by_id",
    "get_league_by_code",
    "join_league",
    "leave_league",
    "get_team_leagues",
    "get_league_leaderboard",
]
