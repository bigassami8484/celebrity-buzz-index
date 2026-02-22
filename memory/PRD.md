# Celebrity Buzz Index - Product Requirements Document

## Original Problem Statement
Build a Celebrity Buzz Index fantasy-league style platform where users can:
- Search ANY celebrity worldwide with a Wikipedia page
- View AI-generated news coverage and Wikipedia info
- Calculate "buzz points" based on media mentions
- Build teams with a £50M budget
- Compete on leaderboards with friends
- Social sharing (Twitter/X, Facebook, WhatsApp)

## Backend Architecture (Refactored Feb 22, 2026)
```
/app/backend/
├── server.py          # Main FastAPI app (5355 lines - routes + business logic)
├── config.py          # Configuration module
├── data/
│   ├── __init__.py    # Data exports
│   ├── celebrity_data.py  # Celebrity pools, A-list definitions, aliases (441 lines)
│   └── constants.py   # Banned words, pricing config, team options (85 lines)
├── models/
│   ├── __init__.py    # Model exports
│   ├── celebrity.py   # Celebrity Pydantic models
│   ├── team.py        # Team models
│   ├── league.py      # League models
│   └── auth.py        # Auth models
├── routes/            # Route templates (ready for migration)
│   ├── auth.py        # Auth route template
│   ├── celebrities.py # Celebrity route template
│   ├── teams.py       # Team route template
│   ├── leagues.py     # League route template
│   └── admin.py       # Admin route template
├── services/          # (Future: extract business logic)
└── utils/
    ├── __init__.py
    └── helpers.py     # normalize_text, decode_html_entities, sanitize_team_name
```

**Completed Refactoring (Phase 1 & 2):**
- ✅ Extracted celebrity data pools (9 categories, 50+ celebs each)
- ✅ Extracted constants (banned words, pricing tiers, team options)
- ✅ Extracted utility functions (text normalization, HTML decoding)
- ✅ Created Pydantic models in separate files
- ✅ Server imports from modular structure
- ✅ Created route template files (auth, celebrities, teams, leagues, admin)

**Remaining Refactoring (Phase 3 - Future):**
- Fully migrate routes from server.py to routes/ directory
- Extract business logic into services/
- Split celebrity search/news generation into separate service

## Current Pricing Structure (DYNAMIC)
| Tier | Price Range | Strategy Impact |
|------|-------------|-----------------|
| A-List | £9m-£12m | High scoring but expensive |
| B-List | £5m-£8m | Balanced steady picks |
| C-List | £2m-£4m | Risk/reward |
| D-List | £0.5m-£1.5m | Cheap wildcards |

**STRICT PRICE CAP: £12M maximum for all celebrities**

**Exception - Brown Bread Watch Premium:**
- #1 oldest celebrity: £15M
- #2 oldest celebrity: £13M
- #3 oldest celebrity: £11M
- Rest: normal tier pricing

## Weekly Price Reset System (NEW - Feb 22, 2026)
- **Automated Scheduler**: Runs every Monday at 00:00 UTC using APScheduler
- **Admin endpoints**:
  - `POST /api/admin/weekly-price-reset` - Manual trigger
  - `POST /api/admin/trigger-weekly-reset` - Manual trigger (same result)
  - `GET /api/admin/price-change-preview` - Preview without modifying data
  - `GET /api/admin/scheduler-status` - Check scheduler status and next run time
- **Process**:
  1. Stores current price as `previous_week_price`
  2. Calculates new price based on `buzz_score` using `get_dynamic_price(tier, buzz_score, name)`
  3. Resets `buzz_score` to 0 for the new week
  4. Logs execution to `scheduled_tasks` collection for auditing
- **UI Display**: Price change indicators show:
  - Green +X% arrow for price increases
  - Red -X% arrow for price decreases
  - Visible on: Celebrity cards, Hot celebs ticker, Search modal, Team panel

## Transfer Window
- **Opens**: Every Saturday at 12:00 GMT
- **Duration**: 24 hours
- **Closes**: Sunday at 12:00 GMT
- 1 transfer per week allowed during window
- ✅ **LIVE COUNTDOWN BANNER** at top of page showing time remaining
- ✅ Green pulsing banner when OPEN, cyan when closed

## What's Been Implemented (Feb 2026)

