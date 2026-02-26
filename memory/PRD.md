# Celebrity Buzz Index - Product Requirements Document

## Original Problem Statement
Build a Celebrity Buzz Index fantasy-league style platform where users can:
- Search ANY celebrity worldwide with a Wikipedia page
- View AI-generated news coverage and Wikipedia info
- Calculate "buzz points" based on media mentions
- Build teams with a £50M budget
- Compete on leaderboards with friends
- Social sharing (Twitter/X, Facebook, WhatsApp)

## Latest Updates (Feb 26, 2026 - Session 8)

### Refactoring & Bug Fixes (Feb 26, 2026)
**User Request**: Refactor frontend and backend, fix "site going black" issue

**BACKEND REFACTORING - Phase 1**:
- Created `/app/backend/services/` module with business logic:
  - `celebrity_service.py`: Celebrity search, fetch, management
  - `team_service.py`: Team creation, management, leaderboards
  - `league_service.py`: Private league operations
- Services are properly exported via `__init__.py`
- Backend still uses `server.py` (9400 lines) but services are ready for gradual migration

**FRONTEND REFACTORING - Phase 1**:
- Created custom hooks in `/app/frontend/src/hooks/`:
  - `useTeam.js`: Team management state and logic
  - `useAuth.js`: Authentication state and logic
  - `useCelebrities.js`: Celebrity data fetching
  - `useLeagues.js`: League management
- Hooks are exported via `index.js`
- App.js still uses direct state but hooks are ready for gradual migration

**BUG FIXES**:
- Added `ErrorBoundary` component to catch and display JavaScript errors gracefully
- Fixed CSS causing black screen flash: set `background: #050505 !important` in `index.css` and `index.html`
- Fixed React key warnings in `BrownBreadWatch.jsx`, `TopPickedCelebs.jsx`, and `App.js`

**Technical Details**:
- Error boundary wraps entire app in `index.js`
- Critical CSS in HTML ensures dark background before React hydrates
- All list renders now use fallback keys: `key={celeb.id || \`fallback-${idx}\`}`

---

## Previous Updates (Feb 26, 2026 - Session 7)

### NEW: Strict Exact-Match Search (Feb 26, 2026)
**User Request**: No partial matches - celebrity should only appear when full name is typed
**Problem Solved**: Typing "shak" would show irrelevant suggestions like "William Shakespeare" or "Shawn Mendes"
**Implementation**:
- Completely rewrote `/api/autocomplete` endpoint to be strict exact-match only
- No fuzzy matching, no Wikipedia autocomplete suggestions
- Single-name celebrities (shakira, adele, beyonce, etc.) handled via explicit dictionary
- Only returns results when full celebrity name is typed exactly
**Verified Results**:
- "shak" → 0 results ✅
- "tom" → 0 results ✅
- "shakira" → 1 result (Shakira, A-LIST, £15M) ✅
- "tom hanks" → 1 result (Tom Hanks, A-LIST, £13M) ✅
- "adele" → 1 result (Adele) ✅
- Case insensitive: "SHAKIRA" works same as "shakira" ✅

### NEW: Random Category (Feb 26, 2026)
**User Request**: Add a category that pulls celebrities from ALL existing categories
**Implementation**:
- Added "Random" to CATEGORIES list with shuffle icon
- Modified `/api/celebrities/category/{category}` to handle `random` category
- Uses MongoDB $sample for true randomness
- Returns 8 celebrities from mixed categories on each request
**Verified Results**:
- Random category appears in UI with shuffle icon ✅
- Returns celebrities from athletes, movie_stars, musicians, royals, tv_actors, etc. ✅
- Different results on each refresh ✅

### NEW: "I'm Feeling Lucky!" Button (Feb 26, 2026)
**User Request**: Auto-draft a random celebrity to the team
**Implementation**:
- Added `GET /api/feeling-lucky/{team_id}` endpoint
- Returns a random affordable celebrity not already in team
- Frontend button with dice icon and pink-to-gold gradient
- Clicking auto-searches and adds the celebrity to team
**Features**:
- Respects budget (only shows celebs you can afford)
- Won't duplicate (skips celebs already in team)
- Won't overflow (disabled when team is full - 10 players)
- Shows toast notification with result

