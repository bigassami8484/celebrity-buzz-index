# Celebrity Buzz Index - Product Requirements Document

## Original Problem Statement
Build a Celebrity Buzz Index fantasy-league style platform where users can:
- Search ANY celebrity worldwide with a Wikipedia page
- View AI-generated news coverage and Wikipedia info
- Calculate "buzz points" based on media mentions
- Build teams with a £50M budget
- Compete on leaderboards with friends
- Social sharing (Twitter/X, Facebook, WhatsApp)

**Latest Requirements:**
- Price fluctuations based on controversy (Prince Andrew costs more)
- "Brown Bread Bonus" (+100 points if celebrity dies)
- "Brown Bread Watch" - elderly celebrities with risk indicators
- Weekly transfer window (1 swap per week)
- Today's Top Celeb News section
- Player count display
- Ban racist/offensive team names
- Top Picked Celebrities section
- A/B/C/D list tiers with tiered pricing
- Friends League system with invite codes
- Mobile responsive design

## Architecture

### Backend (FastAPI + MongoDB)
- `/api/categories` - Get all celebrity categories
- `/api/autocomplete?q=` - Wikipedia autocomplete search (filters for real people only)
- `/api/points-methodology` - Get points calculation explanation
- `/api/stats` - Player count, celebrity count, transfer window
- `/api/todays-news` - Real celebrity news from RSS feeds
- `/api/top-picked` - Most picked celebrities
- `/api/brown-bread-watch` - Elderly celebrities with risk levels
- `/api/trending` - Get trending celebrities with tiers
- `/api/celebrity/search` - Search and create celebrity profile
- `/api/celebrities/category/{category}` - Get celebrities by category
- `/api/team/create` - Create new team (with profanity filter)
- `/api/team/add` - Add celebrity to team (with Brown Bread Bonus)
- `/api/team/transfer` - Weekly transfer (sell one, buy one)
- `/api/team/remove` - Remove celebrity from team
- `/api/team/{team_id}/leagues` - Get leagues team belongs to
- `/api/leaderboard` - Get team rankings
- `/api/league/create` - Create friends league
- `/api/league/join` - Join league with code
- `/api/league/{id}/leaderboard` - League-specific leaderboard

### Celebrity Tier & Pricing System
- **A-LIST** (£18-22M): Oscar/Grammy winners, legendary status
- **B-LIST** (£12-16M): Award-winning, chart-topping
- **C-LIST** (£7-11M): Known for appearances
- **D-LIST** (£3-6M): Everyone else
- **Controversial Boost**: Prince Andrew £12M, Trump/Elon £15M, etc.

### Points Calculation
- News Mentions: +1.0 point per article
- Tabloid Coverage: +3.0 points (Daily Mail, Sun, TMZ)
- Broadsheet Coverage: +2.0 points (BBC, Guardian, Times)
- Controversy Bonus: +25.0 points per scandal
- Social Media Trending: +5.0 points per event
- **Brown Bread Bonus: +100 points** if celebrity passes away
- **Minimum Buzz Score: 5 points** (no celebrity scores below 5)
- **Tier Multipliers**: A=1.0x, B=1.2x, C=1.5x, D=2.0x

### Pricing (Updated)
- **A-list: £9M** (celebrities with major awards, billions in earnings)
- **B-list: £6M** (award-winning, chart-topping)
- **C-list: £4M** (TV appearances, reality stars)
- **D-list: £2M** (everyone else)

### Team Rules
- **Budget: £50M**
- **Max team size: 10 players**
- **1 transfer per week**

### Features
- **Player Count Banner**: Shows total players, celebrities, transfer window
- **Today's News**: Real celebrity news from TMZ, Daily Mail, BBC, People, E! News, US Weekly, Page Six
- **Transfer Window**: 1 swap per week (resets weekly)
- **Profanity Filter**: Blocks racist/offensive team names
- **Social Sharing**: WhatsApp, Facebook, X/Twitter
- **Top Picked**: Most selected celebrities by players
- **Friends Leagues**: Create leagues with invite codes, compete with friends
- **Badge System**: Weekly Champion 🏆, Trendsetter ⚡, Grim Reaper 💀, Controversy King 🔥, A-List Club ⭐, League Legend 👑

## What's Been Implemented (Feb 20, 2026)
- ✅ Full FastAPI backend with all endpoints
- ✅ Wikipedia autocomplete search - filters out albums, films, TV shows, fictional characters
- ✅ A/B/C/D tier system with tiered pricing
- ✅ Controversial celebrity price boosts
- ✅ Brown Bread Bonus (+100 for deceased)
- ✅ Controversy Bonus (+25 points per scandal)
- ✅ Minimum buzz score of 5 points
- ✅ Player count banner
- ✅ Today's Top Celeb News (real RSS feeds from TMZ, Daily Mail, BBC, People, E! News, US Weekly, Page Six, Guardian)
- ✅ Top Picked Celebrities section
- ✅ Transfer window (1 per week)
- ✅ Profanity filter for team names
- ✅ Social sharing (WhatsApp/Facebook/X)
- ✅ Points methodology modal
- ✅ React frontend with Tailwind styling
- ✅ Friends League system with invite codes
- ✅ Badge/achievement system
- ✅ Mobile responsive design with bottom navigation

## Bug Fixes (Dec 2025)
- ✅ Fixed missing pictures in autocomplete - added explicit fallback to ui-avatars.com placeholder
- ✅ Updated minimum base points to 5 (was 10, now enforces min 5)
- ✅ Updated Brown Bread Bonus to +100 in UI (was showing +50)

## New Features (Dec 2025)
- ✅ **Brown Bread Watch** - Strategic sidebar showing elderly celebrities (60+) with risk indicators
  - 🔴 Critical (90+), 🟠 High (80-89), 🟡 Elevated (70-79), 🟢 Moderate (60-69)
  - Grayscale photos, age display, click-to-search integration
  - Extracts birth year from Wikipedia's wikibase-shortdesc API
- ✅ **Friends League System** - Compete with friends
  - Create leagues with auto-generated 6-char invite codes
  - Join leagues by entering code
  - League-specific leaderboards
  - WhatsApp sharing for league invites
- ✅ **Mobile Responsive Design**
  - Bottom navigation bar (Home, Team, Leagues)
  - Responsive CSS for all screen sizes
  - Touch-friendly interface
- ✅ **Improved Celebrity Search**
  - Filters out non-person results (films, albums, shows)
  - Removes duplicates (only one result per celebrity)
  - Filters out fictional characters
  - Uses Wikipedia Search API for better results

## Backlog / Future Features

### P1 (High Priority)
- User authentication for persistent teams
- Real news API integration (NewsAPI)
- Weekly buzz score updates

### P2 (Medium Priority)
- Celebrity comparison feature
- Historical buzz trends chart
- Push notifications

### P3 (Nice to Have)
- Dark/light mode toggle
- Mobile app version
- Achievement badges