### Core Features
- ✅ Full FastAPI backend with all endpoints
- ✅ **WIKIDATA-VERIFIED HUMAN SEARCH** (P31=Q5):
  - Uses SPARQL query to verify entities are humans
  - 100% accurate filtering - no brands, animals, places
  - Verified: Gucci returns only people, Lion returns only Alfred Lion
- ✅ A/B/C/D tier system with STRICT dynamic pricing (max £12M)
- ✅ **CONSISTENT PRICING** - uses default buzz score (50) for Hot Celebs, search, and categories
- ✅ Saturday 12pm GMT transfer window (24 hours)
- ✅ **BUZZ-SCORE-BASED DYNAMIC PRICING** (NEW Feb 22, 2026):
  - Prices fluctuate based on weekly buzz score accumulation
  - `previous_week_price` field tracks last week's price
  - Price change indicators (↑↓) shown in UI
  - Admin endpoints for weekly reset and preview
- ✅ **BROWN BREAD PREMIUM PRICING IN SEARCH**:
  - Top 3 oldest celebrities show premium prices when searched
  - David Attenborough (Age 100): £15M
  - Michael Caine (Age 93): £13M
  - Judi Dench (Age 92): £11M
- ✅ **PRICE HISTORY TRACKING**:
  - MongoDB 'price_history' collection
  - Records price changes automatically
  - API endpoints: `/api/price-history/celebrity-name/{name}`, `/api/celebrity/{id}/price-history`
  - Frontend modal with trend indicators
- ✅ Price alerts system
- ✅ Hot streak notifications (3+ days in news)
- ✅ Profanity filter for team names
- ✅ **CATEGORY DETECTION FIX** (Feb 22, 2026):
  - Known actors (Michael Caine, Ian McKellen, Morgan Freeman, etc.) correctly classified as movie_stars
  - **TV Presenters** correctly categorized as "other": Graham Norton, Holly Willoughby, Amanda Holden, Simon Cowell, David Attenborough
  - **Musicians** correctly categorized: Peter Andre, Victoria Beckham, Kerry Katona
  - **Movie Stars** fixed: Timothée Chalamet, Shia LaBeouf (were incorrectly in musicians)
  - **Athletes** fixed: Jonathan Owens, Tyreek Hill (were incorrectly in other)
  - Added category override system for 40+ commonly miscategorized celebrities
  - Added bio-based detection for "chat show", "talk show", "broadcaster" keywords
- ✅ **24-HOUR NEWS CACHE** - News feed refreshes every 24 hours (was 15 min)
- ✅ **REAL NEWS FROM RSS FEEDS** (Feb 22, 2026):
  - Individual celebrity news now fetches REAL articles from RSS feeds first
  - Searches 18 news sources (BBC, TMZ, People, Daily Mail, The Sun, etc.)
  - Only supplements with AI-generated news when real news is insufficient
  - News articles marked with `is_real: true/false` flag
  - Real news prioritized and shown first in the feed
  - Improved search matching for multi-word names (e.g., "Van Der Beek")
  - Special context for recently deceased celebrities ensures accurate news
  - **RECENT DEATHS HANDLED**: James Van Der Beek (Feb 11), Eric Dane (Feb 18), Robert Duvall

### UI Features
- ✅ **HOT CELEBS BANNER** at top of page with **HORIZONTAL AUTO-SCROLL**
  - **18+ CELEBRITIES ACTUALLY IN THE NEWS THIS WEEK**
  - Checks 150+ known celebrities against 6 RSS news feeds
  - Only shows celebrities with REAL Wikipedia photos (no placeholders)
  - Sources: BBC, TMZ, People, Page Six, Daily Mail, Guardian
  - Shows actual news headline as "hot reason"
  - Auto-scrolling marquee animation (25s linear infinite)
  - Pauses on hover, clickable to search
  - 1-hour cache for performance
- ✅ **CONSISTENT PRICING EVERYWHERE**:
  - Hot Celebs card price = Search result price = Team panel price
  - Fixed bug where Leonardo DiCaprio showed £19M in team (now £10.3M everywhere)
- ✅ "How It Works" with **LARGER** icons (40x40px) and text (text-sm/text-xs)
  - Find any celeb, Tier pricing, Your budget, Transfer window, Brown Bread
