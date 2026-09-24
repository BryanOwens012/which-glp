# Post Extraction Service

Extracts structured features from Reddit posts using Muse Spark 1.3 Contributor, via OpenRouter.

## Overview

Uses Muse Spark through the shared extractor (the `openai` Python SDK pointed at OpenRouter). Per-token prices live in `MODEL_PRICING` in `scripts/legacy-ingestion/shared/openai_extractor.py`; Muse Spark lists no separate cache-write rate, so a cache-writing call bills as plain input. Billed cost is read from OpenRouter's `usage.cost` on each response; `MODEL_PRICING` is only the fallback estimate when OpenRouter doesn't return one.

## How it works

- `vocab.py`: controlled vocabularies (drugs, side effects, post types, treatment status, subreddit hints)
- `schema.py`: `PostExtraction`, sent as a strict JSON schema so those vocabularies are enforced while decoding
- `prompts.py`: the system prompt (field definitions and two examples) and the per-post user message, which carries the subreddit and posted date
- `rows.py`: quote grounding and the mapping from an extraction to an `extracted_features` row
- `pipeline.py`: `extract_post_row`, one post through prompt, model, grounding, and row mapping; `api.py` and the eval both call it
- `api.py`: the batch endpoint that filters, extracts, grounds, and upserts

Measure any change to these with `scripts/extraction-eval/` before shipping.

## Cost

- Reasoning effort `low`. A post sends ~6,500 input tokens, nearly all of them the static system prompt, and gets ~1,600 output tokens back (reasoning included, billed as output)
- ~$0.00035 per post on a cache hit, ~$0.001 on a miss, so the cache hit rate drives cost
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
