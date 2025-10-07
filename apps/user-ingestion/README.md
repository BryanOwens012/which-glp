# User Ingestion Service

Analyzes Reddit user post/comment history to extract demographic information using GLM-4.5-Air.

## Overview

This service:
1. Queries unique usernames from `reddit_posts` table
2. Fetches last 20 posts + 20 comments per user via PRAW
3. Sends to GLM-4.5-Air for demographic extraction
4. Inserts results to `reddit_users` table

## Architecture

```
user-ingestion/
├── glm_client.py       # Z.AI SDK wrapper (GLM-4.5-Air)
├── user_analyzer.py    # Main analyzer (PRAW + GLM)
├── prompts.py          # Demographic extraction prompts
├── schema.py           # Pydantic models (UserDemographics)
├── api.py              # FastAPI service
├── start.sh            # Railway startup script
└── shared/             # Symlink to ../data-ingestion/shared
```

## Database Schema

**Table: `reddit_users`**
- `username` (PK) - Reddit username
- `height_inches` - Height in inches
- `starting_weight_lbs` - Starting weight before GLP-1
- `current_weight_lbs` - Current/most recent weight
- `state` - US state
- `country` - Country (default USA)
- `age` - Age in years
- `sex` - Gender (male/female/other/unknown)
- `comorbidities` - Medical conditions array
- `analyzed_at` - Timestamp
- `post_count` - Number of posts analyzed
- `comment_count` - Number of comments analyzed
- `confidence_score` - AI confidence (0.0-1.0)
- `model_used` - AI model name
- `processing_cost_usd` - Extraction cost
- `raw_response` - Full API response (JSONB)

## Usage

### CLI Mode

```bash
cd apps/user-ingestion
source ../../venv/bin/activate

# Analyze 10 users
python3 user_analyzer.py --limit 10

# Analyze all unanalyzed users
python3 user_analyzer.py

# Custom rate limit (default 2.0s between users)
python3 user_analyzer.py --limit 50 --rate-limit 3.0
```

### API Mode

```bash
# Start FastAPI service
./start.sh

# Or manually
python3 api.py
```

**Endpoints:**
- `GET /health` - Health check
- `GET /api/stats` - Get total/unanalyzed user counts
- `POST /api/analyze` - Trigger analysis (background task)
- `GET /api/status` - Check if analysis is running

**Example:**
```bash
# Get stats
curl http://localhost:8002/api/stats

# Trigger analysis of 10 users
curl -X POST http://localhost:8002/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"limit": 10, "rate_limit_delay": 2.0}'

# Check status
curl http://localhost:8002/api/status
```

## Environment Variables

Required in `.env`:
```bash
# Z.AI API
GLM_API_KEY=your-glm-api-key

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_DB_PASSWORD=your-password

# Reddit API
REDDIT_API_APP_NAME=whichglp-ingestion/0.1
REDDIT_API_APP_ID=your-app-id
REDDIT_API_APP_SECRET=your-app-secret
```

## Cost Analysis

**GLM-4.5-Air Pricing:**
- Input: $0.20 per 1M tokens
- Output: $1.10 per 1M tokens

**Typical User Analysis:**
- 20 posts + 20 comments ≈ 3,000 input tokens
- Structured output ≈ 100 output tokens
- **Cost per user: ~$0.0007** (0.07 cents)

**Comparison to Claude Sonnet 4:**
- Claude cost per user: ~$0.0105
- **Savings: ~15x cheaper**

**Estimated Monthly Costs:**
- 1,000 users: ~$0.70
- 10,000 users: ~$7.00

## Railway Deployment

### Setup

1. Create new Railway service: `whichglp-user-ingestion`
2. Link to GitHub repo
3. Set root directory: `apps/user-ingestion`
4. Set start command: `./start.sh`

### Environment Variables

Add to Railway service:
- `GLM_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_DB_PASSWORD`
- `REDDIT_API_APP_NAME`
- `REDDIT_API_APP_ID`
- `REDDIT_API_APP_SECRET`
- `PORT` (automatically set by Railway)

### Health Check

Configure Railway health check:
- Path: `/health`
- Expected response: `200 OK`

## Monitoring

**Logs:**
- Service logs available via Railway dashboard
- Check for errors in GLM API calls
- Monitor cost accumulation

**Database:**
```sql
-- Check analysis progress
SELECT COUNT(*) FROM reddit_users;

-- Get recent analyses
SELECT username, confidence_score, processing_cost_usd, analyzed_at
FROM reddit_users
ORDER BY analyzed_at DESC
LIMIT 10;

-- Total cost
SELECT SUM(processing_cost_usd) as total_cost FROM reddit_users;
```

## Troubleshooting

**"No unanalyzed users found":**
- Check that `reddit_posts` table has data
- Verify usernames aren't all `[deleted]`

**GLM API errors:**
- Check `GLM_API_KEY` is set correctly
- Verify Z.AI account has credits
- Check network connectivity

**PRAW errors:**
- Verify Reddit API credentials
- Check rate limits (60 req/min with OAuth)
- Ensure user accounts exist and aren't suspended

**Import errors:**
- Ensure `shared/` symlink exists: `ln -s ../data-ingestion/shared shared`
- Verify virtual environment is activated
- Check all dependencies installed: `pip install -r ../../requirements.txt`
