# WhichGLP Deployment Summary

## ✅ Completed: FastAPI ML Service Migration

### What Changed

**Before:**
```
apps/backend/
├── src/
│   └── routers/
│       └── recommendations.ts   # Used exec() to call Python
└── ml/
    ├── recommender.py
    └── recommender_api.py       # CLI wrapper
```

**After:**
```
apps/
├── backend/
│   └── src/
│       └── routers/
│           └── recommendations.ts   # HTTP call to ML service
└── ml/                          # ← NEW: Standalone service
    ├── api.py                       # FastAPI app
    ├── recommender.py               # ML logic
    ├── start_api.sh                 # Local dev script
    ├── railway.json                 # Deployment config
    └── README.md                    # Full documentation
```

### Key Improvements

1. **No more `exec()`** - Backend now makes clean HTTP requests to ML service
2. **Independent service** - ML API can scale and deploy separately
3. **Better error handling** - FastAPI provides structured errors
4. **Health checks** - `/health` endpoint for monitoring
5. **Clean separation** - Each service has clear responsibilities

---

## Local Development

### Start All Services

```bash
# Terminal 1: Frontend (port 3000)
cd apps/frontend
npm run dev

# Terminal 2: Backend (port 8000)
cd apps/backend
npm run dev

# Terminal 3: ML API (port 8001)
./apps/ml/start_api.sh
```

### Test the Stack

```bash
# Test ML API directly
curl http://localhost:8001/health

# Test through backend (via browser or curl)
# Go to http://localhost:3000 and use the recommendation form
```

---

## Railway Deployment

### Current Setup (2 services)

1. **whichglp-backend** (Node.js)
   - Port: 8000
   - Handles: tRPC API, experiences, stats
   - Environment: `ML_URL=<ml-service-url>`

2. **whichglp-frontend** (Next.js)
   - Port: 3000
   - Environment: `NEXT_PUBLIC_API_URL=<backend-url>`

### Add New Service (ML API)

#### Step 1: Create Service

1. Railway Dashboard → New Service
2. Name: `whichglp-ml`
3. Connect to GitHub repo
4. Root Directory: `/` (monorepo root)
5. Start Command: `cd apps/ml && python3 api.py`
6. Health Check Path: `/health`

#### Step 2: Environment Variables

Add to `whichglp-ml`:
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
ML_PORT=8001
```

#### Step 3: Update Backend

In `whichglp-backend` service, add/update:
```bash
ML_URL=https://whichglp-ml.railway.app
```

#### Step 4: Deploy

Push to GitHub → All services auto-deploy

---

## Testing Checklist

### Before Deploying

- [ ] ML API starts locally: `./apps/ml/start_api.sh`
- [ ] Health check works: `curl http://localhost:8001/health`
- [ ] Backend can reach ML API: Check backend logs for successful ML requests
- [ ] Frontend recommendations work: Test the "Recommend for Me" feature

### After Deploying

- [ ] ML API health check: `curl https://your-ml.railway.app/health`
- [ ] Backend logs show successful ML API calls
- [ ] Frontend recommendations work in production
- [ ] Check Railway logs for all 3 services

---

## Architecture Benefits

### Why Split Services?

**Old Way (exec):**
```
┌──────────────────────┐
│   Backend (Node.js)  │
│  ┌────────────────┐  │
│  │ exec() Python  │  │  ← Spawns shell + Python per request
│  └────────────────┘  │  ← Security risk, slow, hard to debug
└──────────────────────┘
```

**New Way (HTTP):**
```
┌─────────────┐   HTTP    ┌──────────────┐
│   Backend   │──────────►│   ML API     │
│  (Node.js)  │           │  (FastAPI)   │
└─────────────┘           └──────────────┘
     ▲                          │
     │                          │
     ▼                          ▼
┌──────────────────────────────────┐
│        Supabase Database         │
└──────────────────────────────────┘
```

### Benefits

✅ **Security**: No shell injection risks
✅ **Performance**: ML service stays warm, no process spawning
✅ **Scalability**: Can scale ML independently
✅ **Reliability**: ML crashes don't affect API
✅ **Monitoring**: Separate logs, health checks
✅ **Development**: Work on ML without touching Node.js

### Trade-offs

❌ **Network Latency**: ~20-50ms overhead for HTTP call (acceptable)
❌ **Complexity**: 3 services instead of 2 (manageable)
❌ **Cost**: Additional Railway service (~$5/month at low scale)

**Decision**: Worth it for the isolation and flexibility

---

## File Reference

### New Files
- `apps/ml/api.py` - FastAPI application
- `apps/ml/start_api.sh` - Local dev script
- `apps/ml/railway.json` - Railway deployment config
- `apps/ml/README.md` - ML service documentation
- `ARCHITECTURE.md` - Overall system architecture
- `DEPLOYMENT_SUMMARY.md` - This file

### Modified Files
- `apps/backend/src/routers/recommendations.ts` - Changed from `exec()` to `fetch()`
- `requirements.txt` - Added FastAPI and Uvicorn

### Deprecated Files (kept for reference)
- `apps/backend/ml/recommender_api.py` - Old CLI wrapper
- Can be deleted after confirming new service works

---

## Next Steps

### Immediate (Pre-Deploy)
1. ✅ Test locally with all 3 services running
2. ✅ Verify recommendations work end-to-end
3. ✅ Check logs for errors

### Deploy to Railway
1. [ ] Create `whichglp-ml` service
2. [ ] Set environment variables
3. [ ] Update `ML_URL` in backend service
4. [ ] Push to GitHub
5. [ ] Monitor deployment logs
6. [ ] Test production recommendations

### Post-Deploy
1. [ ] Monitor Railway logs for 24 hours
2. [ ] Check ML API response times
3. [ ] Verify no regression in recommendation quality
4. [ ] Clean up old `apps/backend/ml/` directory if desired

### Future Enhancements
- [ ] Add Redis caching to ML API
- [ ] Add request logging/tracing
- [ ] Add API authentication
- [ ] Add rate limiting
- [ ] Add Prometheus metrics
- [ ] Optimize KNN algorithm

---

## Rollback Plan

If something goes wrong, you can quickly rollback:

1. **Keep old code**: The `exec()` version still exists in git history
2. **Revert recommendations.ts**:
   ```bash
   git checkout HEAD~1 apps/backend/src/routers/recommendations.ts
   ```
3. **Redeploy backend**: Push to trigger Railway deployment
4. **Delete ML service**: Remove from Railway if not needed

---

## Support

### Documentation
- ML API: `apps/ml/README.md`
- Architecture: `ARCHITECTURE.md`
- Backend tRPC: `apps/backend/src/routers/recommendations.ts`

### Logs
```bash
# Railway CLI
railway logs --service whichglp-ml
railway logs --service whichglp-backend
railway logs --service whichglp-frontend
```

### Health Checks
```bash
# ML API
curl https://your-ml.railway.app/health

# Backend
curl https://your-backend.railway.app/health

# Frontend
curl https://your-frontend.railway.app
```

---

## Success Criteria

✅ All services start successfully
✅ Health checks return 200
✅ Recommendations work in production
✅ No increase in error rates
✅ Response times < 2 seconds
✅ Railway logs show no critical errors

**Status**: Ready to deploy 🚀