---

## Previous Updates (Feb 25, 2026 - Session 6)

### CRITICAL FIX: Price/Tier Consistency Across All UI Components (Feb 25, 2026)
**Problem**: Celebrities showed different prices in Hot Celebs banner, Search results, and Category pages. For example, Taylor Swift showed £14.3M in Hot Celebs but £14.9M in Search.
**Root Cause**: The hot celebs endpoint applied a "news premium" multiplier (1.05-1.15x) to prices, and autocomplete also applied a 1.15x premium for hot celebrities.
**Fix Applied**:
- Removed news premium multiplier from `/api/hot-celebs` endpoint - now uses base price directly
- Removed 1.15x hot celeb premium from `/api/autocomplete` endpoint
- Added `/api/admin/refresh-hot-celebs` endpoint to force cache refresh
**Verified Results**:
- Taylor Swift: £13.0M in Hot Celebs AND Search ✅
- Eric Dane: £6.9M in Hot Celebs AND Search ✅
- Prince Harry: £11.0M in Search AND Category ✅

### NEW: Royals Added with Real Photos (Feb 25, 2026)
**Added Celebrities**:
- Prince Harry, Duke of Sussex (A-LIST, £11M, real photo)
- Charles III (A-LIST, £15M, real photo)
- William, Prince of Wales (A-LIST, £13M, real photo)
- Plus 14 more royals: Princess Anne, Prince Edward, Sophie Duchess of Edinburgh, Sarah Ferguson, Mike Tindall, Lady Louise Windsor, Princess Mary of Denmark, Crown Princess Victoria, King Felipe VI, Queen Letizia, Queen Maxima, etc.
**Total Royals**: ~20 celebrities

### NEW: TV Presenters Moved to tv_personalities (Feb 25, 2026)
**Moved from "Other"**:
- Phillip Schofield, Alan Carr, Rylan Clark, Graham Norton, Davina McCall
- Dermot O'Leary, Ant McPartlin, Declan Donnelly, Jonathan Ross, Holly Willoughby

### NEW: Category Corrections (Feb 25, 2026)
- Gary Lineker → athletes
- Victoria Beckham → musicians

### NEW: Added to "Other" Category (Feb 25, 2026)
- Volodymyr Zelenskyy, Tony Blair, Barack Obama, Joe Biden
- Boris Johnson, Rishi Sunak, Keir Starmer, Nigel Farage
- Elon Musk, Jeff Bezos, Mark Zuckerberg, Bill Gates

### NEW: Banned Streamers/YouTubers (Feb 25, 2026)
**Removed from search results**:
- Ninja, PewDiePie, Shroud, Callux, KSI, Logan Paul, Jake Paul, MrBeast, etc.
**Filter active in**: `/api/autocomplete` endpoint

### NEW: FAQ About Deceased Celebrities (Feb 25, 2026)
**Added FAQ item**: "Why are deceased celebrities still in the game?"
- Explains posthumous scandals, documentaries, estate drama
- Mentions Brown Bread Bonus (+100 points)

### NEW: Periodic Bio Updates from Wikipedia (Feb 25, 2026)
**Feature**: Automatic celebrity bio updates from Wikipedia
- Created `/api/admin/update-bios` endpoint for manual batch updates
- Added scheduled task running daily at 4 AM UTC
- Throttled API calls (0.5-1 second delay) to avoid rate limiting
- Updates celebrities with short/generic bios with real Wikipedia intros
**Progress**: 140+ bios updated, ~200 remaining

### Admin Endpoints Added (Feb 25, 2026)
- `POST /api/admin/add-celebrity` - Add any celebrity with proper tier/price/image
- `POST /api/admin/add-royals` - Add Prince Harry, King Charles, Prince William
- `POST /api/admin/add-celebrities-bulk` - Add multiple celebrities to a category
- `POST /api/admin/move-category` - Move celebrity to different category
- `POST /api/admin/remove-celebrity` - Remove a celebrity by name
- `POST /api/admin/remove-streamers` - Remove all banned streamers/YouTubers
- `POST /api/admin/update-bios` - Batch update celebrity bios from Wikipedia
- `POST /api/admin/refresh-hot-celebs` - Force refresh hot celebs cache

