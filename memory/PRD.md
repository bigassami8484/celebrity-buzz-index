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
- `/api/autocomplete?q=` - Wikipedia search with advanced filtering
- `/api/todays-news` - Major celebrity news (filtered for quality, HTML entities decoded)
- `/api/leaderboard` - Team rankings
- `/api/team/*` - Team management endpoints
- `/api/league/*` - Friends league endpoints
- `/api/hall-of-fame` - Top players with badges
- `/api/brown-bread-watch` - Elderly celebrities with risk levels

### Search Filtering (Wikipedia Autocomplete)
Filters OUT:
- Albums, songs, films, TV shows
- Locations (cities, capitals like Mariehamn, Helsinki)
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
- ✅ Price alerts system for team's celebrities

### UI Features
- ✅ Player count banner (NO celebrity count)
- ✅ Transfer window countdown
- ✅ Scrolling banner shows PRICE (not points)
- ✅ Hot Celebs This Week - RANDOMIZED on each refresh with REAL photos
- ✅ Today's Top Celeb News (major news only, HTML entities decoded)
- ✅ Search bar positioned BEFORE news section
- ✅ "Search for any celebrity or select a category below" helper text
- ✅ Pricing tier info in methodology modal
- ✅ Price Alerts panel in sidebar
- ✅ Mobile responsive design with bottom navigation

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
- ✅ Fixed search returning plants (Holly genus)
- ✅ Fixed search returning locations (Mariehamn, capital cities)
- ✅ Fixed search returning sports teams (IFK Mariehamn, football clubs)
- ✅ Fixed "is a bar" substring false positive
- ✅ Fixed route ordering for customization-options endpoint
- ✅ Added accent normalization for celebrity names
- ✅ Removed celebrity count from stats banner
- ✅ Updated pricing display throughout app
- ✅ Fixed HTML entities in news headlines (&amp; → &, &#8217; → ')
- ✅ Replaced points with prices in scrolling banner

## News Sources
- BBC News (priority - major news)
- The Guardian (priority - major news)
- TMZ
- People
- Page Six
- Daily Mail

News is filtered for MAJOR stories (deaths, divorces, awards, legal battles, scandals) and skips gossip.

## Backlog / Future Features

### P1 (High Priority)
- User authentication for persistent teams
- Real news API integration (NewsAPI)
- Automated weekly badge awards
- Refresh hot celebs based on current trending news

### P2 (Medium Priority)
- Celebrity comparison feature
- Historical buzz trends chart
- Push notifications
- Price history tracking

### P3 (Nice to Have)
- Dark/light mode toggle
- Mobile app version
- Celebrity draft mode (turn-based picking)
