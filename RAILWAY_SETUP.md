# Railway Deployment Setup

## Services Overview

WhichGLP requires 3 separate Railway services:

1. **whichglp-frontend** - Next.js app
2. **whichglp-backend** - Node.js tRPC API
3. **whichglp-ml** - Python FastAPI service

## Service 1: ML API

### Create Service
1. Railway Dashboard → New Service
2. Name: `whichglp-ml`
3. Connect to GitHub repo
4. Settings:
   - **Root Directory**: `/` (monorepo root)
   - **Start Command**: `cd apps/ml && python3 api.py`
   - **Health Check Path**: `/health`
   - **Watch Paths**: `apps/ml/**`

### Environment Variables
```bash
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key-here

# Optional
ML_PORT=8001  # Railway will override with PORT
```

### Generate Domain
1. Settings → Networking → Generate Domain
2. Copy the domain (e.g., `whichglp-ml.railway.app`)
3. Save for next step

### Notes
- Railway will automatically install Python dependencies from `requirements.txt`
- The service listens on `0.0.0.0:8001` which works for Railway's port binding
- Health check ensures the service is running before marking as healthy

---

## Service 2: Backend API

### Create Service
1. Railway Dashboard → New Service
2. Name: `whichglp-backend`
3. Connect to GitHub repo
4. Settings:
   - **Root Directory**: `apps/backend`
   - **Build Command**: `npm run build`
   - **Start Command**: `npm start`
   - **Watch Paths**: `apps/backend/**`, `apps/shared/**`

### Environment Variables
```bash
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here

# ML API Connection (IMPORTANT)
ML_URL=https://whichglp-ml.railway.app

# Redis (from Railway Redis plugin)
REDIS_URL=redis://default:password@redis.railway.internal:6379

# Optional
NODE_ENV=production
```

### Add Redis Plugin
1. Service → New → Database → Add Redis
2. Railway will automatically set `REDIS_URL`
3. Redis connection uses `family: 0` for IPv4/IPv6 compatibility

### Generate Domain
1. Settings → Networking → Generate Domain
2. Copy the domain for frontend configuration

### Notes
- **ML_URL is critical** - must point to the ML service's Railway domain
- Node.js v20+ recommended (v18 deprecated by Supabase)
- Redis connection configured with dual-stack DNS (`family: 0`)

---

## Service 3: Frontend

### Create Service
1. Railway Dashboard → New Service
2. Name: `whichglp-frontend`
3. Connect to GitHub repo
4. Settings:
   - **Root Directory**: `apps/frontend`
   - **Build Command**: `npm run build`
   - **Start Command**: `npm start`
   - **Watch Paths**: `apps/frontend/**`, `apps/shared/**`

### Environment Variables
```bash
# Required
NEXT_PUBLIC_API_URL=https://whichglp-backend.railway.app

# Optional
NODE_ENV=production
```

### Generate Domain
1. Settings → Networking → Generate Domain
2. This is your public-facing URL

### Notes
- `NEXT_PUBLIC_*` variables are embedded at build time
- Frontend makes tRPC calls to the backend service

---

## IPv4/IPv6 Considerations

### Problem
Railway services can have IPv6-only or dual-stack networking, which can cause connection issues if not handled properly.

### Solutions Implemented

#### 1. Redis Connection (`apps/backend/src/lib/redis.ts`)
```typescript
{
  family: 0,  // 0 = dual-stack (try IPv6, fallback to IPv4)
  keepAlive: 30000,
  connectTimeout: 10000
}
```

#### 2. ML API Connection (`apps/backend/src/routers/recommendations.ts`)
```typescript
// Locally: use 127.0.0.1 (IPv4) instead of localhost
// On Railway: use ML_URL env var (handles DNS automatically)
const mlApiUrl = process.env.ML_URL || 'http://127.0.0.1:8001'
```

#### 3. FastAPI Service (`apps/ml/api.py`)
```python
# Listen on 0.0.0.0 (all interfaces, IPv4 and IPv6)
uvicorn.run(
    "api:app",
    host="0.0.0.0",
    port=port,
)
```

