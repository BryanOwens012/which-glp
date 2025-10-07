# Post Ingestion Service

Fetches the 100 most recent posts from tier 1-3 subreddits (no comments, no AI processing).

## Overview

This service:
1. Fetches 100 most recent posts from specified subreddits using `subreddit.new()`
2. Parses posts into database schema
3. Inserts to `reddit_posts` table with deduplication
4. Creates backup files

**No comments fetched, no AI processing** - just raw post ingestion.

## Usage

### CLI
```bash
# Single subreddit
python3 -m apps.post-ingestion.recent_ingest --subreddit Ozempic

# All tier 1 subreddits
python3 -m apps.post-ingestion.recent_ingest --all-tier1

# Custom post limit
python3 -m apps.post-ingestion.recent_ingest --subreddit Mounjaro --posts 200
```

### API
```bash
./start.sh  # Starts on port 8003

# Endpoints
curl http://localhost:8003/health
curl -X POST http://localhost:8003/api/ingest -d '{"subreddit":"Ozempic","posts_limit":100}'
curl http://localhost:8003/api/status
```

## Railway Deployment

Service name: `whichglp-post-ingestion`
Start command: `./start.sh`
Port: Auto (Railway sets `PORT`)
