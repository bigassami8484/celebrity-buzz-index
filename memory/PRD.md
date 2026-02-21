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
- `/api/hot-celebs` - Hot celebrities with REAL Wikipedia photos
- `/api/autocomplete?q=` - Wikipedia search with advanced filtering
- `/api/todays-news` - Major celebrity news (filtered for quality)
- `/api/leaderboard` - Team rankings
- `/api/team/*` - Team management endpoints
- `/api/league/*` - Friends league endpoints
- `/api/hall-of-fame` - Top players with badges
- `/api/brown-bread-watch` - Elderly celebrities with risk levels

### Search Filtering (Wikipedia Autocomplete)
Filters OUT:
- Albums, songs, films, TV shows
- Locations (cities, capitals like Mariehamn)
- Sports teams (IFK, FC, AFC, United, City)
- Football/soccer clubs
- Plants, animals, objects
- Non-celebrities

### Points Calculation
- News Mentions: +1.0 point per article
- Tabloid Coverage: +3.0 points (Daily Mail, Sun, TMZ)
- Broadsheet Coverage: +2.0 points (BBC, Guardian, Times)
- Controversy Bonus: +25.0 points per scandal
- Social Media Trending: +5.0 points per event
- **Brown Bread Bonus: +100 points** if celebrity passes away
- **Minimum Buzz Score: 5 points**
- **Tier Multipliers**: A=1.0x, B=1.2x, C=1.5x, D=2.0x

### Team Rules
- **Budget: £50M**
- **Max team size: 10 players**
- **1 transfer per week** (during Saturday window)

## What's Been Implemented (Feb 2026)

### Core Features
- ✅ Full FastAPI backend with all endpoints
- ✅ Wikipedia autocomplete search with advanced filtering
- ✅ Accent-normalized search (Beyoncé, Rihanna work without accents)
- ✅ A/B/C/D tier system with DYNAMIC pricing
- ✅ Saturday 12pm GMT transfer window (24 hours)
- ✅ Controversial celebrity price boosts
- ✅ Brown Bread Bonus (+100 for deceased)
- ✅ Minimum buzz score of 5 points
- ✅ Profanity filter for team names

### UI Features
- ✅ Player count banner (removed celebrity count)
- ✅ Transfer window countdown
- ✅ Hot Celebs This Week banner with REAL Wikipedia photos
- ✅ Today's Top Celeb News (major news only, no gossip)
- ✅ Search bar positioned ABOVE news section
- ✅ Pricing tier info in methodology modal
- ✅ Mobile responsive design with bottom navigation

### Social Features
- ✅ Team sharing (WhatsApp, X, Facebook)
- ✅ League sharing (WhatsApp, X, Facebook)
- ✅ Friends League system with invite codes
- ✅ Badge/achievement system
- ✅ Hall of Fame

## Bug Fixes (Feb 2026)
- ✅ Fixed search returning plants (Holly genus)
- ✅ Fixed search returning locations (Mariehamn)
- ✅ Fixed search returning sports teams (IFK Mariehamn)
- ✅ Fixed "is a bar" substring false positive
- ✅ Fixed route ordering for customization-options endpoint
- ✅ Added accent normalization for celebrity names
- ✅ Removed celebrity count from stats banner
- ✅ Updated pricing display throughout app

## News Sources
- BBC News (priority - major news)
- The Guardian (priority - major news)
- TMZ
- People
- Page Six
- Daily Mail

News is filtered for MAJOR stories (deaths, divorces, awards, legal battles, scandals) and skips gossip.

## Hot Celebs This Week
Currently featuring with REAL Wikipedia photos:
- Prince Andrew (Royal scandal & legal battles)
- Meghan Markle (Netflix & Royal drama)
- Kanye West (Controversy & headlines)
- Taylor Swift (Eras Tour & awards)
- Elon Musk (Tech & politics headlines)
- Donald Trump (Political & legal news)
- Katie Price (Tabloid regular)
- Holly Willoughby (TV drama)

## Backlog / Future Features

### P1 (High Priority)
- User authentication for persistent teams
- Real news API integration (NewsAPI)
- Automated weekly badge awards
- Refresh hot celebs based on current news

### P2 (Medium Priority)
- Celebrity comparison feature
- Historical buzz trends chart
- Push notifications
- Price history tracking

### P3 (Nice to Have)
- Dark/light mode toggle
- Mobile app version
- Celebrity draft mode (turn-based picking)
