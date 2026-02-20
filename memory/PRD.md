# Celebrity Buzz Index - Product Requirements Document

## Original Problem Statement
Build a Celebrity Buzz Index fantasy-league style platform where users can:
- Search celebrities and view Wikipedia info
- See live AI-generated news coverage  
- Calculate "buzz points" based on media mentions
- Build teams with a £50M budget
- Compete on leaderboards
- Social sharing (Twitter/X + copy link)

**User Requirements:**
- UK-focused celebrities (Prince Andrew, Katie Price, etc.)
- Categories: Movie Stars, TV Actors, Musicians, Athletes, Royals, Reality TV, Other
- "How It Works" section
- Celebrity photos in trending ticker
- Wikipedia and news article links

## Architecture

### Backend (FastAPI + MongoDB)
- `/api/categories` - Get all celebrity categories
- `/api/trending` - Get trending celebrities
- `/api/celebrity/search` - Search and create celebrity profile with AI news
- `/api/celebrities/category/{category}` - Get celebrities by category
- `/api/team/create` - Create new team
- `/api/team/add` - Add celebrity to team
- `/api/team/remove` - Remove celebrity from team  
- `/api/leaderboard` - Get team rankings
- `/api/share/{team_id}` - Get shareable team data

### Frontend (React + Tailwind CSS)
- Header with animated title
- Trending ticker with celebrity photos and buzz scores
- "How It Works" 3-step guide
- Search bar
- Category filter pills (7 categories)
- Celebrity cards with hover news panel
- Team panel with budget display
- Leaderboard
- Share modal (Twitter + copy link)

### Integrations
- Wikipedia API for celebrity bios and images
- OpenAI GPT-4o (via Emergent LLM key) for AI news generation
- MongoDB for data persistence

## User Personas
1. **Celebrity News Enthusiast** - Follows tabloids, wants UK gossip
2. **Fantasy Sports Fan** - Enjoys team building and competition
3. **Social Media User** - Wants to share achievements

## Core Requirements (Static)
- 7 celebrity categories with icon differentiation
- £50M budget for team building
- Buzz score calculation based on news coverage
- Real Wikipedia data integration
- AI-generated news headlines
- Social sharing functionality
- Leaderboard competition

## What's Been Implemented (Feb 20, 2026)
- ✅ Full FastAPI backend with all endpoints
- ✅ MongoDB integration for celebrities, teams, trending cache
- ✅ Wikipedia API integration for bios and images
- ✅ GPT-4o AI news generation via Emergent LLM key
- ✅ Category detection algorithm (Royals, Reality TV, Musicians, Athletes, TV Actors, Movie Stars, Other)
- ✅ React frontend with Tailwind CSS styling
- ✅ "Electric Tabloid" dark theme design
- ✅ Trending ticker with celebrity photos
- ✅ "How It Works" section
- ✅ All 7 category filters
- ✅ Celebrity cards with hover news panels
- ✅ Team management (add/remove celebrities)
- ✅ Budget tracking
- ✅ Leaderboard
- ✅ Share modal (Twitter + copy link)
- ✅ UK celebrities seeded (Prince Andrew, Katie Price, Prince William, etc.)

## Backlog / Future Features

### P0 (Critical)
- None remaining

### P1 (High Priority)
- User authentication for persistent teams
- Real news API integration (NewsAPI or similar)
- Weekly buzz score updates
- Push notifications for big news

### P2 (Medium Priority)  
- Celebrity comparison feature
- Historical buzz trends chart
- Team sharing with preview cards
- Multiple team support

### P3 (Nice to Have)
- Dark/light mode toggle
- Mobile app version
- Celebrity alerts/watchlist
- Achievement badges

## Next Tasks
1. Consider adding user authentication for persistent teams across devices
2. Integrate real news API for live news instead of AI-generated
3. Add more UK celebrities to each category
4. Consider weekly "buzz updates" feature
