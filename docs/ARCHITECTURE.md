# WhichGLP Architecture

## Monorepo Structure

This is a monorepo containing 5 backend services, 1 frontend, and automated cron jobs:

```
which-glp/
├── apps/
│   ├── frontend/          # Next.js 15 app (Vercel)
│   ├── api/               # Node.js tRPC API (Railway)
│   ├── rec-engine/        # Python ML recommendations (Railway)
│   ├── post-ingestion/    # Python Reddit ingestion (Railway)
│   ├── post-extraction/   # Python AI extraction (Railway)
│   ├── user-extraction/   # Python user demographics (Railway)
│   └── shared/            # Shared database migrations
├── scripts/
│   ├── legacy-ingestion/  # Legacy Python Reddit scraper
│   └── cron/              # Cron trigger scripts (Railway)
├── venv/                  # Python virtual environment (shared)
├── requirements.txt       # Python dependencies (shared)
└── package.json           # Root workspace config
```

## Service Architecture

### 1. Frontend (`apps/frontend`)

**Tech Stack:**
- Next.js 15 (App Router)
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
- Auto-deploys from `main` branch
- Environment variables:
  - `NEXT_PUBLIC_API_URL` - API service URL
  - `NEXT_PUBLIC_GA_TAG` - Google Analytics tag

---

###2. API Service (`apps/api`)

**Tech Stack:**
- Node.js 20+
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

**Port:** 8000

**Key Endpoints (tRPC procedures):**
- `experiences.list` - Get filtered experiences
- `experiences.getById` - Get single experience
- `experiences.getStats` - Get aggregated stats
- `recommendations.getForUser` - Get personalized recommendations

**Deployment:**
- Platform: Railway
- Service: `whichglp-api`
- Domain: `api.whichglp.com`
- Build command: `npm run build`
- Start command: `npm start`
- Environment variables:
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY`
  - `REDIS_URL`
  - `REC_ENGINE_URL`

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

**Port:** 8001

**Key Endpoints (REST):**
- `POST /api/recommendations` - Get recommendations
- `GET /health` - Health check
- `GET /api/cache/clear` - Clear cache

**Deployment:**
- Platform: Railway
- Service: `whichglp-rec-engine`
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
- Triggered by cron job every 16 hours

**Port:** 8003

**Key Endpoints (REST):**
- `POST /api/ingest` - Trigger ingestion
- `GET /api/status` - Check ingestion status
- `GET /health` - Health check

**Deployment:**
- Platform: Railway
- Service: `whichglp-post-ingestion`
- Domain: `whichglp-post-ingestion.up.railway.app`
- Start command: `cd apps/post-ingestion && python3 api.py`
- Triggered by: `Post-Ingestion-Cron` (every 16 hours)

---

### 5. Post Extraction (`apps/post-extraction`)

**Tech Stack:**
- Python 3.13
- FastAPI + uvicorn
- GLM-4.5-Air (Z.ai SDK)
- Supabase client

**Responsibilities:**
- Extract structured drug experience data from posts
- AI-powered feature extraction (drug, weight loss, cost, side effects)
- Store in `extracted_features` table
- Triggered by cron job every 22 hours

**Port:** 8004

**Key Endpoints (REST):**
- `POST /api/extract` - Trigger extraction
- `GET /api/status` - Check extraction status
- `GET /health` - Health check

**Deployment:**
- Platform: Railway
- Service: `whichglp-post-extraction`
- Domain: `whichglp-post-extraction.up.railway.app`
- Start command: `cd apps/post-extraction && python3 api.py`
- Triggered by: `Post-Extraction-Cron` (every 22 hours)

---

### 6. User Extraction (`apps/user-extraction`)

**Tech Stack:**
- Python 3.13
- FastAPI + uvicorn
- GLM-4.5-Air (Z.ai SDK)
- Supabase client

**Responsibilities:**
- Extract user demographics from Reddit user history
- AI-powered demographic extraction (age, sex, location)
- Store in `user_demographics` table
- Triggered by cron job daily

**Port:** 8002

**Key Endpoints (REST):**
- `POST /api/analyze` - Trigger user analysis
- `GET /api/stats` - Get analysis statistics
- `GET /api/status` - Check analysis status
- `GET /health` - Health check

**Deployment:**
- Platform: Railway
- Service: `whichglp-user-extraction`
- Domain: `whichglp-user-extraction.up.railway.app`
- Start command: `cd apps/user-extraction && python3 api.py`
- Triggered by: `User-Extraction-Cron` (daily)

---

## Cron Jobs (Automated Scheduling)

### 1. View-Refresher-Cron

**Schedule:** Every 45 minutes
**Function:** Refreshes materialized views in Supabase
**Implementation:** Railway Cron Schedule
**Script:** `scripts/cron/refresh-views.js`

### 2. Post-Ingestion-Cron

**Schedule:** Every 16 hours
**Function:** Triggers `POST /api/ingest` on Post-Ingestion service
**Implementation:** Railway Cron Schedule
**Target:** `whichglp-post-ingestion.up.railway.app/api/ingest`

### 3. Post-Extraction-Cron

**Schedule:** Every 22 hours
**Function:** Triggers `POST /api/extract` on Post-Extraction service
**Implementation:** Railway Cron Schedule
**Target:** `whichglp-post-extraction.up.railway.app/api/extract`

### 4. User-Extraction-Cron

**Schedule:** Daily (24 hours)
**Function:** Triggers `POST /api/analyze` on User-Extraction service
**Implementation:** Railway Cron Schedule
**Target:** `whichglp-user-extraction.up.railway.app/api/analyze`

---

## Infrastructure Services

### Redis

**Platform:** Railway
**Type:** Redis Database with persistent volume
**Volume:** `redis-volume`
**Function:** Caching layer for API service
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
│ Post-Ingestion   │ ◄─── Cron (every 16 hours)
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
│ Post-Extraction  │ ◄─── Cron (every 22 hours)
│ (GLM-4.5-Air)    │
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
│ (GLM-4.5-Air)    │
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
│ View-Refresher   │ ◄─── Cron (every 45 min)
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

**Total Services: 9**

| Service | Type | Port | Schedule |
|---------|------|------|----------|
| API | Node.js | 8000 | Always-on |
| Rec-Engine | Python | 8001 | Always-on |
| Post-Ingestion | Python | 8003 | Always-on (HTTP triggered) |
| Post-Extraction | Python | 8004 | Always-on (HTTP triggered) |
| User-Extraction | Python | 8002 | Always-on (HTTP triggered) |
| Redis | Database | 6379 | Always-on |
| View-Refresher-Cron | Cron | N/A | Every 45 minutes |
| Post-Ingestion-Cron | Cron | N/A | Every 16 hours |
| Post-Extraction-Cron | Cron | N/A | Every 22 hours |
| User-Extraction-Cron | Cron | N/A | Daily |

**Note:** Frontend is deployed on Vercel separately.

---

## Local Development

### Start all services

```bash
# Terminal 1: Frontend
cd apps/frontend
npm run dev  # http://localhost:3000

