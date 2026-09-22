# Post Extraction Service

Extracts structured features from Reddit posts using GPT-6 Luna (replaces Claude Sonnet 4).

## Overview

Uses GPT-6 Luna API ($0.10/$0.50 per 1M input/output tokens; $0.01 cached input, $0.125 cache write) instead of Claude ($3/$15 per 1M tokens) - **~30x cheaper**.

## Cost Savings

- Claude cost per post: ~$0.01
- GPT-6 Luna cost per post: ~$0.00035
- **Savings: ~97%** ($10 → $0.35 per 1,000 posts)

## Usage

### API
```bash
./start.sh  # Port 8004

curl http://localhost:8004/health
curl -X POST http://localhost:8004/api/extract -d '{"subreddit":"Ozempic","limit":100}'
```

## Railway Deployment

Service: `Post-Extraction`, declared in `.railway/railway.ts` (Railpack from the monorepo root, start `cd apps/post-extraction && uvicorn api:app --host 0.0.0.0 --port $PORT`, healthcheck `/health`); triggered daily at 06:00 UTC by `Post-Extraction-Cron`
Model: `gpt-6-luna`
Env: variable names are declared in `.railway/railway.ts`; values live on Railway