---

## Previous Updates (Feb 24, 2026 - Session 5)

### FEATURE: Disambiguation Search Results (Feb 24, 2026)
**Problem**: Searching for "james morrison" only returned 1 result, but there are multiple celebrities with that name (singer, footballer, actor, etc.)
**Fix Applied**:
- Modified search to return up to 5 results for disambiguation cases (names with parentheses like "James Morrison (singer)")
- Fixed duplicate detection to allow different people with same base name through
- Now users can choose the correct celebrity from the list
**Verified Results**:
- "james morrison" → 5 results: jazz musician (C), singer (B), footballer (B), actor (C), golfer (D) ✅

### FEATURE: Fuzzy Search for Spelling Variations (Feb 24, 2026)
**Problem**: Common misspellings like "Bryan" vs "Brian", "Steven" vs "Stephen" would fail to find results
**Fix Applied**:
- Added SPELLING_VARIATIONS dictionary with 40+ common name spelling variations
- Search automatically tries alternate spellings when no results found
**Examples**:
- "bryan mcfadden" → Brian McFadden ✅
- "stephen spielberg" → Steven Spielberg ✅
- "katy perry" (direct) → Katy Perry ✅

### OPTIMIZATION: Search Speed Improvements (Feb 24, 2026)
**Problem**: Search was slow (2+ seconds)
**Fixes Applied**:
- Moved hot_celebs_cache lookup outside the loop (fetch once instead of per result)
- Removed artificial delays (asyncio.sleep) from Wikidata lookups
- Search now typically completes in under 1 second

### BUG FIX: Search Failing for Names with "Mc/Mac" Prefixes (Feb 24, 2026)
**Problem**: Searching for "bryan mcfadden" returned no results
**Root Cause**: The keyword filter list included "fc", "cf", "afc" (meant for sports teams) but these matched inside names like "McFadden" because the check was substring-based (`kw in title_lower`).
**Fix Applied**:
- Replaced substring matching for sports abbreviations with regex word-boundary checking: `r'\b(fc|cf|afc)\b'`
- This correctly filters "Barcelona FC", "Real Madrid CF", "AFC Bournemouth" while allowing "Brian McFadden", "Bryant McFadden", "MacFarlane" through
**Verified Results**:
- "bryan mcfadden" → Brian McFadden (B-List, £4M) ✅
- "bryant mcfadden" → Bryant McFadden ✅
- "barcelona fc" → 0 results (correctly filtered) ✅

---

## Previous Updates (Feb 24, 2026 - Session 4)

### NEW FEATURE: Hot Streaks (Feb 24, 2026)
**Feature**: Track celebrities with 3+ consecutive days of news mentions
- In-app alerts for celebrities with hot streaks (5+ days)
- New `/api/hot-streaks` endpoint
- Visual indicator with streak days and news article count
- Auto-dismissible alerts stored in sessionStorage

### FIX: Celebrity Image Issues (Feb 24, 2026)
**Problem**: Lady Gaga, Madonna, Post Malone, The Weeknd showing placeholder images
**Fix**: 
- Enhanced alias matching to prefer fresh Wikidata images over stale DB cache
- Added aliases for Madonna, Post Malone, The Weeknd
- PRIORITY 2 alias logic now replaces DB matches when Wikidata has fresher images

### FIX: Category Corrections (Feb 24, 2026)
- Zooey Deschanel → tv_actors (New Girl)
- Anthony Head → tv_actors (Buffy, Merlin)

### FIX: National Team Athletes Tier Boost (Feb 24, 2026)
**Problem**: England rugby players and other national team athletes showing as D-list
**Fix**: Added national team indicators that boost D-list athletes to minimum C-list:
- "national team", "international caps", "six nations", "rugby union international"
- "premier league", "la liga", "champions league", "olympics", etc.

### IMPROVEMENT: Varied A-List Pricing (Feb 24, 2026)
**Problem**: All A-list celebrities were £15M
**Fix**: Dynamic pricing based on language count within each tier:
- A-LIST: £10M - £15M (120+ langs = £15M, 90+ = £13M, 75+ = £11M, else £10M)
- B-LIST: £4M - £6.9M
- C-LIST: £1.5M - £2.9M  
- D-LIST: £0.5M - £1M