- ✅ **CELEB NEWS** with **3-LINE HEADLINES** (line-clamp-3)
- ✅ **PLAYER COUNT REMOVED** - cleaner header design
- ✅ **PRICE HISTORY BUTTON** on each celebrity card (chart icon)
- ✅ **PRICE HISTORY MODAL** showing current price, tier, and historical entries
- ✅ Proper spacing between components
- ✅ "Select a category or search for any celebrity" helper text
- ✅ Category filter directly under search bar
- ✅ **PRICE HISTORY BUTTON** on each celebrity card (chart icon top-right)
- ✅ **PRICE HISTORY MODAL** showing current price, tier, and historical entries with trend indicators

### Search Verification (Wikidata P31=Q5)
**Verified Test Cases:**
- "gucci" → Gucci Mane, Maurizio Gucci, Guccio Gucci, Paolo Gucci, Aldo Gucci (NO BRAND) ✅
- "lion" → Alfred Lion (NO ANIMAL) ✅
- "beyonce" → Beyoncé ✅
- "taylor" → Taylor Swift, Elizabeth Taylor, Angus Taylor, Teyana Taylor, Christine Taylor ✅
- "nike" → Nike Ardilla and other people (NO BRAND) ✅
- "tesla" → Nikola Tesla (NO CARS) ✅

## API Endpoints

### New Price History Endpoints
- `GET /api/price-history/celebrity-name/{name}` - Get price history by celebrity name
- `GET /api/celebrity/{id}/price-history` - Get price history by celebrity ID

Response format:
```json
{
  "celebrity_name": "Taylor Swift",
  "current_price": 5.5,
  "current_tier": "B",
  "history": [
    {
      "celebrity_id": "xxx",
      "celebrity_name": "Taylor Swift",
      "price": 5.5,
      "tier": "B",
      "buzz_score": 21.5,
      "recorded_at": "2026-02-21T..."
    }
  ]
}
```

## Backlog / Future Features

### P0 (Immediate - In Progress)
- ✅ Wikidata-based search filtering - COMPLETED
- ✅ Price history tracking - COMPLETED
- 🔄 Hot Streak Notifications - Backend ready, needs full UI

### P1 (High Priority)
- User authentication for persistent teams
- Real news API integration (NewsAPI)
- Automated weekly badge awards

### P2 (Medium Priority)
- Celebrity comparison feature
- Push notifications
- ✅ **Refactor App.js into smaller components** - COMPLETED Feb 2026
  - Reduced from 2,674 lines to 730 lines (73% reduction)
  - Created modular component structure:
    - `/src/api/index.js` - All API functions (191 lines)
    - `/src/components/auth/` - AuthModal, AuthCallback, UserMenu, SaveTeamPrompt
    - `/src/components/celebrities/` - SearchBar, CelebrityCard, HotCelebsBanner, TopPickedCelebs, BrownBreadWatch, TodaysNews
    - `/src/components/team/` - TeamPanel, TeamCustomizeModal
    - `/src/components/leagues/` - LeaguePanel, LeagueDetailModal, Leaderboard
    - `/src/components/modals/` - ShareModal, PointsMethodology, PriceHistoryModal, HallOfFameModal, PriceAlerts, HotStreaks
    - `/src/components/layout/` - Header, Footer, TransferWindowBanner, HowItWorks
    - `/src/components/common/` - TierBadge, LoadingCard, CategoryFilter
- ✅ **AI Image Generation for Celebrities** - COMPLETED Dec 2025
  - Uses OpenAI gpt-image-1 via Emergent LLM key
  - Generates professional portraits when Wikipedia has no photo
  - Images cached in MongoDB `ai_images` collection
  - On-demand generation via "AI Photo" button on celebrity cards
  - API endpoints: POST `/api/celebrity/generate-image`, GET `/api/celebrity/ai-image/{name}`

### P3 (Nice to Have)
- Dark/light mode toggle
- Mobile app version
- Celebrity draft mode (turn-based picking)
- ✅ Hot Celebs uses DYNAMIC pricing based on tier and buzz
- ✅ "How It Works" section with explainer text
- ✅ News headlines cleaned (HTML entities decoded) - limited to 6 articles
- ✅ Price Alerts panel in sidebar
- ✅ Hot Streaks panel in sidebar
- ✅ Brown Bread Watch with PREMIUM tags for top 3
- ✅ **MOBILE RESPONSIVE** - fully functional on phones

### Mobile Features
- ✅ Responsive layout with stacked elements
- ✅ Bottom navigation bar (Home, Team tabs)
- ✅ Touch-friendly category buttons
- ✅ Scrollable Hot Celebs with photos
- ✅ Mobile-optimized search bar