# Terminal 2: API
cd apps/api
npm run dev  # http://localhost:8000

# Terminal 3: Rec-Engine
cd apps/rec-engine
python3 api.py  # http://localhost:8001

# Terminal 4: Post-Ingestion
cd apps/post-ingestion
python3 api.py  # http://localhost:8003

# Terminal 5: Post-Extraction
cd apps/post-extraction
python3 api.py  # http://localhost:8004

# Terminal 6: User-Extraction
cd apps/user-extraction
python3 api.py  # http://localhost:8002

# Terminal 7: Redis
redis-server  # localhost:6379
```

### Environment Setup

1. **Root `.env`** (for Python services):
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_DB_PASSWORD=your-db-password
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
REDDIT_CLIENT_ID=your-client-id
REDDIT_CLIENT_SECRET=your-client-secret
REDDIT_USER_AGENT=whichglp-ingestion/0.1
ZAI_API_KEY=your-zai-api-key
```

2. **`apps/frontend/.env.local`**:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_GA_TAG=your-ga-tag
```

3. **`apps/api/.env`**:
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
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
railway logs --service whichglp-api
railway logs --service whichglp-rec-engine
railway logs --service whichglp-post-ingestion
railway logs --service whichglp-post-extraction
railway logs --service whichglp-user-extraction
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
❌ **More Complex Deployment**: 9 services vs 1 monolith
❌ **Higher Cost**: Multiple Railway services (mitigated by efficient scheduling)

### Why Cron Jobs Instead of Always-Running?

**Reasoning:**
- Data ingestion doesn't need to run 24/7
- Reddit posts arrive at predictable rates
- Cron jobs reduce Railway costs (pay for compute time, not idle time)
- FastAPI services boot quickly (~2-5 seconds)
- 16-22 hour intervals ensure fresh data without wasted cycles

### Why GLM-4.5-Air Instead of Claude?

**Cost Comparison:**
- Claude Sonnet 4: $3/1M input tokens, $15/1M output tokens
- GLM-4.5-Air: ~$0.50/1M tokens (via Z.ai SDK)
- **Savings: ~85% cost reduction**

**Trade-offs:**
- Slightly lower quality extractions (~5-10% less accurate)
- Faster response times (optimized for speed)
- Good enough for text extraction, summarization, sentiment analysis
- Can always upgrade to Claude for critical extractions

---

## Future Architecture

### Phase 1 (Current)
✅ Monorepo with 9 Railway services
✅ Cron-based automation
✅ Redis caching

### Phase 2 (Q2 2025)
- Add request logging/tracing (OpenTelemetry)
- Add rate limiting (Redis-based)
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
