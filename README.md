# WhichGLP

Real-world dashboard for GLP-1 weight-loss drug outcomes by analyzing and aggregating Reddit posts. Mission is to help people make educated decisions when choosing their weight-loss drug.

I've accelerated development by prompting Claude Code to generate code. More details at [docs/AGENTS.md](docs/AGENTS.md).

The website is available at: [whichglp.com](https://whichglp.com)

## Tech Stack

### API service

- **Runtime:** Node.js 20+
- **Framework:** Express.js
- **API Layer:** tRPC (end-to-end type safety with frontend)
- **Database ORM:** Prisma
- **Caching/Rate Limiting:** Redis
- **Data Ingestion:** Reddit API (PRAW/custom HTTP client)
- **Scraping Backup:** Playwright (when APIs rate-limited/unavailable)
- **AI Processing:** Claude Sonnet 4 API (extract structured data from posts)
- **Recommendation Engine:** FastAPI + Python microservice (KNN-based ML recommendations)

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
- **API Hosting:** Railway (Express + tRPC + Redis + Playwright)
- **Frontend Hosting:** Vercel

### Architecture Notes

- **Primary ingestion:** Reddit API (PRAW/custom HTTP client)
- **Backup ingestion:** Playwright scraping (fallback when API limits exceeded)
- **Type safety:** tRPC ensures frontend/api contract enforcement
- **Supabase benefits:** PostgreSQL + Auth + Storage + Realtime in single platform; but we primarily use the PostgreSQL
- **Railway deployment:** Separate services for frontend, API (Node.js), and rec-engine (Python)

