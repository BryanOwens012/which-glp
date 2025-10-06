# Weekly Ingestion Schedule

## Strategy

Run Reddit ingestion **twice per week** (Wednesday + Sunday) to achieve comprehensive coverage while minimizing recency bias.

### Why Twice Weekly?

- **Better temporal coverage**: Wednesday run captures Mon-Wed, Sunday run captures Thu-Sun
- **~150 new posts/week**: 2 runs × 75 new posts = 150 total (minimal overlap due to timing)
- **95% coverage**: ~200 posts/week out of ~210 total for active subreddits like r/Zepbound
- **Balances dataset**: 90% non-top content (75 new + 15 controversial) complements top-heavy seed data

### Per-Run Defaults

Each run fetches:
- **10 top posts** from past week (exceptional content)
- **75 new posts** (most recent, less vote bias)
- **15 controversial posts** from past week (edge cases)
- **5 comments per post** (top comments only)

Total: ~100 unique posts per run per subreddit (after deduplication)

## Cron Schedule

### Option 1: All Subreddits (Tier 1-3)

```bash
# Wednesday 2 AM - Mid-week run
0 2 * * 3 cd /Users/bryan/Github/which-glp && venv/bin/python3 -m ingestion.weekly_ingest

# Sunday 2 AM - Weekend run
0 2 * * 0 cd /Users/bryan/Github/which-glp && venv/bin/python3 -m ingestion.weekly_ingest
```

### Option 2: Tier 1 Only (Drug-Specific Subreddits)

```bash
# Wednesday 2 AM
0 2 * * 3 cd /Users/bryan/Github/which-glp && venv/bin/python3 -m ingestion.weekly_ingest --tier tier1

# Sunday 2 AM
0 2 * * 0 cd /Users/bryan/Github/which-glp && venv/bin/python3 -m ingestion.weekly_ingest --tier tier1
```

### Option 3: Staggered Schedule (Different Tiers on Different Days)

```bash
# Wednesday 2 AM - Tier 1 (most important)
0 2 * * 3 cd /Users/bryan/Github/which-glp && venv/bin/python3 -m ingestion.weekly_ingest --tier tier1

# Friday 2 AM - Tier 2 (general GLP-1)
0 2 * * 5 cd /Users/bryan/Github/which-glp && venv/bin/python3 -m ingestion.weekly_ingest --tier tier2

# Sunday 2 AM - Tier 3 (broader weight loss)
0 2 * * 0 cd /Users/bryan/Github/which-glp && venv/bin/python3 -m ingestion.weekly_ingest --tier tier3
```

## Manual Run Examples

### All subreddits with defaults
```bash
cd /Users/bryan/Github/which-glp
venv/bin/python3 -m ingestion.weekly_ingest
```

### Single subreddit
```bash
venv/bin/python3 -m ingestion.weekly_ingest --subreddit Ozempic
```

### Custom limits
```bash
venv/bin/python3 -m ingestion.weekly_ingest --top 20 --new 100 --controversial 25
```

### Tier 1 only
```bash
venv/bin/python3 -m ingestion.weekly_ingest --tier tier1
```

## Expected Results

### Per Subreddit Per Week
- **~150-200 unique posts** (2 runs with minimal overlap)
- **~3,000-4,000 comments** (150-200 posts × 20 comments)
- **95% coverage** of weekly activity for active subs

### All Subreddits (25 total)
- **~3,750-5,000 posts/week**
- **~75,000-100,000 comments/week**

## Data Quality Benefits

1. **Reduces recency bias**: Two runs spread across the week vs single run
2. **Captures trending content**: Top posts may shift between Wed → Sun
3. **Balances exceptional vs typical**: 10% top, 75% new, 15% controversial
4. **Complements seed data**: Seed has top 500 all-time, weekly adds "normal" experiences
5. **Automatic deduplication**: Database `ON CONFLICT DO NOTHING` handles overlaps

## Backup Location

All runs create backups at:
```
/Users/bryan/Github/which-glp/backups/ingestion/weekly_run_YYYYMMDD_HHMMSS/
```

Each backup includes:
- `{subreddit}_posts.json` - All fetched posts
- `{subreddit}_comments.json` - All fetched comments
- `summary.json` - Run statistics

## Monitoring

Check run status:
```bash
ls -lht /Users/bryan/Github/which-glp/backups/ingestion/ | head -5
```

View summary of last run:
```bash
cat /Users/bryan/Github/which-glp/backups/ingestion/weekly_run_*/summary.json | jq
```

## Estimated Runtime

- **Per subreddit**: ~5-10 minutes (100 posts × 20 comments)
- **Tier 1 (6 subs)**: ~30-60 minutes
- **Tier 2 (5 subs)**: ~25-50 minutes
- **Tier 3 (14 subs)**: ~70-140 minutes
- **All tiers (25 subs)**: ~2-4 hours

## Rate Limiting

Built-in delays to avoid Reddit API bans:
- **3 seconds** between subreddits
- **0.5 seconds** between fetching comments for each post
- **10 seconds** after any API error

## Future Enhancements

Potential improvements for later:
- True random sampling (fetch 200 new, sample 75)
- Dynamic limits based on subreddit activity
- Parallel processing for faster ingestion
- Email notifications on completion/errors
