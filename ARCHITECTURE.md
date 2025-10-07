# WhichGLP Architecture

## Monorepo Structure

This is a monorepo containing three independent services:

```
which-glp/
├── apps/
│   ├── frontend/        # Next.js 15 app
│   ├── backend/         # Node.js tRPC API
│   └── ml/              # Python FastAPI service
├── apps/data-ingestion/ # Python Reddit scraper (separate tooling)
├── venv/                # Python virtual environment (shared)
├── requirements.txt     # Python dependencies (shared)
└── package.json         # Root workspace config
```

## Service Architecture

### 1. Frontend (`apps/frontend`)

**Tech Stack:**
- Next.js 15 (App Router)
- React 19
- TypeScript
- Tailwind CSS v4
- tRPC client

**Responsibilities:**
- User-facing web application
- Forms for user input (weight, goals, preferences)
- Display drug recommendations
- Browse community experiences

**Port:** 3000 (local) / Railway domain (production)

**Deployment:**
- Railway service: `whichglp-frontend`
- Build command: `npm run build`
- Start command: `npm start`

---

### 2. Backend (`apps/backend`)

**Tech Stack:**
- Node.js 18+
- TypeScript
- tRPC (type-safe API)
- Supabase client
- Redis for caching

**Responsibilities:**
- API layer for frontend
- Fetch experiences from Supabase
- Aggregate statistics
- Call ML API for recommendations
- Handle caching

**Port:** 8000 (local) / Railway domain (production)

**Key Endpoints (tRPC procedures):**
- `experiences.list` - Get filtered experiences
- `experiences.getById` - Get single experience
- `experiences.getStats` - Get aggregated stats
- `recommendations.getForUser` - Get personalized recommendations (calls ML API)

**Deployment:**
- Railway service: `whichglp-backend`
- Build command: `npm run build`
- Start command: `npm start`
- Environment variables:
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY`
  - `REDIS_URL`
  - `ML_URL` (points to ML service)

---

### 3. ML API (`apps/ml`)

**Tech Stack:**
- Python 3.13
- FastAPI
- Uvicorn
- scikit-learn (KNN)
- pandas
- Supabase client

**Responsibilities:**
- Machine learning recommendations
- KNN-based user matching
- Drug ranking algorithm
- Side effect prediction
- Cost estimation

**Port:** 8001 (local) / Railway domain (production)

**Key Endpoints (REST):**
- `POST /api/recommendations` - Get recommendations
- `GET /health` - Health check
- `GET /api/cache/clear` - Clear cache

**Deployment:**
- Railway service: `whichglp-ml`
- Start command: `cd apps/ml && python3 api.py`
- Environment variables:
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_KEY`
  - `ML_PORT`

---

## Data Flow

### Recommendation Request

```
┌─────────┐     tRPC      ┌─────────┐    HTTP      ┌────────┐
│ Frontend│─────────────►│ Backend │────────────►│ ML API │
│ (Next)  │              │ (tRPC)  │             │(FastAPI)│
└─────────┘              └─────────┘             └────────┘
                              │                       │
                              │                       │
                              ▼                       ▼
                         ┌──────────────────────────────┐
                         │        Supabase DB           │
                         │   (experiences, features)    │
                         └──────────────────────────────┘
```

**Steps:**
1. User fills form on frontend
2. Frontend calls `recommendations.getForUser` via tRPC
3. Backend forwards request to ML API via HTTP
4. ML API:
   - Fetches experiences from Supabase
   - Runs KNN algorithm
   - Ranks drugs
   - Returns recommendations
5. Backend returns to frontend
6. Frontend displays recommendations

### Experience Browsing

```
┌─────────┐     tRPC      ┌─────────┐
│ Frontend│─────────────►│ Backend │
│ (Next)  │              │ (tRPC)  │
└─────────┘              └─────────┘
                              │
                              ▼
                         ┌────────┐
                         │ Redis  │ (cache)
                         └────────┘
                              │
                              ▼
                         ┌────────┐
                         │Supabase│
                         └────────┘
```

**Steps:**
1. Frontend calls `experiences.list`
2. Backend checks Redis cache
3. If miss, query Supabase
4. Cache result in Redis
5. Return to frontend