### Social Features
- ✅ Team sharing (WhatsApp, X, Facebook)
- ✅ League sharing (WhatsApp, X, Facebook)
- ✅ Friends League system with invite codes
- ✅ Badge/achievement system
- ✅ Hall of Fame

### Search Filtering (Updated Feb 21, 2026)
- ✅ Filters out locations, cities, countries, areas
- ✅ Filters out films, TV shows, albums, songs
- ✅ Filters out universities, schools, institutions
- ✅ Filters out awards, medals, decorations
- ✅ Filters out prisons, hospitals, buildings
- ✅ Only returns actual people/celebrities

**Tested Search Queries:**
- "leonard" → Kawhi Leonard, Leonard Cohen, Leonard Nimoy ✅
- "georgia" → Georgia O'Keeffe, Georgia Holt, Georgia Tennant ✅
- "florence" → Florence Welch, Florence Pugh, Florence Nightingale ✅
- "victoria" → Queen Victoria, Victoria Beckham, Victoria Justice ✅

## Example Prices (Verified)
**Trending Celebs:**
- Ed Sheeran: D-LIST £0.9M ✅
- Gemma Collins: C-LIST £2.4M ✅
- David Beckham: C-LIST £2.4M ✅
- Gordon Ramsay: D-LIST £0.7M ✅
- Tom Holland: A-LIST £9.5M ✅
- Katie Price: D-LIST £0.7M ✅

**Hot Celebs (Dynamic Pricing):**
- Adele: A-LIST £9.5M ✅
- Prince Harry: A-LIST £10.3M ✅
- Kate Middleton: A-LIST £10.3M ✅
- Kerry Katona: C-LIST £2.9M ✅

**Brown Bread Watch:**
- Michael Caine (Age 93): £15M ⭐ PREMIUM
- Judi Dench (Age 92): £13M ⭐ PREMIUM
- Morgan Freeman (Age 89): £11M ⭐ PREMIUM
- Ian McKellen (Age 87): £10.3M
- Al Pacino (Age 86): £9.5M

## Backlog / Future Features

### P0 (Immediate - In Progress)
- ✅ Search filter improvements - COMPLETED
- ✅ Hot Celebs dynamic pricing - COMPLETED
- ✅ How It Works explainer text - COMPLETED
- ✅ **Title Size Fix** - COMPLETED (Dec 2025)
  - Desktop: 6-8rem (96-128px) - well balanced
  - Mobile: 2.75-3.25rem (44-52px) - increased for readability
- ✅ **Authentication System** - COMPLETED (Dec 2025)
  - Emergent Google OAuth (no API keys required)
  - Magic Link email login (requires RESEND_API_KEY for production)
  - Sign In button in header
  - Auth modal with Google + Email options
  - User menu with logout
- ✅ **Save My Team Prompt** - COMPLETED (Dec 2025)
  - Shows for guest users after adding celebrities
  - 3-second delay for better UX
  - "Sign In to Save" and "Later" options
- ✅ **Mobile Bottom Tabs Removed** - COMPLETED (Dec 2025)
- 🔄 Hot Streak Notifications - Backend ready, needs full UI

### P1 (High Priority)
- Link user accounts to teams for persistent data
- Real news API integration (NewsAPI)
- Automated weekly badge awards

### P2 (Medium Priority)
- Celebrity comparison feature
- Historical buzz trends chart
- Push notifications
- Price history tracking

### P3 (Nice to Have)
- Dark/light mode toggle
- Mobile app version
- Celebrity draft mode (turn-based picking)

