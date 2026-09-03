# WhichGLP Architecture

## Monorepo Structure

This is a monorepo containing 5 backend services, 1 frontend, and automated cron jobs:

```
which-glp/
├── apps/
│   ├── frontend/          # Next.js 16 app (Vercel)
│   ├── api/               # Node.js tRPC API (Railway)
│   ├── rec-engine/        # Python ML recommendations (Railway)
│   ├── post-ingestion/    # Python Reddit ingestion (Railway)
│   ├── post-extraction/   # Python AI extraction (Railway)
│   ├── user-extraction/   # Python user demographics (Railway)
│   └── shared/            # Shared database migrations
├── scripts/
│   ├── legacy-ingestion/  # Legacy Python Reddit scraper
│   └── cron/              # Cron trigger scripts (not deployed; Railway runs .railway/functions/)
├── venv/                  # Python virtual environment (shared)
└── requirements.txt       # Python dependencies (shared)
```

## Service Architecture

### 1. Frontend (`apps/frontend`)

**Tech Stack:**
- Next.js 16 (App Router)
- React 19
- TypeScript (strict mode)
- Tailwind CSS v4
- tRPC client + TanStack Query

**Responsibilities:**
- User-facing web application
- Forms for user input (weight, goals, preferences)
- Display drug recommendations
- Browse community experiences

**Deployment:**
- Platform: Vercel
- Deploys on push (branches enabled in `vercel.json`)
- Environment variables:
  - `NEXT_PUBLIC_API_URL` - API service URL
  - `NEXT_PUBLIC_GA_TAG` - Google Analytics tag
  - `NEXT_PUBLIC_POSTHOG_PROJECT_TOKEN`, `NEXT_PUBLIC_POSTHOG_HOST` - PostHog (optional)

---

### 2. API Service (`apps/api`)

**Tech Stack:**
- Node.js 22+
- TypeScript (strict mode)
- tRPC (type-safe API)
- Supabase client
- Redis (ioredis)

**Responsibilities:**
- API gateway for frontend
- Fetch experiences from Supabase
- Aggregate statistics
- Call Rec-Engine for recommendations
- Handle caching with Redis

**Port:** 3002 (local development; `PORT` overrides)

**Key Endpoints (tRPC procedures):**
- `experiences.list` - Get filtered experiences
- `experiences.getById` - Get single experience
- `experiences.list` / `experiences.getById`, `drugs.getAllStats`, `platform.getStats` / `platform.getTrends`, `locations.getData`, `demographics.getData`, `recommendations.getForUser` (routers in `apps/api/src/routers/`)
- `recommendations.getForUser` - Get personalized recommendations

**Non-tRPC routes:** `GET /health` returns `{"status":"ok","service":"api"}`. It is
the only non-`/trpc` path the service answers; everything else returns 404.

**HTTP edge behavior** (`apps/api/src/index.ts` plus `src/lib/{config,cors,client-ip,rate-limit}.ts`):
- **CORS is an allowlist, not a reflection.** Allowed: the production origins, this
  project's Vercel preview deployments, and localhost outside production. An unlisted
  origin gets no `Access-Control-Allow-Origin` at all. Add extra origins via
  `ALLOWED_ORIGINS` (comma-separated bare origins — no path, no trailing slash; the
  service refuses to boot otherwise). No `Access-Control-Allow-Credentials` is sent:
  nothing here is authenticated, so nothing needs it. Reintroduce it only alongside auth.
  Allowed request headers are `Content-Type`, `Authorization`, and `trpc-accept` (the
  streaming negotiation header `httpBatchStreamLink` sends).
- **tRPC responses are streamed**, piped from the fetch adapter to the socket, so a batch's
  procedures reach the client as each one resolves. A client that disconnects mid-response
  is not logged as an error.
- **Request bodies are capped** at `MAX_REQUEST_BODY_BYTES` (default 1 MB), enforced on
  raw bytes both via `Content-Length` and while streaming, and refused at the
  `Expect: 100-continue` handshake so an oversized upload is never transmitted.
