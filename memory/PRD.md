# Celebrity Buzz Index - Product Requirements Document

## Original Problem Statement
Build a Celebrity Buzz Index fantasy-league style platform where users can:
- Search ANY celebrity worldwide with a Wikipedia page
- View AI-generated news coverage and Wikipedia info
- Calculate "buzz points" based on media mentions
- Build teams with a £50M budget
- Compete on leaderboards
- Social sharing (Twitter/X + copy link)

**User Requirements:**
- UK-focused celebrities (Prince Andrew, Katie Price, etc.)
- Categories: Movie Stars, TV Actors, Musicians, Athletes, Royals, Reality TV, Other
- A/B/C/D list celebrity tiers with tiered pricing
- Autocomplete search showing all matching names with photos and prices
- Points calculation explainer
- Celebrity photos in trending ticker with tier badges

## Architecture

### Backend (FastAPI + MongoDB)
- `/api/categories` - Get all celebrity categories
- `/api/autocomplete?q=` - **NEW** Wikipedia autocomplete search
- `/api/points-methodology` - **NEW** Get points calculation explanation
- `/api/trending` - Get trending celebrities with tiers
- `/api/celebrity/search` - Search and create celebrity profile with AI news + tier
- `/api/celebrities/category/{category}` - Get celebrities by category
- `/api/team/create` - Create new team
- `/api/team/add` - Add celebrity to team
- `/api/team/remove` - Remove celebrity from team
- `/api/leaderboard` - Get team rankings

### Celebrity Tier System
- **A-LIST** (£18-22M): Oscar/Grammy winners, legendary status, "one of the most"
- **B-LIST** (£12-16M): Award-winning, chart-topping, successful
- **C-LIST** (£7-11M): Known for appearances, featured in
- **D-LIST** (£3-6M): Everyone else

### Points Calculation
- News Mentions: +1.0 point per article
- Tabloid Coverage: +3.0 points (Daily Mail, Sun, TMZ)
- Broadsheet Coverage: +2.0 points (BBC, Guardian, Times)
- Controversy Bonus: +1.0 point per scandal article
- Social Media Trending: +5.0 points per event
- **Tier Multipliers**: A=1.0x, B=1.2x, C=1.5x, D=2.0x

### Frontend (React + Tailwind CSS)
- Header with animated title
- Trending ticker with celebrity photos, buzz scores, and tier badges
- "How It Works" 4-step guide
- "How Points Work" methodology modal
- Autocomplete search with suggestions dropdown
- Category filter pills (7 categories)
- Celebrity cards with tier badges, Wikipedia links
- Team panel with budget display
- Leaderboard
- Share modal (Twitter + copy link)

### Integrations
- Wikipedia API for celebrity bios, images, and autocomplete
- OpenAI GPT-4o (via Emergent LLM key) for AI news generation
- MongoDB for data persistence

## What's Been Implemented (Feb 20, 2026)
- ✅ Full FastAPI backend with all endpoints
- ✅ Wikipedia autocomplete search (any celebrity worldwide)
- ✅ A/B/C/D tier system with tiered pricing
- ✅ Points methodology modal with detailed explanation
- ✅ Celebrity photos in trending ticker with tier badges
- ✅ GPT-4o AI news generation
- ✅ React frontend with Tailwind styling
- ✅ "Electric Tabloid" dark theme
- ✅ All 7 category filters
- ✅ Celebrity cards with tier badges
- ✅ Team management (add/remove)
- ✅ Budget tracking with tier pricing
- ✅ Leaderboard
- ✅ Share modal (Twitter + copy link)
- ✅ UK celebrities seeded

## Backlog / Future Features

### P0 (Critical)
- None remaining

### P1 (High Priority)
- User authentication for persistent teams
- Real news API integration (NewsAPI)
- Weekly buzz score updates

### P2 (Medium Priority)
- Celebrity comparison feature
- Historical buzz trends chart
- Team sharing with preview cards

### P3 (Nice to Have)
- Dark/light mode toggle
- Mobile app version
- Achievement badges
