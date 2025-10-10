# WhichGLP

Real-world dashboard for GLP-1 weight-loss drug outcomes by analyzing and aggregating Reddit posts. Mission is to help people make educated decisions when choosing their weight-loss drug.

I've accelerated development by prompting Claude Code to generate code. More details at [docs/AGENTS.md](docs/AGENTS.md).

The website is available at: [whichglp.com](https://whichglp.com)

## Tech Stack

### Frontend Service

- **Framework:** Next.js 15 (App Router)
- **Language:** TypeScript (strict mode)
- **UI:** React 19, Tailwind CSS v4, Radix UI + shadcn/ui
- **API Client:** tRPC client, TanStack Query

### Backend Services

**1. API Service** (`apps/api`)
- **Runtime:** Node.js 20+
- **Language:** TypeScript (strict mode)
- **Framework:** tRPC (type-safe API)
- **Database:** Supabase client
- **Caching:** Redis (ioredis)

**2. Post Ingestion** (`apps/post-ingestion`)
- **Framework:** FastAPI + uvicorn
- **Language:** Python 3.13+
- **Data Source:** Reddit API (PRAW)
- **Database:** Supabase client
- **Function:** Fetch recent Reddit posts from GLP-1 subreddits

**3. Post Extraction** (`apps/post-extraction`)
- **Framework:** FastAPI + uvicorn
- **Language:** Python 3.13+
- **Database:** Supabase client
- **AI Model:** GLM-4.5-Air (via Z.ai SDK), a cost-effective model for simple text extraction, summarization, and sentiment analysis
- **Function:** Extract structured drug experience data from posts

**4. User Extraction** (`apps/user-extraction`)
- **Framework:** FastAPI (Python) + uvicorn
- **Language:** Python 3.13+
- **Database:** Supabase client
- **AI Model:** GLM-4.5-Air (via Z.ai SDK)
- **Function:** Extract user demographics from Reddit user history (their posts and comments)

**5. Recommendation Engine** (`apps/rec-engine`)
- **Framework:** FastAPI + uvicorn
- **Language:** Python 3.13+
- **ML Stack:** scikit-learn (KNN), pandas, numpy
- **Function:** Generate personalized drug recommendations

### Infrastructure

**Vercel**
- **Frontend:** Next.js app deployed on Vercel

**Railway**
- **Caching:** Redis
- **Backend Services:** API, Post Ingestion, Post Extraction, User Extraction, Recommendation Engine
- **Lambdas:** Cron-triggered functions to periodically run Post Ingestion, Post Extraction, and User Extraction services

**Supabase**
- **Database:** PostgreSQL

### Development

- **Python:** 3.13 with shared venv at repository root
- **Node.js:** 20+ for frontend and API service
- **Monorepo:** All services in `apps/` directory