- **Rate limiting is per client IP, in Redis**, because the service runs multiple
  replicas — a per-process counter would grant one budget per replica. Two budgets:
  `/trpc` and `/health` draw on a generous one (default 300/60s, sized for CGNAT and the
  frontend's prefetching); every other path draws on a tight one (default 5/600s), and
  exhausting it blocks the address from *unknown paths* for an hour. The block is
  deliberately not extended to `/trpc`, so one bad host cannot lock out everyone sharing
  its NAT address. If Redis is unreachable the limiter falls back to a per-process
  budget; the client stops reconnecting after three failed attempts, so that fallback
  lasts until the replica restarts.
- **The client IP comes from the rightmost `X-Forwarded-For` entry**, which Railway's
  edge appended. The leftmost is client-supplied and would let any caller choose its own
  bucket. A request whose address cannot be resolved is refused.
- **Unknown paths are not logged per request.** Scanner sprays are the bulk of that
  traffic; only the resulting block is logged. Logged paths are truncated and stripped
  of control characters.

**Deployment:**
- Platform: Railway
- Service: `API`
- Domain: `api.whichglp.com`
- Build command: `npm run build`
- Start command: `npm start`
- Environment variables:
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_KEY`
  - `REDIS_URL`
  - `REC_ENGINE_URL`
  - `ALLOWED_ORIGINS` (optional) - extra CORS origins beyond the built-in allowlist
  - `ALLOW_VERCEL_PREVIEW_ORIGINS` (optional, set `false` to refuse this project's Vercel preview origins)
  - `MAX_REQUEST_BODY_BYTES` (optional, default `1000000`)
  - `SHUTDOWN_TIMEOUT_MS` (optional, default `10000`) - how long a shutdown waits for in-flight requests before exiting anyway. Railway SIGKILLs a deployment 0 seconds after SIGTERM by default, so the API's `drainingSeconds` in `.railway/railway.ts` must exceed this or the graceful shutdown never runs
  - `RATE_LIMIT_ENABLED` (optional, set `false` to disable) and the
    `RATE_LIMIT_API_*` / `RATE_LIMIT_PROBE_*` overrides in `src/lib/config.ts`

---

### 3. Recommendation Engine (`apps/rec-engine`)

**Tech Stack:**
- Python 3.13
- FastAPI + uvicorn
- scikit-learn (KNN)
- pandas, numpy
- Supabase client

**Responsibilities:**
- Machine learning recommendations
- KNN-based user matching
- Drug ranking algorithm
- Side effect prediction
- Cost estimation

**Key Endpoints (REST):**
- `POST /api/recommendations` - Get recommendations
- `GET /health` - Health check
- `GET /api/cache/clear` - Clear cache

**Deployment:**
- Platform: Railway
- Service: `Rec-Engine`
- Domain: `whichglp-rec-engine.up.railway.app`
- Start command: `cd apps/rec-engine && python3 api.py`
- Environment variables:
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_KEY`
  - `PORT`

---

### 4. Post Ingestion (`apps/post-ingestion`)

**Tech Stack:**
- Python 3.13
- FastAPI + uvicorn
- PRAW (Reddit API)
- Supabase client

**Responsibilities:**
- Fetch recent Reddit posts from GLP-1 subreddits
- Store raw posts in `reddit_posts` table
- Triggered daily by its cron function (schedule in `.railway/railway.ts`)

**Key Endpoints (REST):**
- `POST /api/ingest` - Trigger ingestion
- `GET /api/status` - Check ingestion status
- `GET /health` - Health check

**Deployment:**
- Platform: Railway
- Service: `Post-Ingestion`
- Domain: `whichglp-post-ingestion.up.railway.app`
- Start command: `uvicorn api:app --host 0.0.0.0 --port $PORT`
- Triggered by: `Post-Ingestion-Cron` (daily)

---

### 5. Post Extraction (`apps/post-extraction`)

**Tech Stack:**
- Python 3.13
- FastAPI + uvicorn
- GPT-5-nano (OpenAI SDK)
- Supabase client

**Responsibilities:**
- Extract structured drug experience data from posts
- AI-powered feature extraction (drug, weight loss, cost, side effects)
- Store in `extracted_features` table
- Triggered daily by its cron function (schedule in `.railway/railway.ts`)

**Key Endpoints (REST):**
- `POST /api/extract` - Trigger extraction
- `GET /api/status` - Check extraction status
- `GET /health` - Health check

**Deployment:**
- Platform: Railway
- Service: `Post-Extraction`
- Domain: `whichglp-post-extraction.up.railway.app`
- Start command: `uvicorn api:app --host 0.0.0.0 --port $PORT`
- Triggered by: `Post-Extraction-Cron` (daily)

---

### 6. User Extraction (`apps/user-extraction`)

**Tech Stack:**
- Python 3.13
- FastAPI + uvicorn
- GPT-5-nano (OpenAI SDK)
- Supabase client

**Responsibilities:**
- Extract user demographics from Reddit user history
- AI-powered demographic extraction (age, sex, location)
- Store in `user_demographics` table
- Triggered daily by its cron function (schedule in `.railway/railway.ts`)

**Key Endpoints (REST):**
- `POST /api/analyze` - Trigger user analysis
- `GET /api/stats` - Get analysis statistics
- `GET /api/status` - Check analysis status
- `GET /health` - Health check

**Deployment:**
- Platform: Railway
- Service: `User-Extraction`
- Domain: `whichglp-user-extraction.up.railway.app`
- Start command: `uvicorn api:app --host 0.0.0.0 --port $PORT`
- Triggered by: `User-Extraction-Cron` (daily)

---

## Cron Jobs (Automated Scheduling)

### 1. View-Refresher-Cron

**Schedule:** Daily (UTC time in `.railway/railway.ts`)
**Function:** Refreshes materialized views in Supabase
**Implementation:** Railway Cron Schedule
**Script:** `.railway/functions/view-refresher-cron.ts`

### 2. Post-Ingestion-Cron

**Schedule:** Daily (UTC time in `.railway/railway.ts`)
**Function:** Triggers `POST /api/ingest` on Post-Ingestion service
**Implementation:** Railway Cron Schedule
**Target:** `whichglp-post-ingestion.up.railway.app/api/ingest`

### 3. Post-Extraction-Cron

**Schedule:** Daily (UTC time in `.railway/railway.ts`)
**Function:** Triggers `POST /api/extract` on Post-Extraction service
**Implementation:** Railway Cron Schedule
**Target:** `whichglp-post-extraction.up.railway.app/api/extract`

### 4. User-Extraction-Cron

**Schedule:** Daily (UTC time in `.railway/railway.ts`)
**Function:** Triggers `POST /api/analyze` on User-Extraction service
**Implementation:** Railway Cron Schedule
**Target:** `whichglp-user-extraction.up.railway.app/api/analyze`

---

## Infrastructure Services

### Redis

**Platform:** Railway
**Type:** Redis Database with persistent volume
**Volume:** `redis-volume`
**Function:** Response cache and per-IP rate-limit counters for the API service
**Connected to:** API service

### Supabase

**Type:** PostgreSQL Database
**Tier:** Pro ($25/month, 8GB storage)
**Function:** Primary data storage
**Tables:**
- `reddit_posts` - Raw Reddit posts
- `reddit_comments` - Raw Reddit comments
- `extracted_features` - AI-extracted structured data
- `user_demographics` - User demographic data
- `mv_experiences_denormalized` - Materialized view for fast queries

---

## Data Flow

### Data Ingestion Pipeline

```
┌──────────────────┐
│ Post-Ingestion   │ ◄─── Cron (daily)
│ (Reddit API)     │
└────────┬─────────┘
         │
         ▼
   ┌──────────┐
   │ Supabase │
   │  reddit_ │
   │  posts   │
   └────┬─────┘
        │
        ▼
┌──────────────────┐
│ Post-Extraction  │ ◄─── Cron (daily)
│ (GPT-5-nano)     │
└────────┬─────────┘
         │
         ▼
   ┌──────────┐
   │ Supabase │
   │ extracted│
   │ features │
   └────┬─────┘
        │
        ▼
┌──────────────────┐
│ User-Extraction  │ ◄─── Cron (daily)
│ (GPT-5-nano)     │
└────────┬─────────┘
         │
         ▼
   ┌──────────┐
   │ Supabase │
   │   user_  │
   │demographics│
   └────┬─────┘
        │
        ▼
┌──────────────────┐
│ View-Refresher   │ ◄─── Cron (daily)
└────────┬─────────┘
         │
         ▼
   ┌──────────┐
   │ Supabase │
   │    mv_   │
   │experiences│
   └──────────┘
```

### Recommendation Request Flow

```
┌─────────┐     tRPC      ┌─────────┐    HTTP      ┌────────────┐
│ Frontend│─────────────►│   API   │────────────►│Rec-Engine  │
│ (Vercel)│              │(Railway)│             │  (Railway) │
└─────────┘              └─────┬───┘             └──────┬─────┘
                               │                        │
                               ▼                        │
                          ┌────────┐                    │
                          │ Redis  │                    │
                          │ Cache  │                    │
                          └────────┘                    │
                               │                        │
                               └────────────┬───────────┘
                                            │
                                            ▼
                                    ┌──────────────┐
                                    │   Supabase   │
                                    │  PostgreSQL  │
                                    └──────────────┘
```

**Steps:**
1. User fills form on frontend (Vercel)
2. Frontend calls `recommendations.getForUser` via tRPC
3. API service forwards request to Rec-Engine via HTTP
4. Rec-Engine:
   - Fetches experiences from Supabase
   - Runs KNN algorithm
   - Ranks drugs
   - Returns recommendations
5. API caches result in Redis
6. API returns to frontend
7. Frontend displays recommendations

### Experience Browsing Flow

```
┌─────────┐     tRPC      ┌─────────┐
│ Frontend│─────────────►│   API   │
│ (Vercel)│              │(Railway)│
└─────────┘              └─────┬───┘
                               │
                               ▼
                          ┌────────┐
                          │ Redis  │ (check cache)
                          └────┬───┘
                               │
                               ▼
                        ┌──────────────┐
                        │   Supabase   │
                        │ mv_experiences│
                        └──────────────┘
```

**Steps:**
1. Frontend calls `experiences.list` via tRPC
2. API checks Redis cache
3. If miss, query Supabase materialized view
4. Cache result in Redis (TTL: 5 minutes)
5. Return to frontend

---

## Railway Deployment Summary

**Total Services: 10**

| Service | Type | Schedule |
|---------|------|----------|
| API | Node.js | Always-on |
| Rec-Engine | Python | Always-on |
| Post-Ingestion | Python | Always-on (HTTP triggered) |
| Post-Extraction | Python | Always-on (HTTP triggered) |
| User-Extraction | Python | Always-on (HTTP triggered) |
| Redis | Database | Always-on |
| View-Refresher-Cron | Cron | Daily |
| Post-Ingestion-Cron | Cron | Daily |
| Post-Extraction-Cron | Cron | Daily |
| User-Extraction-Cron | Cron | Daily |

**Note:** Frontend is deployed on Vercel separately.

---

### Dual-stack networking

Railway services can be IPv6-only or dual-stack, so every cross-service address must tolerate both:

- `apps/api/src/lib/redis.ts` connects with `family: 0` (dual-stack), `keepAlive: 30000`, `connectTimeout: 10000`.
- `apps/api/src/routers/recommendations.ts` reads `REC_ENGINE_URL`, falling back to `http://127.0.0.1:8001` locally (never `localhost`, which may resolve to `::1` alone).
- Python services bind `0.0.0.0` (`--host 0.0.0.0` in `railway.ts`, `host="0.0.0.0"` in each `api.py`), which is IPv4 only.
- Prefer the `.railway.internal` private hostnames declared in `.railway/railway.ts` for service-to-service calls.

## Local Development

Local default ports: API `3002`, Rec-Engine `8001`, User-Extraction `8002`, Post-Ingestion `8003`, Post-Extraction `8004`. The Python defaults live in each `api.py`'s `__main__` block, so `python3 api.py` picks them up while the `uvicorn` CLI needs `--port` (its own default is 8000). Health checks: `curl http://localhost:<port>/health`.

### Start all services

```bash
# Terminal 1: Frontend
cd apps/frontend
npm run dev  # http://localhost:3000

# Terminal 2: API
cd apps/api
npm run dev  # http://localhost:3002

# Terminal 3: Rec-Engine
cd apps/rec-engine
python3 api.py

# Terminal 4: Post-Ingestion
cd apps/post-ingestion
uvicorn api:app --reload --port 8003

# Terminal 5: Post-Extraction
cd apps/post-extraction
uvicorn api:app --reload --port 8004

# Terminal 6: User-Extraction
cd apps/user-extraction
uvicorn api:app --reload --port 8002

# Terminal 7: Redis
redis-server  # Port 6379
```

### Environment Setup

1. **Root `.env`** (for Python services):
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_DB_PASSWORD=your-db-password
SUPABASE_SERVICE_KEY=your-service-key
SUPABASE_SERVICE_KEY=your-service-key
REDDIT_CLIENT_ID=your-client-id
REDDIT_CLIENT_SECRET=your-client-secret
REDDIT_USER_AGENT=whichglp-ingestion/0.1
OPENAI_API_KEY=your-openai-api-key
```

2. **`apps/frontend/.env.local`**:
```bash
NEXT_PUBLIC_API_URL=http://localhost:3002/trpc
NEXT_PUBLIC_GA_TAG=your-ga-tag
```

3. **`apps/api/.env`**:
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
REDIS_URL=redis://localhost:6379
REC_ENGINE_URL=http://localhost:8001
```

---

## Monitoring & Health Checks

### Health Check Endpoints

```bash
# API
curl https://api.whichglp.com/health

# Rec-Engine
curl https://whichglp-rec-engine.up.railway.app/health

# Post-Ingestion
curl https://whichglp-post-ingestion.up.railway.app/health

# Post-Extraction
curl https://whichglp-post-extraction.up.railway.app/health

# User-Extraction
curl https://whichglp-user-extraction.up.railway.app/health
```

### Railway Logs

```bash
# Service names are Railway display names; -p/-e are needed in an unlinked clone
railway logs -s API -p df649372-5b20-4e68-8ccd-31935edceade -e production
railway logs -s Rec-Engine -p df649372-5b20-4e68-8ccd-31935edceade -e production
railway logs -s Post-Ingestion -p df649372-5b20-4e68-8ccd-31935edceade -e production
railway logs -s Post-Extraction -p df649372-5b20-4e68-8ccd-31935edceade -e production
railway logs -s User-Extraction -p df649372-5b20-4e68-8ccd-31935edceade -e production
```

---

## Architecture Decisions

### Why Separate Microservices?

**Pros:**
✅ **Independent Scaling**: Each service scales based on load
✅ **Process Isolation**: Failures don't cascade across services
✅ **Technology Optimization**: Use best tool for each job (Node.js for API, Python for ML/AI)
✅ **Faster Deployments**: Deploy services independently
✅ **Simpler Testing**: Test each service in isolation
✅ **Cost Optimization**: Scale down unused services

**Cons:**
❌ **Network Latency**: HTTP calls between services add ~20-50ms
❌ **More Complex Deployment**: 10 services vs 1 monolith
❌ **Higher Cost**: Multiple Railway services (mitigated by efficient scheduling)

### Why Cron Jobs Instead of Always-Running?

**Reasoning:**
- Data ingestion doesn't need to run 24/7
- Reddit posts arrive at predictable rates
- Cron jobs reduce Railway costs (pay for compute time, not idle time)
- FastAPI services boot quickly (~2-5 seconds)
- 2-day intervals ensure fresh data without wasted cycles

### Why GPT-5-nano Instead of Claude?

**Cost Comparison:**
- Claude Sonnet 4: $3/1M input tokens, $15/1M output tokens
- GPT-5-nano: ~$0.05/$0.40 per 1M tokens (via OpenAI SDK)
- **Savings: ~85% cost reduction**

**Trade-offs:**
- Slightly lower quality extractions (~5-10% less accurate)
- Faster response times (optimized for speed)
- Good enough for text extraction, summarization, sentiment analysis
- Can always upgrade to Claude for critical extractions

---

## Future Architecture

### Phase 1 (Current)
✅ Monorepo with 10 Railway services
✅ Cron-based automation
✅ Redis caching

### Phase 2 (Q2 2025)
- Add request logging/tracing (OpenTelemetry)
- Add monitoring dashboard (Prometheus + Grafana)
- Database read replicas

### Phase 3 (Q3 2025)
- Move ML to async job queue (BullMQ)
- Add CDN for frontend assets
- Multi-region deployment
- Real-time WebSocket updates

### Phase 4 (Growth)
- GraphQL federation
- Event-driven architecture (Kafka)
- Real-time ML retraining pipeline
- Multi-region database replication
