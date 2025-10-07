# WhichGLP ML API

FastAPI microservice for drug recommendations based on user profiles and real-world Reddit data.

## Architecture

This is a **standalone Python service** separate from the Node.js API:

```
apps/
├── frontend/        # Next.js app (port 3000)
├── api/             # Node.js tRPC API (port 8000)
└── rec-engine/      # Python FastAPI service (port 8001) ← YOU ARE HERE
```

### Why Separate?

- **Independent scaling**: ML workloads can scale separately from API traffic
- **Process isolation**: Python ML crashes don't affect Node.js API
- **Clean separation**: Each service has single responsibility
- **Optimized deployments**: Change ML without redeploying Node

## Local Development

### Prerequisites

```bash
# From repo root
source venv/bin/activate
pip3 install -r requirements.txt
```

### Start the service

```bash
# Option 1: Use start script
./apps/rec-engine/start_api.sh

# Option 2: Manual
cd apps/rec-engine
python3 api.py
```

Runs on `http://localhost:8001`

### Test endpoints

```bash
# Health check
curl http://localhost:8001/health

# Get recommendations
curl -X POST http://localhost:8001/api/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "currentWeight": 200,
    "weightUnit": "lbs",
    "goalWeight": 180,
    "age": 35,
    "sex": "female",
    "country": "USA",
    "hasInsurance": true
  }'
```

## API Endpoints

### `POST /api/recommendations`

Generate personalized drug recommendations.

**Request:**
```typescript
{
  currentWeight: number        // Required
  weightUnit: "lbs" | "kg"     // Required
  goalWeight: number           // Required
  age?: number                 // Optional (default: 35)
  sex?: "male" | "female" | "other"  // Optional
  state?: string               // Optional (e.g. "CA")
  country: string              // Default: "USA"
  comorbidities?: string[]     // Optional
  hasInsurance: boolean        // Default: false
  insuranceProvider?: string   // Optional
  maxBudget?: number          // Optional (monthly cost limit)
  sideEffectConcerns?: string[] // Optional
}
```

**Response:**
```typescript
{
  recommendations: Array<{
    drug: string
    matchScore: number          // 0-100
    expectedWeightLoss: {
      min: number
      max: number
      avg: number
      unit: string
    }
    successRate: number         // 0-100
    estimatedCost: number | null
    sideEffectProbability: Array<{
      effect: string
      probability: number       // 0-100
      severity: "mild" | "moderate" | "severe"
    }>
    similarUserCount: number
    pros: string[]
    cons: string[]
  }>
  totalExperiences: number
}
```

### `GET /health`

Returns `{"status": "healthy", "service": "ml"}`

### `GET /api/cache/clear`

Clears in-memory experiences cache (admin endpoint).

## Files

```
apps/rec-engine/
├── api.py                  # FastAPI app + endpoints
├── recommender.py          # KNN-based recommendation engine
├── recommender_api.py      # Legacy CLI wrapper (deprecated)
├── test_recommender.py     # Unit tests
├── start_api.sh           # Local dev start script
├── Procfile               # Railway deployment config
├── railway.json           # Railway service config
└── README.md              # This file
```

## Environment Variables

Required:
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_ANON_KEY` or `SUPABASE_SERVICE_KEY` - Supabase credentials

Optional:
- `REC_ENGINE_PORT` - Port to run on (default: 8001)

## Railway Deployment

### Step 1: Create ML API Service

1. Go to Railway dashboard → New → Empty Service
2. Name: `whichglp-rec-engine`
3. Connect to GitHub repo
4. Settings:
   - **Root Directory**: `/` (monorepo root)
   - **Start Command**: `cd apps/rec-engine && python3 api.py`
   - **Health Check Path**: `/health`

5. Environment Variables:
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_SERVICE_KEY=your-service-key
   REC_ENGINE_PORT=8001
   ```

6. Generate domain → Copy URL (e.g., `https://whichglp-rec-engine.railway.app`)

### Step 2: Update Backend Service

In your `whichglp-api` Railway service, add:

```
REC_ENGINE_URL=https://whichglp-rec-engine.railway.app
```

### Step 3: Deploy

Push to GitHub → Both services auto-deploy

## Architecture Details

### KNN Recommender

The service uses K-Nearest Neighbors to match users with similar profiles:

1. **Feature extraction**: Age, sex, starting weight, insurance status
2. **Similarity search**: Find K=15 most similar users
3. **Aggregation**: Calculate avg weight loss, success rate, side effects per drug
4. **Ranking**: Score drugs based on match quality

### Caching Strategy

- **In-memory cache**: Stores experiences DataFrame
- **Cache invalidation**: Manual via `/api/cache/clear`
- **TODO**: Add Redis + TTL for production

### Performance

- **Cold start**: ~2-3s (loads 1000 experiences from DB)
- **Warm requests**: ~500-800ms (cached data)
- **Concurrent requests**: FastAPI async handles multiple simultaneous requests

## Testing

```bash
# Run unit tests
cd apps/rec-engine
pytest test_recommender.py -v

# Test live API
curl -X POST http://localhost:8001/api/recommendations \
  -H "Content-Type: application/json" \
  -d @test_payload.json
```

## Monitoring

Check logs in Railway:
```bash
railway logs --service whichglp-rec-engine
```

Health check should return 200:
```bash
curl https://your-ml.railway.app/health
```

## Future Improvements

- [ ] Add Redis caching
- [ ] Implement request logging (structlog)
- [ ] Add rate limiting (slowapi)
- [ ] Add API authentication
- [ ] Add Prometheus metrics
- [ ] Add request tracing (OpenTelemetry)
- [ ] Optimize KNN with FAISS
- [ ] Add batch prediction endpoint
- [ ] Add model versioning
- [ ] A/B testing framework