**Examples**:
- Taylor Swift (153 langs): £15M
- Ed Sheeran (88 langs): £11M
- The Weeknd (74 langs): £10M

---

## Previous Updates (Feb 24, 2026 - Session 3)

### BUG FIX: Duplicate Search Results for Aliased Names (Feb 24, 2026)
**Problem**: Searching for "zoe saldana" returned TWO results:
- "Zoe Saldana" (D-List, 0 recognition score) - incorrect stale DB match
- "Zoe Saldaña" (A-List, 76 languages) - correct Wikipedia data

**Root Cause**: The duplicate detection logic used simple `.lower()` comparison which treated "Zoe Saldana" and "Zoe Saldaña" as different strings due to the accented character.

**Fix Applied**:
1. Added `normalize_text()` function (removes accents using unicodedata) to duplicate checks
2. Modified PRIORITY 2 alias matching to REPLACE stale DB matches when fresh Wikipedia data has a higher recognition score
3. Updated final duplicate removal to use normalized names for proper deduplication

**Code Changes**:
- `/app/backend/server.py`: Lines 3556-3600 (alias matching with replacement logic)
- `/app/backend/server.py`: Lines 3708-3717 (duplicate removal with normalization)

**Verified Results**:
- "zoe saldana" → 1 result: Zoe Saldaña (A-List, 76 langs, £15M) ✅
- "diddy" → 1 result: Sean Combs (A-List, 62 langs) ✅
- "p diddy" → 1 result: Sean Combs (A-List, 62 langs) ✅
- "richard gere" → Richard Gere first (A-List, 78 langs) ✅
- "mario" → Mario (American singer) first ✅
- "oscar nunez" → Oscar Nunez (C-List, 21 langs) ✅

---

## Previous Updates (Feb 24, 2026 - Session 2)

### CRITICAL FIX: Tier/Price Consistency (Feb 24, 2026)
**Problem**: Celebrities were showing mismatched tiers and prices across different endpoints (e.g., D-List with £5.9M price, A-List celebrities showing as C-List).

**Root Cause**: Multiple tier calculation functions existed with different logic:
- `calculate_tier_and_price()` - Language count based (CORRECT)
- `determine_tier_from_bio()` - Bio length estimation (INCORRECT)
- `calculate_tier_from_wikipedia_data()` - Recognition score model (DIFFERENT RESULTS)

**Fix Applied**:
1. Created new async `get_tier_and_price_from_wikidata()` function as SINGLE SOURCE OF TRUTH
2. Replaced ALL tier/price calculations in:
   - `/api/autocomplete` endpoint (DB-cached celebs)
   - `/api/celebrity/search` endpoint (existing celebs AND new celebs)
   - `/api/trending` endpoint
   - `/api/celebrities/category/{category}` endpoint
   - Search alias matching
3. Fixed award detection to only trigger for WINNERS, not nominees

**New Helper Functions Added**:
- `get_wikidata_language_count(name)` - Fetches language count from Wikidata API
- `get_tier_and_price_from_wikidata(name, bio)` - Single source of truth for tier/price

### Award Detection Fix (Feb 24, 2026)
**Problem**: Michael B. Jordan was incorrectly A-LIST because his bio mentions "nominations for an academy award" which triggered the award check.

**Fix**: Changed `major_awards` list to `major_award_patterns` that requires WINNER-specific keywords:
- "won an academy award", "academy award winner", "oscar winner", "oscar-winning"
- "grammy winner", "grammy-winning", "won a grammy"
- "emmy winner", "emmy-winning", "won an emmy"
- "golden globe winner", "won a golden globe"
- etc.

### TV Presenter Classification (Feb 24, 2026)
Added logic to properly classify TV presenters:
- If "television presenter", "TV host", or "broadcaster" appears
- AND no major acting credits exist
- Classify as `tv_personalities` category

### Pink (Singer) Wiki Link Fix (Feb 24, 2026)
Added "pink" alias mapping to `CELEBRITY_ALIASES`:
- "pink" → "Pink (singer)"
- "p!nk" → "Pink (singer)"
- "pink singer" → "Pink (singer)"
- "alecia moore" → "Pink (singer)"