## Authentication Details (Dec 2025)
- **Google OAuth**: Uses Emergent Auth (https://auth.emergentagent.com)
  - No API keys needed - managed by Emergent
  - Redirect flow with session_id in URL fragment
  - Backend exchanges session_id for user data
- **Magic Link**: Uses Resend for email (requires RESEND_API_KEY in production)
- **Session Storage**: MongoDB with 7-day expiry
- **Cookie**: httpOnly, secure, sameSite=none

### Auth Endpoints:
- `POST /api/auth/session` - Exchange Emergent session_id for user session
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Log out user
- `POST /api/auth/magic-link/send` - Send magic link email
- `POST /api/auth/magic-link/verify` - Verify magic link token


## Code Architecture (Updated Dec 2025)

### Frontend Structure (Refactored)
```
/app/frontend/src/
├── App.js                    # Main app (730 lines, refactored from 2674)
├── App.css                   # All styles
├── api/
│   └── index.js              # All API functions (191 lines)
├── components/
│   ├── auth/                 # AuthModal, AuthCallback, UserMenu, SaveTeamPrompt
│   ├── celebrities/          # SearchBar, CelebrityCard, HotCelebsBanner, TopPickedCelebs, BrownBreadWatch, TodaysNews
│   ├── team/                 # TeamPanel, TeamCustomizeModal
│   ├── leagues/              # LeaguePanel, LeagueDetailModal, Leaderboard
│   ├── modals/               # ShareModal, PointsMethodology, PriceHistoryModal, HallOfFameModal, PriceAlerts, HotStreaks
│   ├── layout/               # Header, Footer, TransferWindowBanner, HowItWorks
│   ├── common/               # TierBadge, LoadingCard, CategoryFilter
│   └── ui/                   # Shadcn components
```

### Backend Structure (Preparation for Refactoring)
```
/app/backend/
├── server.py                 # Monolithic server (3,772 lines) - NEEDS REFACTORING
├── config/
│   ├── __init__.py           # Config exports
│   ├── database.py           # MongoDB connection
│   └── settings.py           # Constants, badges, team options
├── models/
│   └── __init__.py           # Pydantic models
├── utils/
│   └── __init__.py           # Utility functions (pricing, profanity filter, etc.)
├── routes/                   # (Prepared - not yet migrated)
├── services/                 # (Prepared - not yet migrated)
└── tests/                    # Test files
```

### Key Technical Details
- **Frontend**: React.js, TailwindCSS, axios, lucide-react, sonner (toasts)
- **Backend**: Python, FastAPI, Motor (async MongoDB), Pydantic, httpx, feedparser
- **Authentication**: Emergent-managed Google OAuth, guest sessions with JWT
- **Data Sources**: Wikipedia API (OpenSearch), Wikidata API (SPARQL), Public RSS Feeds, OpenAI (news generation)

## Remaining Backend Refactoring Tasks
- [ ] Split server.py routes into `/routes/` modules (auth.py, celebrities.py, teams.py, leagues.py)
- [ ] Move services into `/services/` (wikipedia.py, news.py, pricing.py)
- [ ] Test thoroughly after migration to ensure no regressions

## Recent Updates (Feb 22, 2026)

### Celebrity Image Fix - COMPLETED
- ✅ **Image Auto-Refresh**: When searching for a celebrity with a placeholder image, the system now automatically:
  1. Re-fetches from Wikipedia to get real image
  2. Falls back to AI image generation (OpenAI gpt-image-1) if Wikipedia has no image
- ✅ **Name Disambiguation**: Added aliases for ambiguous celebrity names:
  - "Brian Cox" → Brian Cox (physicist) - gets correct Wikipedia page
  - "Drake" → Drake (musician)
  - "Alex Scott" → Alex Scott (footballer, born 1984)
  - "George Russell" → George Russell (racing driver)
  - "Sam Thompson" → Sam Thompson (TV personality)
  - "Queen Camilla" → Queen Camilla
  - "Prince Edward" → Prince Edward, Duke of Edinburgh
  - And many more...
- ✅ **Admin Endpoint**: `/api/admin/refresh-placeholder-images` to batch refresh images
- ✅ **Current Status**: 
  - 95% of celebrities have Wikipedia images (515 out of 540)
  - 2% have AI-generated images (13 celebrities)
  - Only 2% still have placeholders (12 celebrities - these lack both Wikipedia and successful AI generation)

### User-Requested Celebrities Verified:
- ✅ Scarlett Johansson: Wikipedia image
- ✅ Brian Cox (physicist): Wikipedia image
- ✅ Queen Camilla: Wikipedia image  
- ✅ Spencer Matthews: Initials placeholder (per user request)
- ✅ Georgia Toffolo: Initials placeholder (per user request)
- ✅ Sam Thompson: Wikipedia image

### UI Improvements (Feb 22, 2026)
- ✅ **Floating Search Result Card**: When searching for a celebrity, results now appear in a floating modal overlay instead of being added to the category grid
  - Centered modal with blur backdrop
  - Shows image, tier badge, price, bio, category
  - "Add to Team" button
  - Click outside or X to close
- ✅ **Data Cleanup**: Removed duplicate celebrity entries, fixed TV Personalities categorization
- ✅ **Category Counts**: 529 celebrities across all categories

