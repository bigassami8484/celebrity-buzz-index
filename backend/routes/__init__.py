"""
Routes module - API endpoint definitions

This module provides modular route definitions.
Routes are being migrated from the monolithic server.py file.

Completed Migrations:
- auth.py: Authentication (login, logout, OAuth, magic links)

Pending Migrations:
- celebrities.py: Celebrity search, categories, hot celebs
- teams.py: Team management, transfers
- leagues.py: Private leagues
- admin.py: Admin operations, price resets
"""

from .auth import auth_router, get_current_user, create_user_session

__all__ = [
    "auth_router",
    "get_current_user",
    "create_user_session",
]
