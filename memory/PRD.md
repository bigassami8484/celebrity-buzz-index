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
- ✅ Wikipedia autocomplete search with **ADVANCED FILTERING** (no locations, places, films, universities, awards)
- ✅ A/B/C/D tier system with STRICT dynamic pricing (max £12M)
- ✅ Saturday 12pm GMT transfer window (24 hours)
- ✅ Brown Bread Watch with PREMIUM pricing (top 3 up to £15M)
- ✅ Price alerts system
- ✅ Hot streak notifications (3+ days in news)
- ✅ Profanity filter for team names

### UI Features
- ✅ Scrolling banner shows CORRECT tier-based prices
- ✅ "Select a category or search for any celebrity" helper text (gold, under search)
- ✅ Category filter directly under search bar
- ✅ Hot Celebs RANDOMIZED on each refresh with real Wikipedia photos
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