### Category Cards Fix (Feb 24, 2026)
Updated `/api/celebrities/category/{category}` endpoint to:
- Recalculate tier/price for each celebrity using `get_tier_and_price_from_wikidata()`
- Ensures category cards show consistent tier badges with search results

### Tier Calculation System (Simplified Feb 24, 2026)

**SINGLE SOURCE OF TRUTH:** `calculate_tier_and_price()` function

**LAYER 1 - Language Count (Primary):**
- A-LIST: 60+ Wikipedia languages (global superstars)
- B-LIST: 25-59 languages (internationally recognized)
- C-LIST: 10-24 languages (nationally known)
- D-LIST: <10 languages (emerging/niche)

**LAYER 2 - Achievement Modifiers (+1 tier upgrade):**
- Global franchise lead (Harry Potter, Marvel, Star Wars, etc.)
- Major international award WINNER (Oscar, Grammy, Emmy, etc.)
- World champion/record holder

**LAYER 3 - Reality TV Modifier (-1 tier downgrade):**
- Reality TV without other achievements (unless 40+ languages)

**Pricing:**
- A-LIST: £15M base (updated from £12M)
- B-LIST: £6M base
- C-LIST: £2.5M base
- D-LIST: £1M base

**Verified Results (All Tests Passed):**
- Daniel Radcliffe: A-LIST (101 langs, Harry Potter) £15M ✅
- Michael B. Jordan: B-LIST (55 langs, nominated but NOT won Oscar) £6.9M ✅
- Rochelle Humes: C-LIST (13 langs) £2.5M ✅
- Pink (singer): A-LIST (78 langs) £15M ✅
- Kelly Osbourne: B-LIST (35 langs) £6.9M ✅
- Sharon Osbourne: B-LIST (33 langs) £6M ✅
- Ray J: B-LIST (now searchable!) £6M ✅
- Sean Combs (P Diddy): A-LIST (now searchable via multiple aliases) £15M ✅
- Mario (singer): A-LIST (now searchable!) £15M ✅

### Bug Fixes (Feb 24, 2026)
- ✅ **apply_brown_bread_premium → get_brown_bread_premium** - Fixed NameError in celebrity search endpoint
- ✅ **Removed duplicate fetch_wikipedia_info function** - Cleaned up leftover code from refactoring
- ✅ **Restored get_brown_bread_premium function definition** - Missing async def was causing await errors
- ✅ **Hot Celebs List Fixed** - Added 20+ missing celebrities to KNOWN_CELEBRITIES list
- ✅ **Hot Celebs Now Shows Real News** - Banner now displays celebrities with 3+ actual news mentions

## Previous Updates (Feb 23, 2026)

### Search Price/Tier Mismatch Fix (Feb 23, 2026)
- ✅ **Fixed autocomplete price inconsistency** - Autocomplete endpoint was using wrong cache type (`hot_celebs`) instead of correct one (`hot_celebs_from_news_v4`)
- ✅ **Hot celeb premium pricing in autocomplete** - Now applies premium pricing to partial matches in autocomplete, not just exact matches
- ✅ **Verified mobile view in preview** - Mobile rendering working correctly with proper responsive layout
- ✅ **Search debounce already reduced** - Was set to 150ms (previously 300ms) for faster response

### Image Fix - Wikidata Priority (Feb 23, 2026)
- ✅ **Paris Hilton and Rafael Nadal images fixed** - Updated to use reliable Wikidata Commons URLs
- ✅ **Improved image fetching logic** - Now prioritizes Wikidata P18 images over Wikipedia thumbnails (avoids 429 rate limits)
- ✅ **Proper URL encoding** - Fixed URL encoding for Wikimedia Commons Special:FilePath URLs

### Price Watch Feature (NEW - Feb 23, 2026)
- ✅ **Backend API endpoints** - GET/POST/DELETE for price watches
- ✅ **Team-based tracking** - Each team can watch up to 10 celebrities
- ✅ **Alert types** - Watch for price drops OR price rises
- ✅ **Target notifications** - Shows when target price is reached
- ✅ **Frontend modal** - Beautiful UI with celebrity search, tier badges, current/target prices
- ✅ **Pro tip guidance** - Helpful tips for using price watches effectively

