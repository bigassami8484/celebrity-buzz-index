# Celebrity Buzz Index - Product Requirements Document

## Original Problem Statement
Build a Celebrity Buzz Index fantasy-league style platform where users can:
- Search ANY celebrity worldwide with a Wikipedia page
- View AI-generated news coverage and Wikipedia info
- Calculate "buzz points" based on media mentions
- Build teams with a £50M budget
- Compete on leaderboards with friends
- Social sharing (Twitter/X, Facebook, WhatsApp)

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

## Transfer Window
- **Opens**: Every Saturday at 12:00 GMT
- **Duration**: 24 hours
- **Closes**: Sunday at 12:00 GMT
- 1 transfer per week allowed during window

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
- ✅ Brown Bread Watch with PREMIUM pricing (top 3 up to £15M)
- ✅ **PRICE HISTORY TRACKING**:
  - MongoDB 'price_history' collection
  - Records price changes automatically
  - API endpoints: `/api/price-history/celebrity-name/{name}`, `/api/celebrity/{id}/price-history`
  - Frontend modal with trend indicators
- ✅ Price alerts system
- ✅ Hot streak notifications (3+ days in news)
- ✅ Profanity filter for team names
- ✅ **CATEGORY DETECTION FIX**: Known actors (Michael Caine, Ian McKellen, Morgan Freeman, etc.) correctly classified as movie_stars
- ✅ **24-HOUR NEWS CACHE** - News feed refreshes every 24 hours (was 15 min)

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
- Refactor App.js into smaller components

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
- 🔄 Hot Streak Notifications - Backend ready, needs full UI

### P1 (High Priority)
- User authentication for persistent teams
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
