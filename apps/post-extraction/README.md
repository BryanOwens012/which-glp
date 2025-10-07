# Post Extraction Service

Extracts structured features from Reddit posts using GLM-4.5-Air (replaces Claude Sonnet 4).

## Overview

Uses GLM-4.5-Air API ($0.20/$1.10 per 1M tokens) instead of Claude ($3/$15 per 1M tokens) - **15x cheaper**.

## Cost Savings

- Claude cost per post: ~$0.01
- GLM cost per post: ~$0.0007
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
Model: `glm-4.5-air`
Env: `GLM_API_KEY`, `SUPABASE_URL`, `SUPABASE_DB_PASSWORD`