### Data Quality Fixes (Feb 23, 2026 - Session 2)
- ✅ **Adele image fixed** - Updated Wikipedia image URL (was returning 429 rate limit)
- ✅ **Dua Lipa image fixed** - Updated Wikipedia image URL (was returning 429 rate limit)
- ✅ **Damian Lewis category fixed** - Changed from `tv_actors` to `movie_stars` (bio says "actor and musician" - actor comes first)
- ✅ **Transfer Window banner fixed** - Changed from "Sat 12pm" to "Sun 12pm" in HowItWorks.jsx
- ✅ **Keanu Reeves verified** - Already correctly classified as `movie_stars`

### Friends League Feature (NEW!)
- ✅ **Create Leagues**: Users can create private leagues with up to 10 friends
- ✅ **Join via Code**: 6-character invite codes for easy sharing
- ✅ **Weekly Leaderboard**: Track weekly standings within your league
- ✅ **Monthly Leaderboard**: Accumulated monthly standings
- ✅ **League Chat**: Real-time chat with friends in your league (with profanity filter)
- ✅ **Badge System**: Awards for weekly/monthly winners
  - 🏆 Weekly Champion - Won a weekly league competition
  - 🌟 Monthly Master - Won a monthly league competition  
  - 👑 League Legend - Won 3+ weeks in your league
  - 💪 Undefeated - Won 4 weeks in a row
  - 🎯 League Founder - Created a league with 5+ members
- ✅ **Share to Social**: WhatsApp, X (Twitter), Facebook sharing
- ✅ **League Stats**: Weeks played, total celebs, most decorated team

### Automated Tier Classification System (NEW!)
- ✅ **Wikipedia Language Editions**: More languages = global recognition
  - 80+ languages → A-list
  - 50-80 languages → High recognition
  - 30-50 languages → International
  - <30 languages → Limited recognition
- ✅ **Years Active**: Career longevity detection
- ✅ **Award Scoring**: Detects Oscars, Grammys, Emmys, Olympic medals, etc.
- ✅ **Career Quality Detection**:
  - Reality TV/Influencer → Lower tier (-10 to -15 points)
  - Box office/Blockbuster → Higher tier (+15-20 points)
  - Royal/Political status → A-list automatic (+30-40 points)
- ✅ **Admin Endpoints**:
  - `POST /api/admin/reclassify-tiers` - Batch reclassify all celebrities
  - `GET /api/admin/test-tier-calculation/{name}` - Test tier for specific celebrity

### Automated Schedulers
- ✅ **Daily Points Update**: 23:00 UTC - Updates team points daily
- ✅ **Weekly League Scoring**: Sunday 23:59 UTC - Records weekly winners, awards badges
- ✅ **Monthly League Winner**: 1st of month 00:30 UTC - Crowns monthly champion
- ✅ **Weekly Price Reset**: Monday 00:00 UTC - Updates celebrity prices

### Celebrity Tier Fixes
- ✅ Adam Sandler: A-list £10M (was C-list)
- ✅ Debbie Harry: B-list £6M (newly added)
- ✅ Simone Biles: A-list £10M (was D-list)
- ✅ Andrew Garfield: A-list £10M
- ✅ Harry Styles: A-list £12M
- ✅ Michael B. Jordan: Added to hot celebs pool (A-list)
- ✅ Andrew Mountbatten-Windsor: Kept (removed "Prince Andrew" duplicate)

### UI/UX Improvements
- ✅ Celebrity card bio overlay redesigned - smaller and positioned at bottom
- ✅ Bio text reduced to 2 lines with smaller font
- ✅ Celebrity faces now fully visible
- ✅ Wikipedia links restored on all cards

### Data Updates
- ✅ Charlie Kirk moved to `public_figure` category
- ✅ JoJo Siwa added as B-list (£6M) in reality_tv
- ✅ Stacey Solomon moved to reality_tv
- ✅ Removed 5 duplicate celebrities (Beyoncé, Drake, etc.)
- ✅ Added 17 UK Reality TV and TV stars with images