### Railway's Internal Networking
- Railway provides internal DNS for service-to-service communication
- Internal URLs (`.railway.internal`) work correctly with both IPv4/IPv6
- Public URLs (`.railway.app`) also handle both protocols
- Use environment variables with full URLs (don't rely on localhost/127.0.0.1)

---

## Deployment Checklist

### Before First Deploy
- [ ] All services created in Railway
- [ ] Environment variables set for each service
- [ ] `ML_URL` in backend points to ML service domain
- [ ] `NEXT_PUBLIC_API_URL` in frontend points to backend domain
- [ ] Redis plugin added to backend service
- [ ] Domains generated for all services

### After Deploy
- [ ] Check ML API health: `curl https://whichglp-ml.railway.app/health`
- [ ] Check backend logs for successful ML API connection
- [ ] Test frontend recommendations feature
- [ ] Monitor Railway logs for all 3 services

### Common Issues

**Issue**: Backend can't connect to ML API
**Solution**: Verify `ML_URL` is set correctly in backend environment variables

**Issue**: Redis connection refused
**Solution**: Check Redis plugin is added and `REDIS_URL` is set

**Issue**: Frontend can't reach backend
**Solution**: Verify `NEXT_PUBLIC_API_URL` is correct and rebuild frontend

**Issue**: ML API crashes on startup
**Solution**: Check `SUPABASE_SERVICE_KEY` is set and Python dependencies installed

---

## Service-to-Service Communication

```
┌──────────┐                           ┌──────────┐
│ Frontend │ ──── HTTPS (public) ────► │ Backend  │
│ (Next.js)│                           │ (tRPC)   │
└──────────┘                           └──────────┘
                                             │
                                             │ HTTP (internal)
                                             ▼
                                       ┌──────────┐
                                       │  ML API  │
                                       │ (FastAPI)│
                                       └──────────┘
```

- **Frontend → Backend**: Public HTTPS via Railway domain
- **Backend → ML API**: Internal HTTP via Railway's private network (faster, free bandwidth)
- **Backend → Redis**: Internal connection via `redis.railway.internal`
- **ML API → Supabase**: External HTTPS

---

## Cost Optimization

### Railway Pricing (as of 2025)
- **Hobby Plan**: $5/month + usage
- **Pro Plan**: $20/month + usage
- Usage: ~$0.000463 per GB-hour

### Estimated Monthly Costs (Hobby Plan)
- Frontend: ~512MB RAM × 720 hours = ~$0.17/month
- Backend: ~512MB RAM × 720 hours = ~$0.17/month
- ML API: ~1GB RAM × 720 hours = ~$0.33/month
- Redis: ~256MB RAM × 720 hours = ~$0.08/month
- **Total**: ~$0.75/month (plus $5 base) = **~$5.75/month**

### Optimization Tips
1. Use hobby plan for MVP stage
2. Enable auto-scaling only if needed
3. Use Redis caching to reduce ML API calls
4. Monitor usage in Railway dashboard

---

## Monitoring & Logs

### View Logs
```bash
# Railway CLI
railway logs --service whichglp-ml
railway logs --service whichglp-backend
railway logs --service whichglp-frontend
```

### Health Checks
```bash
# ML API
curl https://whichglp-ml.railway.app/health

# Backend (via frontend)
curl https://whichglp-frontend.railway.app/api/trpc/platform.getStats

# Frontend
curl https://whichglp-frontend.railway.app
```

### Metrics to Monitor
- **ML API**: Response times, error rates, cache hit rate
- **Backend**: tRPC call success rate, Redis connection status
- **Frontend**: Page load times, API call success rate

---

## Rollback Procedure

If deployment fails:

1. **Railway Dashboard**: Go to service → Deployments → Click previous successful deployment → "Redeploy"

2. **CLI**:
```bash
railway rollback --service whichglp-backend
```

3. **Git**:
```bash
git revert HEAD
git push
```

Railway will automatically redeploy on push.

---

## Production Readiness

### Security
- [ ] Environment variables properly set (no hardcoded secrets)
- [ ] CORS configured correctly in ML API
- [ ] Rate limiting added (future)
- [ ] API authentication added (future)

### Performance
- [ ] Redis caching enabled
- [ ] ML API responses under 2 seconds
- [ ] Health checks passing
- [ ] Auto-scaling configured (if needed)

### Monitoring
- [ ] Railway metrics dashboard configured
- [ ] Error tracking set up (Sentry, etc.)
- [ ] Uptime monitoring (Uptime Robot, etc.)
- [ ] Log aggregation (Railway logs or external)

---

## Support & Documentation

- Railway Docs: https://docs.railway.com
- Redis IPv6 Fix: https://docs.railway.com/reference/errors/enotfound-redis-railway-internal
- FastAPI Deployment: https://fastapi.tiangolo.com/deployment/
- Node.js Best Practices: https://docs.railway.com/guides/nodejs

For project-specific issues, see:
- `ARCHITECTURE.md` - System architecture
- `DEPLOYMENT_SUMMARY.md` - Migration summary
- `apps/ml/README.md` - ML service docs