---

## Why Separate ML Service?

### Pros
✅ **Independent Scaling**: ML is compute-intensive, can scale separately
✅ **Process Isolation**: Python crashes don't affect Node.js API
✅ **Technology Optimization**: Use Python ML ecosystem without Node.js overhead
✅ **Faster Deployments**: Change ML model without redeploying API
✅ **Simpler Testing**: Test ML logic independently

### Cons
❌ **Network Latency**: ~20-50ms overhead for HTTP call
❌ **More Complex Deployment**: 2 services instead of 1
❌ **Higher Cost**: 2 Railway services (but still cheap at low scale)

### Trade-off Decision
For WhichGLP, the pros outweigh the cons because:
- Recommendation requests are async (latency acceptable)
- ML model will evolve independently
- Backend has other non-ML responsibilities

---

## Local Development

### Start all services

```bash
# Terminal 1: Frontend
cd apps/frontend
npm run dev

# Terminal 2: Backend
cd apps/backend
npm run dev

# Terminal 3: ML API
cd apps/ml
./start_api.sh
```

### Environment Setup

1. **Root `.env`** (for Python services):
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_DB_PASSWORD=your-db-password
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
```

2. **`apps/frontend/.env.local`**:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

3. **`apps/backend/.env`**:
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
REDIS_URL=redis://localhost:6379
ML_URL=http://localhost:8001
```

---

## Railway Deployment Guide

### Step 1: Frontend Service

1. Create new service: `whichglp-frontend`
2. Connect to GitHub
3. Settings:
   - Root directory: `apps/frontend`
   - Build command: `npm run build`
   - Start command: `npm start`
4. Environment variables:
   - `NEXT_PUBLIC_API_URL=https://your-backend.railway.app`

### Step 2: Backend Service

1. Create new service: `whichglp-backend`
2. Connect to GitHub
3. Settings:
   - Root directory: `apps/backend`
   - Build command: `npm run build`
   - Start command: `npm start`
4. Environment variables:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `REDIS_URL` (from Railway Redis addon)
   - `ML_URL=https://your-ml.railway.app`

### Step 3: ML API Service

1. Create new service: `whichglp-ml`
2. Connect to GitHub
3. Settings:
   - Root directory: `/` (monorepo root)
   - Start command: `cd apps/ml && python3 api.py`
   - Health check: `/health`
4. Environment variables:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_KEY`
   - `ML_PORT=8001`

### Step 4: Link Services

Update backend environment:
```bash
ML_URL=https://whichglp-ml.railway.app
```

Update frontend environment:
```bash
NEXT_PUBLIC_API_URL=https://whichglp-backend.railway.app
```

---

## Database Schema

See `apps/data-ingestion/migrations/` for SQL schema.

### Key Tables

- `reddit_posts` - Raw Reddit posts
- `reddit_comments` - Raw Reddit comments
- `extracted_features` - AI-extracted structured data
- `mv_experiences_denormalized` - Materialized view for fast queries

---

## Testing

### Frontend
```bash
cd apps/frontend
npm run lint
npm run build  # Type checking
```

### Backend
```bash
cd apps/backend
npm run lint
npm run build
npm test
```

### ML API
```bash
cd apps/ml
pytest test_recommender.py -v
```

---

## Monitoring

### Health Checks

```bash
# Frontend
curl https://your-frontend.railway.app

# Backend
curl https://your-backend.railway.app/health

# ML API
curl https://your-ml.railway.app/health
```

### Logs

```bash
railway logs --service whichglp-frontend
railway logs --service whichglp-backend
railway logs --service whichglp-ml
```

---

## Future Architecture

### Phase 1 (Current)
- Monorepo with 3 services
- Direct HTTP calls between services
- In-memory caching in ML API

### Phase 2 (Near Future)
- Add Redis to ML API for experience caching
- Add request logging/tracing
- Add rate limiting

### Phase 3 (Scale)
- Move ML to async job queue (BullMQ)
- Add CDN for frontend
- Add database read replicas
- Add monitoring (Prometheus/Grafana)

### Phase 4 (Growth)
- Microservices for each drug type
- Real-time ML retraining pipeline
- GraphQL federation
- Multi-region deployment
