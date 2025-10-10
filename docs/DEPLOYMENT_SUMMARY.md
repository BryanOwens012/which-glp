# WhichGLP Deployment Summary

## Current Architecture: 9 Railway Services + Vercel Frontend

### Production Infrastructure

**Vercel:**
- **Frontend** (Next.js 15) - `whichglp.com`

**Railway** (9 services):
1. **API** (Node.js tRPC) - `api.whichglp.com`
2. **Rec-Engine** (Python ML) - `whichglp-rec-engine.up.railway.app`
3. **Post-Ingestion** (Python) - `whichglp-post-ingestion.up.railway.app`
4. **Post-Extraction** (Python + GLM-4.5-Air) - `whichglp-post-extraction.up.railway.app`
5. **User-Extraction** (Python + GLM-4.5-Air) - `whichglp-user-extraction.up.railway.app`
6. **Redis** (Cache) - Persistent volume
7. **View-Refresher-Cron** - Every 2 days
8. **Post-Ingestion-Cron** - Every 2 days
9. **Post-Extraction-Cron** - Every 2 days
10. **User-Extraction-Cron** - Every 2 days

**External:**
- **Supabase** - PostgreSQL database

### Key Features

✅ **Microservices Architecture** - Each service independently scalable
✅ **Cron-Based Automation** - Automated data pipeline (ingestion → extraction → view refresh)
✅ **AI Processing** - GLM-4.5-Air for cost-effective extraction
✅ **ML Recommendations** - KNN-based drug matching
✅ **Redis Caching** - Fast API responses

---

## Local Development

### Start All Services

```bash
# Terminal 1: Frontend
cd apps/frontend
npm run dev

# Terminal 2: API
cd apps/api
npm run dev

# Terminal 3: Rec-Engine
cd apps/rec-engine
python3 api.py

# Terminal 4: Post-Ingestion
cd apps/post-ingestion
uvicorn api:app --reload

# Terminal 5: Post-Extraction
cd apps/post-extraction
uvicorn api:app --reload

# Terminal 6: User-Extraction
cd apps/user-extraction
uvicorn api:app --reload

# Terminal 7: Redis
redis-server
```

### Test the Stack

```bash
# Test all health endpoints
curl http://localhost:8000/health  # API
curl http://localhost:8001/health  # Rec-Engine
curl http://localhost:8002/health  # User-Extraction
curl http://localhost:8003/health  # Post-Ingestion
curl http://localhost:8004/health  # Post-Extraction

# Test frontend
open http://localhost:3000
```

**Note:** Port assignments are managed by uvicorn/FastAPI and configured via environment variables or defaults.

---

## Railway Deployment

### Current Services (9 total)

| Service | Type | Trigger |
|---------|------|---------|
| whichglp-api | Node.js | Always-on |
| whichglp-rec-engine | Python | Always-on |
| whichglp-post-ingestion | Python | Cron (2 days) |
| whichglp-post-extraction | Python | Cron (2 days) |
| whichglp-user-extraction | Python | Cron (2 days) |
| redis | Database | Always-on |
| View-Refresher-Cron | Cron | Every 2 days |
| Post-Ingestion-Cron | Cron | Every 2 days |
| Post-Extraction-Cron | Cron | Every 2 days |
| User-Extraction-Cron | Cron | Every 2 days |

### Environment Variables

**API Service:**
```bash
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
REDIS_URL=${{Redis.REDIS_URL}}
REC_ENGINE_URL=https://whichglp-rec-engine.up.railway.app
```

**Python Services (all):**
```bash
SUPABASE_URL=...
SUPABASE_SERVICE_KEY=...
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
REDDIT_USER_AGENT=whichglp-ingestion/0.1
ZAI_API_KEY=...
PORT=${{RAILWAY_PUBLIC_PORT}}
```

### Deployment Process

1. Push to GitHub `main` branch
2. Railway auto-deploys all services
3. Verify health checks
4. Monitor logs for errors

---

## Testing Checklist

### Production Health Checks

```bash
curl https://api.whichglp.com/health
curl https://whichglp-rec-engine.up.railway.app/health
curl https://whichglp-post-ingestion.up.railway.app/health
curl https://whichglp-post-extraction.up.railway.app/health
curl https://whichglp-user-extraction.up.railway.app/health
```

### Monitor Logs

```bash
railway logs --service whichglp-api
railway logs --service whichglp-rec-engine
railway logs --service whichglp-post-ingestion
railway logs --service whichglp-post-extraction
railway logs --service whichglp-user-extraction
```

---

## Architecture Overview

See `docs/ARCHITECTURE.md` for detailed architecture documentation including:
- Complete service descriptions
- Data flow diagrams
- Environment setup
- Deployment guides
- Architecture decisions (microservices, cron jobs, GLM-4.5-Air)

### Quick Reference

**Data Pipeline Flow:**
```
Post-Ingestion → reddit_posts table
                 ↓
Post-Extraction → extracted_features table
                 ↓
User-Extraction → user_demographics table
                 ↓
View-Refresher → mv_experiences_denormalized
```

**Request Flow:**
```
Frontend (Vercel) → API (Railway) → Rec-Engine (Railway) → Supabase
                                   ↓
                                Redis Cache
```

---

## Future Enhancements

- [ ] Request logging/tracing (OpenTelemetry)
- [ ] Rate limiting (Redis-based)
- [ ] Monitoring dashboard (Prometheus + Grafana)
- [ ] Database read replicas
- [ ] Async job queue (BullMQ)
- [ ] CDN for frontend assets
- [ ] Multi-region deployment

---

## Documentation

- **Architecture:** `docs/ARCHITECTURE.md`
- **Tech Spec:** `docs/TECH_SPEC.md`
- **Railway Setup:** `docs/RAILWAY_SETUP.md`
- **Cron Setup:** `docs/RAILWAY_CRON_SETUP.md`

**Status**: ✅ Production deployment active
