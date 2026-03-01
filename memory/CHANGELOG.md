# Celebrity Buzz Index - Changelog

## Feb 22, 2026 - Backend Refactoring Phase 2

### Auth Routes Migration
- ✅ Migrated all authentication routes from `server.py` to `/routes/auth.py`
- ✅ Created shared database configuration at `/config/database.py`
- ✅ Updated auth models at `/models/auth.py`
- ✅ Server.py reduced from 5488 to 5080 lines (~408 lines moved)

### Auth Endpoints Migrated:
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/magic-link/send` - Send magic link email
- `POST /api/auth/magic-link/verify` - Verify magic link token
- `POST /api/auth/google/callback` - Google OAuth callback
- `POST /api/auth/guest/convert` - Convert guest to registered user
- `POST /api/auth/logout` - Logout user
- `POST /api/auth/session` - Exchange Emergent Auth session

### Testing
- All auth endpoints verified working (100% pass rate)
- Frontend auth modal working correctly
- Test file created: `/app/backend/tests/test_iteration_19_auth_refactor.py`

---

## Earlier Changes (Feb 21-22, 2026)

### SEO Improvements
- Added pre-rendered static HTML content to `index.html`
- Added H1 tags and rich meta descriptions
- Added `<noscript>` fallback for crawlers

### Transfer Window Update
- Increased transfer limit from 2 to 3 transfers per window

### Search Performance & Accuracy
- Optimized celebrity search endpoint for faster responses
- Improved autocomplete to prioritize exact matches
- Fixed news matching logic for multi-word names

### Team & Points System
- Implemented "Submit Team" functionality with team locking
- Added transfer window status endpoint and UI banner
- Changed to daily points display (removed weekly)

### UI/UX Enhancements
- Added skull icon (💀) for deceased celebrities
- Made news articles clickable links
- Expanded "Brown Bread Watch" and "Most Picked" to show all 10
- Added custom SVG favicon

### Data Integrity
- Removed bands from database (The 1975, Twenty One Pilots)
- Implemented backend filter for bands/groups
- Updated deceased status for recently passed celebrities

### Backend Refactoring Phase 1
- Extracted celebrity data pools to `/data/celebrity_data.py`
- Extracted constants to `/data/constants.py`
- Created utility functions in `/utils/helpers.py`
- Created model templates for auth, celebrities, teams, leagues
