# Celebrity Buzz Index - Product Requirements Document

## Original Problem Statement
Build a Celebrity Buzz Index fantasy-league style platform where users can:
- Search ANY celebrity worldwide with a Wikipedia page
- View AI-generated news coverage and Wikipedia info
- Calculate "buzz points" based on media mentions
- Build teams with a £50M budget
- Compete on leaderboards
- Social sharing (Twitter/X, Facebook, WhatsApp)

**Latest Requirements:**
- Price fluctuations based on controversy (Prince Andrew costs more)
- "Brown Bread Bonus" (+50 points if celebrity dies)
- Weekly transfer window (1 swap per week)
- Today's Top Celeb News section
- Player count display
- Ban racist/offensive team names
- Top Picked Celebrities section
- A/B/C/D list tiers with tiered pricing

## Architecture

### Backend (FastAPI + MongoDB)
- `/api/categories` - Get all celebrity categories
- `/api/autocomplete?q=` - Wikipedia autocomplete search
- `/api/points-methodology` - Get points calculation explanation
- `/api/stats` - **NEW** Player count, celebrity count, transfer window
- `/api/todays-news` - **NEW** AI-generated daily celebrity news
- `/api/top-picked` - **NEW** Most picked celebrities
- `/api/trending` - Get trending celebrities with tiers
- `/api/celebrity/search` - Search and create celebrity profile
- `/api/celebrities/category/{category}` - Get celebrities by category
- `/api/team/create` - Create new team (with profanity filter)
- `/api/team/add` - Add celebrity to team (with Brown Bread Bonus)
- `/api/team/transfer` - **NEW** Weekly transfer (sell one, buy one)
- `/api/team/remove` - Remove celebrity from team
- `/api/leaderboard` - Get team rankings

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

### Features
- **Player Count Banner**: Shows total players, celebrities, transfer window
- **Today's News**: 8 AI-generated celebrity headlines
- **Transfer Window**: 1 swap per week (resets weekly)
- **Profanity Filter**: Blocks racist/offensive team names
- **Social Sharing**: WhatsApp, Facebook, X/Twitter
- **Top Picked**: Most selected celebrities by players

## What's Been Implemented (Feb 20, 2026)
- ✅ Full FastAPI backend with all endpoints
- ✅ Wikipedia autocomplete search with fallback images
- ✅ A/B/C/D tier system with tiered pricing
- ✅ Controversial celebrity price boosts
- ✅ Brown Bread Bonus (+100 for deceased)
- ✅ Controversy Bonus (+25 points per scandal)
- ✅ Minimum buzz score of 5 points
- ✅ Player count banner
- ✅ Today's Top Celeb News (real RSS feeds from Daily Mail, BBC, Guardian)
- ✅ Top Picked Celebrities section
- ✅ Transfer window (1 per week)
- ✅ Profanity filter for team names
- ✅ Social sharing (WhatsApp/Facebook/X)
- ✅ Points methodology modal
- ✅ React frontend with Tailwind styling

## Bug Fixes (Dec 2025)
- ✅ Fixed missing pictures in autocomplete - added explicit fallback to ui-avatars.com placeholder
- ✅ Updated minimum base points to 5 (was 10, now enforces min 5)
- ✅ Updated Brown Bread Bonus to +100 in UI (was showing +50)

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
