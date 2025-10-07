# Railway Cron Job Setup Guide

This guide explains how to set up automated cron jobs on Railway to run the post-ingestion, post-extraction, and user-extraction services every 2 days.

## Overview

We have 3 services that need to run on a schedule:
1. **Post Ingestion** - Fetches new posts from Reddit (Tier 1 subreddits)
2. **Post Extraction** - Extracts features from posts using GLM-4.5-Air
3. **User Extraction** - Analyzes user demographics using GLM-4.5-Air

Each service has a retry wrapper script with:
- Exponential backoff
- Up to 5 retry attempts
- Timeout handling
- Status checking to avoid duplicate runs

## Schedule Strategy

Run services every 2 days, staggered to avoid conflicts:

- **Day 1, 2 AM**: Post Ingestion (fetch new posts)
- **Day 1, 4 AM**: Post Extraction (extract features from posts)
- **Day 1, 6 AM**: User Extraction (analyze user demographics)
- **Day 3, 2 AM**: Post Ingestion (repeat)
- etc.

## Railway Cron Setup

### Option 1: Using Railway's Built-in Cron (Recommended)

Railway supports cron jobs via the `cronSchedule` field in `railway.json`.

#### Step 1: Create Cron Service for Post Ingestion

Create a new Railway service with this configuration:

**File: `apps/post-ingestion/railway.cron.json`**
```json
{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "echo 'No build needed for cron job'"
  },
  "deploy": {
    "cronSchedule": "0 2 */2 * *",
    "restartPolicyType": "NEVER",
    "startCommand": "bash scripts/cron-post-ingestion.sh"
  }
}
```

**Environment Variables:**
- `POST_INGESTION_URL` - URL of your post-ingestion service (e.g., `https://post-ingestion-production.up.railway.app`)

#### Step 2: Create Cron Service for Post Extraction

**File: `apps/post-extraction/railway.cron.json`**
```json
{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "echo 'No build needed for cron job'"
  },
  "deploy": {
    "cronSchedule": "0 4 */2 * *",
    "restartPolicyType": "NEVER",
    "startCommand": "bash scripts/cron-post-extraction.sh"
  }
}
```

**Environment Variables:**
- `POST_EXTRACTION_URL` - URL of your post-extraction service (e.g., `https://post-extraction-production.up.railway.app`)

#### Step 3: Create Cron Service for User Extraction

**File: `apps/user-extraction/railway.cron.json`**
```json
{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "echo 'No build needed for cron job'"
  },
  "deploy": {
    "cronSchedule": "0 6 */2 * *",
    "restartPolicyType": "NEVER",
    "startCommand": "bash scripts/cron-user-extraction.sh"
  }
}
```

**Environment Variables:**
- `USER_EXTRACTION_URL` - URL of your user-extraction service (e.g., `https://user-extraction-production.up.railway.app`)

### Option 2: Using Railway CLI

Alternatively, you can set up cron jobs using the Railway CLI:

```bash
# Deploy post-ingestion cron
railway up --service post-ingestion-cron \
  --cron "0 2 */2 * *" \
  --start-command "bash scripts/cron-post-ingestion.sh"

# Deploy post-extraction cron
railway up --service post-extraction-cron \
  --cron "0 4 */2 * *" \
  --start-command "bash scripts/cron-post-extraction.sh"

# Deploy user-extraction cron
railway up --service user-extraction-cron \
  --cron "0 6 */2 * *" \
  --start-command "bash scripts/cron-user-extraction.sh"
```

### Option 3: External Cron Service (e.g., Cron-job.org, EasyCron)

If Railway doesn't support cron schedules, use an external cron service to trigger the scripts:

1. Deploy the scripts as separate services on Railway
2. Get the service URLs
3. Set up cron jobs on an external service to hit those URLs

Example using `cron-job.org`:
- URL: `https://your-railway-app.up.railway.app/run-cron-post-ingestion`
- Schedule: `0 2 */2 * *` (Every 2 days at 2 AM)

## Cron Schedule Reference

| Schedule | Description | Example |
|----------|-------------|---------|
| `0 2 */2 * *` | Every 2 days at 2 AM | Day 1 2 AM, Day 3 2 AM, Day 5 2 AM... |
| `0 4 */2 * *` | Every 2 days at 4 AM | Day 1 4 AM, Day 3 4 AM, Day 5 4 AM... |
| `0 6 */2 * *` | Every 2 days at 6 AM | Day 1 6 AM, Day 3 6 AM, Day 5 6 AM... |
| `0 2 * * *` | Daily at 2 AM | Every day at 2 AM |
| `0 2 * * 0,3` | Sunday and Wednesday at 2 AM | Twice per week |

## Retry Logic Details

Each cron script includes:

