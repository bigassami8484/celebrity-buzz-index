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
- Today's Top Celeb News section (MAJOR news only, not gossip)
- Hot Celebs This Week banner (big names in headlines)
- Player count display
- Ban racist/offensive team names
- Top Picked Celebrities section
- A/B/C/D list tiers with tiered pricing
- Friends League system with invite codes + social sharing
- Team customization (colors and icons)
- Mobile responsive design

## Architecture

### Backend (FastAPI + MongoDB)
- `/api/categories` - Get all celebrity categories
- `/api/autocomplete?q=` - Wikipedia autocomplete search (filters for real people only)
- `/api/points-methodology` - Get points calculation explanation
- `/api/stats` - Player count, celebrity count, transfer window
- `/api/hot-celebs` - Hot celebrities making headlines this week
- `/api/todays-news` - Real celebrity news from RSS feeds (major news only)
- `/api/top-picked` - Most picked celebrities
- `/api/brown-bread-watch` - Elderly celebrities with risk levels
- `/api/trending` - Get trending celebrities with tiers
- `/api/celebrity/search` - Search and create celebrity profile
- `/api/celebrities/category/{category}` - Get celebrities by category
- `/api/team/create` - Create new team (with profanity filter)
- `/api/team/add` - Add celebrity to team (with Brown Bread Bonus)
- `/api/team/transfer` - Weekly transfer (sell one, buy one)
- `/api/team/remove` - Remove celebrity from team
- `/api/team/customization-options` - Get available colors and icons
- `/api/team/customize` - Update team appearance
- `/api/team/{team_id}/leagues` - Get leagues team belongs to
- `/api/leaderboard` - Get team rankings
- `/api/league/create` - Create friends league
- `/api/league/join` - Join league with code
- `/api/league/code/{code}` - Get league by invite code
- `/api/league/{id}/leaderboard` - League-specific leaderboard
- `/api/hall-of-fame` - Top players with most badges
- `/api/badges` - Available badges

### Celebrity Tier & Pricing System
- **A-LIST** (£9M): Oscar/Grammy winners, legendary status
- **B-LIST** (£6M): Award-winning, chart-topping
- **C-LIST** (£4M): Known for appearances
- **D-LIST** (£2M): Everyone else
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

### Team Rules
- **Budget: £50M**
- **Max team size: 10 players**
- **1 transfer per week**

### Team Customization
- 8 colors: Hot Pink, Electric Blue, Gold, Royal Purple, Fire Red, Emerald, Sunset Orange, Classic White
- 12 icons: ⭐ Star, 👑 Crown, 🔥 Fire, ⚡ Lightning, 🚀 Rocket, 💎 Diamond, 💀 Skull, 👻 Ghost, 👽 Alien, 🤖 Robot, 🦄 Unicorn, 🐉 Dragon

### Features
- **Player Count Banner**: Shows total players, celebrities, transfer window
- **Hot Celebs This Week**: Major names making headlines (Prince Andrew, Meghan Markle, Kanye West, Taylor Swift, Elon Musk, Donald Trump, Katie Price, Holly Willoughby)
- **Today's News**: Real celebrity news filtered for MAJOR stories only (deaths, divorces, awards, legal battles) - no gossip
- **Transfer Window**: 1 swap per week (resets weekly)
- **Profanity Filter**: Blocks racist/offensive team names
- **Social Sharing**: WhatsApp, Facebook, X/Twitter (for teams AND leagues)
- **Top Picked**: Most selected celebrities by players
- **Friends Leagues**: Create leagues with invite codes, compete with friends
- **Badge System**: Weekly Champion 🏆, Trendsetter ⚡, Grim Reaper 💀, Controversy King 🔥, A-List Club ⭐, League Legend 👑
- **Hall of Fame**: Top players with most badges

## What's Been Implemented (Feb 20, 2026)
- ✅ Full FastAPI backend with all endpoints
- ✅ Wikipedia autocomplete search - filters out albums, films, TV shows, fictional characters, plants, locations
- ✅ Accent-normalized search (Beyoncé, Rihanna work with or without accents)
- ✅ A/B/C/D tier system with tiered pricing
- ✅ Controversial celebrity price boosts
- ✅ Brown Bread Bonus (+100 for deceased)
- ✅ Controversy Bonus (+25 points per scandal)
- ✅ Minimum buzz score of 5 points
- ✅ Player count banner
- ✅ Hot Celebs This Week banner
- ✅ Today's Top Celeb News (filtered for MAJOR news, no gossip)
- ✅ Top Picked Celebrities section
- ✅ Transfer window (1 per week)
- ✅ Profanity filter for team names
- ✅ Social sharing (WhatsApp/Facebook/X) for both teams AND leagues
- ✅ Points methodology modal
- ✅ React frontend with Tailwind styling
- ✅ Friends League system with invite codes
- ✅ League sharing via WhatsApp, X (Twitter), Facebook
- ✅ Badge/achievement system
- ✅ Mobile responsive design with bottom navigation
- ✅ Hall of Fame page showing top badge earners
- ✅ Team customization (colors and icons)
- ✅ Brown Bread Watch (elderly celebrities with risk indicators)

## Bug Fixes (Feb 2026)
- ✅ Fixed search returning plants (Holly genus) - now requires query to be in celebrity's name
- ✅ Fixed search returning albums/songs with celebrity names
- ✅ Fixed search returning unrelated people (e.g., Kanye search returning Bianca Censori)
- ✅ Fixed "is a bar" substring false positive (Rihanna "is a Barbadian singer" was being filtered)
- ✅ Fixed route ordering issue with /api/team/customization-options
- ✅ Added accent normalization for celebrity names (Beyoncé, etc.)
- ✅ Added league sharing buttons (WhatsApp, X, Facebook)

## News Sources
- BBC News (priority)
- The Guardian (priority)
- TMZ
- People
- Page Six
- Daily Mail

News is filtered to show only MAJOR stories (deaths, divorces, awards, legal battles, scandals) and skip gossip (braless, bikini, outfit stories).

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
- Automated weekly badge awards
