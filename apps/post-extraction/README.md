# Post Extraction Service

Extracts structured features from Reddit posts using Muse Spark 1.3 Contributor, via OpenRouter.

## Overview

Uses Muse Spark through the shared extractor (the `openai` Python SDK pointed at OpenRouter). Per-token prices live in `MODEL_PRICING` in `scripts/legacy-ingestion/shared/openai_extractor.py`; Muse Spark lists no separate cache-write rate, so a cache-writing call bills as plain input. Billed cost is read from OpenRouter's `usage.cost` on each response; `MODEL_PRICING` is only the fallback estimate when OpenRouter doesn't return one.

## Cost

- A post sends ~9,500 input tokens, nearly all of them the static system prompt, and gets ~800 output tokens back (reasoning included, billed as output)
- About $0.0003 per post on average: ~$0.00018 on a cache hit (mostly output), ~$0.001 on a miss, so the cache hit rate drives cost
- `scripts/tests/test_openai_minimal.py` is a live smoke test that sends the real system prompt twice and prints cached/written tokens and billed cost

## Usage

### API
```bash
./start.sh  # Port 8004

curl http://localhost:8004/health
curl -X POST http://localhost:8004/api/extract -d '{"subreddit":"Ozempic","limit":100}'
```

## Railway Deployment

Service: `Post-Extraction`, declared in `.railway/railway.ts` (Railpack from the monorepo root, start `cd apps/post-extraction && uvicorn api:app --host 0.0.0.0 --port $PORT`, healthcheck `/health`); triggered daily at 06:00 UTC by `Post-Extraction-Cron`
Model: `meta/muse-spark-1.3-contributor` (via OpenRouter)
Env: variable names are declared in `.railway/railway.ts`; values live on Railway
