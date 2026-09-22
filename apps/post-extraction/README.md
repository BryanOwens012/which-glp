# Post Extraction Service

Extracts structured features from Reddit posts using GPT-6 Luna.

## Overview

Uses the GPT-6 Luna API through the shared extractor. Per-token prices live in `MODEL_PRICING` in `scripts/legacy-ingestion/shared/openai_extractor.py`; they are ~30x below Claude Sonnet 4's on both input and output.

## Cost

Measured on live calls:
- A post sends ~9,500 input tokens, nearly all of them the cached static system prompt, and gets ~350–550 output tokens back
- ~$0.00035 per post while the prompt cache is warm; ~$0.0015 for the call that writes it

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
