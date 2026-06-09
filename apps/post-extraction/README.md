# Post Extraction Service

Extracts structured features from Reddit posts using GPT-5-nano (replaces Claude Sonnet 4).

## Overview

Uses GPT-5-nano API ($0.05/$0.40 per 1M tokens) instead of Claude ($3/$15 per 1M tokens) - **~60x cheaper**.

## Cost Savings

- Claude cost per post: ~$0.01
- GPT-5-nano cost per post: ~$0.0002
- **Savings: ~93%** ($100 → $7 per 1,000 posts)

## Usage

### API
```bash
./start.sh  # Port 8004

curl http://localhost:8004/health
curl -X POST http://localhost:8004/api/extract -d '{"subreddit":"Ozempic","limit":100}'
```

## Railway Deployment

Service: `whichglp-post-extraction`
Model: `gpt-5-nano`
Env: `OPENAI_API_KEY`, `SUPABASE_URL`, `SUPABASE_DB_PASSWORD`
