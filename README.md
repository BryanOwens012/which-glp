# WhichGLP

Real-world dashboard for GLP-1 weight-loss drug outcomes by analyzing and aggregating Reddit posts. Mission is to help people make educated decisions when choosing their weight-loss drug.

I've accelerated development by prompting Claude Code to generate code. More details at [docs/AGENTS.md](docs/AGENTS.md).

The website is available at: [whichglp.com](https://whichglp.com)

## Tech Stack

### Frontend

- **Framework:** Next.js 15 (App Router)
- **Language:** TypeScript (strict mode)
- **UI:** React 19, Tailwind CSS v4, Radix UI + shadcn/ui
- **API Client:** tRPC client, TanStack Query
- **Hosting:** Railway

### Backend Services (FastAPI Microservices)

**API Service** (`apps/api`)
- **Runtime:** Node.js 20+
- **Framework:** tRPC (type-safe API)
- **Database:** Supabase client
- **Caching:** Redis (ioredis)

**Post Ingestion** (`apps/post-ingestion`)
- **Framework:** FastAPI + uvicorn
- **Data Source:** Reddit API (PRAW)
- **Function:** Fetch recent Reddit posts from GLP-1 subreddits

**User Extraction** (`apps/user-extraction`)
- **Framework:** FastAPI + uvicorn
- **AI Model:** GLM-4.5-Air (via Z.ai SDK)
- **Function:** Extract user demographics from Reddit user history

**Post Extraction** (`apps/post-extraction`)
- **Framework:** FastAPI + uvicorn
- **AI Model:** GLM-4.5-Air (via Z.ai SDK)
- **Function:** Extract structured drug experience data from posts

**Recommendation Engine** (`apps/rec-engine`)
- **Framework:** FastAPI + uvicorn
- **ML Stack:** scikit-learn (KNN), pandas, numpy
- **Function:** Generate personalized drug recommendations

### Infrastructure

- **Database:** PostgreSQL (Supabase)
- **Caching:** Redis
- **Hosting:** Railway (6 services: frontend, api, 4 Python microservices)
- **AI Processing:** GLM-4.5-Air via Z.ai SDK (post/user extraction)

### Development

- **Python:** 3.13 with shared venv at repository root
- **Node.js:** 20+ for frontend and API service
- **Monorepo:** All services in `apps/` directory

