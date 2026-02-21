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

**Dynamic Pricing**: Prices fluctuate weekly based on media coverage. Hot celebs in the news cost more, quiet celebs cost less.

## Transfer Window
- **Opens**: Every Saturday at 12:00 GMT
- **Duration**: 24 hours
- **Closes**: Sunday at 12:00 GMT
- 1 transfer per week allowed during window

## Architecture

### Backend (FastAPI + MongoDB)
- `/api/stats` - Player count and transfer window status (NO celebrity count)
- `/api/pricing-info` - Tier pricing information and strategy guide
- `/api/hot-celebs` - Hot celebrities RANDOMIZED on each refresh with real photos
- `/api/price-alerts/{team_id}` - Price change alerts for team's celebrities
- `/api/hot-streaks/{team_id}` - Hot streak notifications (3+ days in news)
- `/api/autocomplete?q=` - Wikipedia search with advanced filtering
- `/api/todays-news` - Major celebrity news (filtered for quality, HTML entities decoded)
- `/api/trending` - Trending celebrities with CORRECT dynamic pricing
- `/api/leaderboard` - Team rankings
- `/api/team/*` - Team management endpoints
- `/api/league/*` - Friends league endpoints
- `/api/hall-of-fame` - Top players with badges
- `/api/brown-bread-watch` - Elderly celebrities with risk levels

### UI Layout (Top to Bottom)
1. Stats Banner (Player count + Transfer window countdown)
2. Header
3. Trending Ticker (with PRICES not points)
4. How It Works
5. **Search Bar** (with helper text below)
6. **Category Filter** (directly under search)
7. Hot Celebs This Week (randomized)
8. Today's Top Celeb News
9. Celebrity Grid + Sidebar

### Sidebar Components
1. Team Panel
2. League Panel
3. **Price Alerts** (upcoming price changes)
4. **Hot Streaks** (3+ days in news notifications)
5. Top Picked Celebs
6. Brown Bread Watch
7. Leaderboard
8. Hall of Fame button

## What's Been Implemented (Feb 2026)

### Core Features
- ✅ Full FastAPI backend with all endpoints
- ✅ Wikipedia autocomplete search with advanced filtering
- ✅ A/B/C/D tier system with DYNAMIC pricing
- ✅ Saturday 12pm GMT transfer window (24 hours)
- ✅ Brown Bread Bonus (+100 for deceased)
- ✅ Price alerts system
- ✅ Hot streak notifications (3+ days in news)
- ✅ Profanity filter for team names

### UI Features
- ✅ Scrolling banner shows PRICE (correct for tier ranges)
- ✅ Category filter moved UNDER search bar
- ✅ Search helper text: "Search for any celebrity or select a category below"
- ✅ Hot Celebs RANDOMIZED on each refresh with real Wikipedia photos
- ✅ News headlines cleaned (HTML entities decoded)
- ✅ Price Alerts panel in sidebar
- ✅ Hot Streaks panel in sidebar
- ✅ Mobile responsive design

### Social Features
- ✅ Team sharing (WhatsApp, X, Facebook)
- ✅ League sharing (WhatsApp, X, Facebook)
- ✅ Friends League system with invite codes
- ✅ Badge/achievement system
- ✅ Hall of Fame

## Hot Celebs Pool (30+ celebrities)
Randomized from pool including:
- **Royals**: Prince Andrew, Meghan Markle, Prince Harry, Kate Middleton, King Charles III
- **Musicians**: Kanye West, Taylor Swift, Beyoncé, Drake, Rihanna, Ed Sheeran, Adele
- **Tech/Business**: Elon Musk, Mark Zuckerberg, Jeff Bezos
- **Politicians**: Donald Trump, Joe Biden
- **Reality TV/UK**: Katie Price, Holly Willoughby, Phillip Schofield, Gemma Collins, Kerry Katona
- **Actors**: Tom Cruise, Leonardo DiCaprio, Jennifer Lawrence, Brad Pitt, Angelina Jolie
- **Sports**: Cristiano Ronaldo, David Beckham, Lewis Hamilton

## Bug Fixes (Feb 2026)
- ✅ Fixed scrolling banner prices to use correct tier ranges
- ✅ Fixed trending endpoint to recalculate dynamic prices
- ✅ Moved category filter under search bar
- ✅ Fixed HTML entities in news headlines
- ✅ Hot celebs randomized on each refresh

## Backlog / Future Features

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
