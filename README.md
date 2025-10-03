# WhichGLP

Real-world dataset for GLP-1 weight-loss drug outcomes by aggregating Reddit/Twitter posts and user-submitted reviews.

I've accelerated development by prompting Claude Code to generate code. More details at AGENTS.md and AGENTS_APPENDLOG.md. 

Once complete, this project will be available at whichglp.com.

## Tech Stack So Far

I'm currently running this stack locally and non-containerized, to seed the Supabase DB with historical Reddit posts + comments.

- **Data Ingestion:** Reddit API (PRAW/custom HTTP client) with Python
- **Database:** PostgreSQL via Supabase (free tier: 500MB, upgrade to Pro: 8GB @ $25/month)

I'll progressively add more stack as necessary. No need to prematurely optimize.

## Full Tech Stack Vision

### Backend

- **Runtime:** Node.js 20+
- **Framework:** Express.js
- **API Layer:** tRPC (end-to-end type safety with frontend)
- **Database ORM:** Prisma
- **Caching/Rate Limiting:** Redis
- **Data Ingestion:** Reddit API (PRAW/custom HTTP client), Twitter API (via twitterapi.io)
- **Scraping Backup:** Playwright (when APIs rate-limited/unavailable)
- **AI Processing:** Claude Sonnet 4 API (extract structured data from posts)
- **Optional:** FastAPI + Python microservice (heavy NLP/data processing if needed)

### Frontend

- **Framework:** Next.js 15 (App Router)
- **Language:** TypeScript (strict mode)
- **UI Library:** React.js
- **Styling:** Tailwind CSS
- **Components:** Radix UI + Shadcn/ui
- **Package Manager:** Yarn

### Infrastructure

- **Database:** PostgreSQL via Supabase (free tier: 500MB, upgrade to Pro: 8GB @ $25/month)
- **Auth:** Supabase Auth
- **Backend Hosting:** Railway (Express + tRPC + Redis + Playwright)
- **Frontend Hosting:** Vercel
- **Containerization:** Not present initially, Docker added later for production

### Architecture Notes

- **Primary ingestion:** Reddit API + Twitter API (twitterapi.io proxy)
- **Backup ingestion:** Playwright scraping (fallback when API limits exceeded)
- **Type safety:** tRPC ensures frontend/backend contract enforcement
- **Supabase benefits:** PostgreSQL + Auth + Storage + Realtime in single platform
- **Railway deployment:** Single service for Node.js backend, Redis, and Playwright dependencies