## Backend Architecture (Updated Feb 23, 2026)
```
/app/backend/
├── server.py          # Main FastAPI app (5080 lines - reduced from 5488)
├── config/
│   ├── __init__.py
│   ├── database.py    # MongoDB connection, env vars (30 lines)
│   └── settings.py    # Configuration settings
├── data/
│   ├── __init__.py    # Data exports
│   ├── celebrity_data.py  # Celebrity pools, A-list definitions, aliases (441 lines)
│   └── constants.py   # Banned words, pricing config, team options (85 lines)
├── models/
│   ├── __init__.py    # Model exports
│   ├── celebrity.py   # Celebrity Pydantic models
│   ├── team.py        # Team models
│   ├── league.py      # League models
│   └── auth.py        # Auth models (User, UserSession, MagicLinkRequest, etc.)
├── routes/            # Modular API routes
│   ├── __init__.py    # Route exports
│   ├── auth.py        # ✅ MIGRATED: Auth routes (449 lines)
│   ├── celebrities.py # Template (pending migration)
│   ├── teams.py       # Template (pending migration)
│   ├── leagues.py     # Template (pending migration)
│   └── admin.py       # Template (pending migration)
├── services/          # (Future: extract business logic)
└── utils/
    ├── __init__.py
    └── helpers.py     # normalize_text, decode_html_entities, sanitize_team_name
```

**Completed Refactoring:**
- ✅ Phase 1: Extracted celebrity data pools (9 categories, 50+ celebs each)
- ✅ Phase 1: Extracted constants (banned words, pricing tiers, team options)
- ✅ Phase 1: Extracted utility functions (text normalization, HTML decoding)
- ✅ Phase 1: Created Pydantic models in separate files
- ✅ Phase 2: **AUTH ROUTES MIGRATED** (Feb 22, 2026):
  - Moved all auth endpoints to `/routes/auth.py`
  - Includes: /api/auth/me, magic-link/send, magic-link/verify, google/callback, guest/convert, logout, session
  - Server.py reduced by ~408 lines
  - Uses shared database config from `/config/database.py`

**Remaining Refactoring (Phase 3 - Future):**
- Migrate celebrity routes (search, categories, hot celebs) to `/routes/celebrities.py`
- Migrate team routes to `/routes/teams.py`
- Migrate league routes to `/routes/leagues.py`
- Migrate admin routes to `/routes/admin.py`
- Extract business logic into services/

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
- ✅ **MASS WIKIDATA UPDATE** (Feb 23, 2026):
  - **1,605 celebrities now have real Wikipedia images** (82.6% coverage)
  - Automated Wikidata API integration fetches P18 (image) and P106 (occupation)
  - 339 celebrities remain with placeholder images (no Wikidata images available)
- ✅ **WIKIPEDIA BIO & CATEGORY FIX** (Feb 23, 2026):
  - All celebrities now have real Wikipedia bios (replaced generic "is a celebrity" text)
  - Categories based on **FIRST OCCUPATION** from Wikipedia description
  - Smart parsing: "is an American singer-songwriter" → musicians
  - Handles edge cases: "Queen of Country" doesn't trigger royals, "sex tape with singer Ray J" doesn't make Kim K a musician
  - Only actual royal family members (Prince of Wales, Duke of Sussex, etc.) are categorized as royals
  - Final category distribution: movie_stars (427), athletes (291), musicians (279), royals (254), reality_tv (211), public_figure (193), other (184), tv_personalities (102), tv_actors (3)
  - Admin endpoint: `/api/admin/fix-celebrity-bios`
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
- ✅ **News Fetching Fix - COMPLETED Feb 22, 2026**
  - Fixed name-matching algorithm in `fetch_real_celebrity_news`
  - Removed overly-restrictive "ambiguous_last_names" blocklist
  - Added word-boundary matching to avoid false positives
  - Added celebrity-specific aliases (e.g., "Cheryl Cole" → "Cheryl", "Gemma Collins" → "The GC")
  - Added URL extraction from RSS feeds for clickable news links
  - Added sports RSS feeds (Sky Sports, BBC Sport, ESPN, Goal)
  - Test results: 100% of major celebrities now return news articles
- 🔄 Hot Streak Notifications - Backend ready, needs full UI

### P1 (High Priority)
- User authentication for persistent teams
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