### 1. Service Health Check
- Verifies service is accessible before triggering
- Max 5 retries with exponential backoff

### 2. Duplicate Prevention
- Checks if service is already running
- Waits for completion or times out gracefully

### 3. Exponential Backoff
- Initial delay: 60 seconds
- Doubles on each retry
- Max timeout: 30-60 minutes (depending on service)

### 4. Error Handling
- Logs all errors with timestamps
- Returns appropriate exit codes
- Railway logs available for debugging

## Monitoring

### Check Cron Logs on Railway

```bash
# View logs for specific cron service
railway logs --service post-ingestion-cron

# Tail logs in real-time
railway logs --service post-ingestion-cron --follow
```

### Check Service Status

```bash
# Post Ingestion
curl https://post-ingestion-production.up.railway.app/api/status

# Post Extraction
curl https://post-extraction-production.up.railway.app/api/status

# User Extraction
curl https://user-extraction-production.up.railway.app/api/status
```

### Check Service Health

```bash
# Post Ingestion
curl https://post-ingestion-production.up.railway.app/health

# Post Extraction
curl https://post-extraction-production.up.railway.app/health

# User Extraction
curl https://user-extraction-production.up.railway.app/health
```

## Manual Trigger

To manually trigger any cron job (for testing):

```bash
# Post Ingestion
POST_INGESTION_URL=https://post-ingestion-production.up.railway.app \
  bash scripts/cron-post-ingestion.sh

# Post Extraction
POST_EXTRACTION_URL=https://post-extraction-production.up.railway.app \
  bash scripts/cron-post-extraction.sh

# User Extraction
USER_EXTRACTION_URL=https://user-extraction-production.up.railway.app \
  bash scripts/cron-user-extraction.sh
```

## Troubleshooting

### Cron Job Not Running

1. Check Railway service logs: `railway logs --service <service-name>`
2. Verify environment variables are set correctly
3. Test script manually with curl commands above
4. Check cron schedule syntax is correct

### Service Already Running Error (409 Conflict)

This is expected behavior. The cron script will:
1. Wait for the current run to complete (with timeout)
2. Skip the run if it takes too long
3. Try again on the next scheduled run

### Timeout Errors

If you see timeout errors frequently:
1. Increase `MAX_TIMEOUT` in the cron script
2. Reduce the batch size (e.g., `posts_limit`, `USER_LIMIT`)
3. Check service logs for performance issues

### Service Health Check Failures

If health checks fail:
1. Verify the service URL is correct
2. Check if the service is deployed and running
3. Test the `/health` endpoint manually
4. Review Railway service logs for errors

## Cost Optimization

To reduce costs:

1. **Adjust Frequency**: Change from every 2 days to weekly
   ```json
   "cronSchedule": "0 2 * * 0"  // Sunday at 2 AM
   ```

2. **Reduce Batch Sizes**:
   - Post Ingestion: Reduce `posts_limit` from 100 to 50
   - Post Extraction: Reduce `EXTRACTION_LIMIT` from 500 to 250
   - User Extraction: Reduce `USER_LIMIT` from 50 to 25

3. **Stagger More**: Spread jobs across different days to reduce peak load

## Environment Variables Summary

Set these in Railway for each cron service:

### Post Ingestion Cron
- `POST_INGESTION_URL` - URL of post-ingestion service

### Post Extraction Cron
- `POST_EXTRACTION_URL` - URL of post-extraction service

### User Extraction Cron
- `USER_EXTRACTION_URL` - URL of user-extraction service

## Next Steps

1. Deploy each cron service to Railway
2. Set environment variables
3. Verify first run in Railway logs
4. Monitor for 1 week to ensure stability
5. Adjust schedules/limits based on performance

## Alternative: GitHub Actions (if Railway cron is unavailable)

If Railway doesn't support cron schedules, use GitHub Actions:

**File: `.github/workflows/cron-jobs.yml`**
```yaml
name: Scheduled Data Pipeline

on:
  schedule:
    - cron: '0 2 */2 * *'  # Post Ingestion
    - cron: '0 4 */2 * *'  # Post Extraction
    - cron: '0 6 */2 * *'  # User Extraction

jobs:
  post-ingestion:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Trigger Post Ingestion
        run: |
          bash scripts/cron-post-ingestion.sh
        env:
          POST_INGESTION_URL: ${{ secrets.POST_INGESTION_URL }}

  post-extraction:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Trigger Post Extraction
        run: |
          bash scripts/cron-post-extraction.sh
        env:
          POST_EXTRACTION_URL: ${{ secrets.POST_EXTRACTION_URL }}

  user-extraction:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Trigger User Extraction
        run: |
          bash scripts/cron-user-extraction.sh
        env:
          USER_EXTRACTION_URL: ${{ secrets.USER_EXTRACTION_URL }}
```
