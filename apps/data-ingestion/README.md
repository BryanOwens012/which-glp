# Reddit Data Ingestion

Local Reddit data ingestion pipeline for GLP-1 medication subreddits. Fetches posts and comments from Reddit API and stores them in Supabase PostgreSQL database with comprehensive error handling and batch operations.

## Overview

This ingestion system:
- Fetches posts from 6 Tier 1 GLP-1 subreddits (Ozempic, Mounjaro, Wegovy, zepbound, semaglutide, tirzepatidecompound)
- Retrieves all comments for each post
- Parses data with 50+ edge case tests covering deleted authors, missing fields, NSFW content, etc.
- Batch inserts to Supabase (100 records per batch for optimal performance)
- Automatic deduplication using `ON CONFLICT DO NOTHING`
- Runs on schedule (every 15 minutes) or once
- Comprehensive logging to console and rotating log files

## Architecture

The codebase is organized into three separate concerns:

```
ingestion/            # Reddit data ingestion
├── scheduler.py      # Main orchestrator with APScheduler
├── historical_ingest.py  # Historical data fetching
├── upload_from_backup.py # Upload from JSON backups
├── client.py         # PRAW wrapper for Reddit API
└── parser.py         # Safe data extraction with null handling

extraction/           # AI-powered feature extraction
├── ai_extraction.py  # Main extraction pipeline
├── ai_client.py      # Claude AI client wrapper
├── prompts.py        # Prompt templates for extraction
├── context.py        # Context builder for nested comments
└── schema.py         # Pydantic models for extracted data

shared/               # Shared utilities
├── database.py       # Database operations with psycopg2
└── config.py         # Logging configuration

migrations/           # Database schema migrations
├── 001_create_reddit_tables.up.sql
├── 002_create_extracted_features.up.sql
└── run_migration.py  # Migration runner
```

## Prerequisites

1. **Python 3.8+**
2. **Reddit API Credentials** (see Setup section)
3. **Supabase Account** with PostgreSQL database
4. **Database Migration** must be run first (see Database Setup)

## Setup

### 1. Environment Variables

Create a `.env` file in the repository root with:

```env
# Reddit API Credentials
# Get these from: https://www.reddit.com/prefs/apps
REDDIT_API_APP_NAME=your_app_name
REDDIT_API_APP_ID=your_client_id
REDDIT_API_APP_SECRET=your_client_secret

# Supabase Credentials
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_DB_PASSWORD=your_database_password
```

### 2. Install Dependencies

```bash
# From repository root
pip install -r requirements.txt
```

Key dependencies for ingestion:
- `praw` - Python Reddit API Wrapper
- `psycopg2-binary` - PostgreSQL adapter
- `python-dotenv` - Environment variable management
- `APScheduler` - Job scheduling
- `pytest` - Testing framework

### 3. Database Setup

Run the database migration to create required tables:

```bash
cd apps/data-ingestion/migrations
python run_migration.py 001_create_reddit_tables.up.sql
```

This creates two tables:
- `reddit_posts` - Reddit posts/submissions
- `reddit_comments` - Comments with parent relationships

Verify schema:
```bash
python verify_schema.py
```

## Usage

### Run Ingestion Once

Fetch data from all Tier 1 subreddits once:

```bash
cd apps/data-ingestion
python -m ingestion.scheduler
```

### Run Ingestion on Schedule

Run every 15 minutes automatically:

```bash
python -m ingestion.scheduler --schedule
```

Custom interval (e.g., every 30 minutes):

```bash
python -m ingestion.scheduler --schedule --interval 30
```

### Run Historical Ingestion

Fetch top 100 posts from the past year:

```bash
python -m ingestion.historical_ingest --subreddit Ozempic --posts 100 --comments 20
```

### Run AI Extraction

Extract features from ingested posts/comments:

```bash
python -m extraction.ai_extraction --subreddit Ozempic
```

Stop with `Ctrl+C`.

## Testing

Run comprehensive test suite (50+ tests):

```bash
cd apps/data-ingestion
pytest tests/test_parser.py -v
```

Tests cover:
- Safe attribute extraction (deleted authors, missing fields)
- Post and comment parsing with all edge cases
- Comment depth calculation for nested replies
- Data validation
- JSON serialization
- NSFW content handling
- Empty strings vs None values
- Special characters and long text

## Logging

Logs are written to:
- **Console**: INFO level with timestamps
- **File**: `ingestion.log` with DEBUG level and full details

Log rotation:
- Max file size: 10MB
- Backup files: 5
- Automatic rotation when size exceeded

## Database Schema

### reddit_posts

| Column | Type | Description |
|--------|------|-------------|
| id | BIGSERIAL | Primary key |
| post_id | TEXT | Reddit post ID (unique) |
| created_at | TIMESTAMPTZ | Post creation time |
| subreddit | TEXT | Subreddit name |
| subreddit_id | TEXT | Subreddit ID |
| author | TEXT | Username or [deleted] |
| author_flair_text | TEXT | User flair (nullable) |
| title | TEXT | Post title |
| body | TEXT | Post body (nullable for link posts) |
| body_html | TEXT | HTML body (nullable) |
| is_nsfw | BOOLEAN | NSFW flag |
| score | INTEGER | Net upvotes |
| upvote_ratio | FLOAT | Ratio 0-1 (nullable for new posts) |
| num_comments | INTEGER | Comment count |
| permalink | TEXT | Reddit URL path |
| url | TEXT | External URL |
| raw_json | JSONB | Full API response |
| ingested_at | TIMESTAMPTZ | Ingestion timestamp |

### reddit_comments

| Column | Type | Description |
|--------|------|-------------|
| id | BIGSERIAL | Primary key |
| comment_id | TEXT | Reddit comment ID (unique) |
| created_at | TIMESTAMPTZ | Comment creation time |
| post_id | TEXT | Parent post ID (foreign key) |
| parent_comment_id | TEXT | Parent comment ID if nested |
| depth | INTEGER | Nesting depth (1 = top-level) |
| subreddit | TEXT | Subreddit name |
| subreddit_id | TEXT | Subreddit ID |
| author | TEXT | Username or [deleted] |
| author_flair_text | TEXT | User flair (nullable) |
| body | TEXT | Comment text |
| body_html | TEXT | HTML body (nullable) |
| is_nsfw | BOOLEAN | NSFW flag |
| score | INTEGER | Net upvotes |
| permalink | TEXT | Reddit URL path |
| raw_json | JSONB | Full API response |
| ingested_at | TIMESTAMPTZ | Ingestion timestamp |

## Performance

- **Batch Size**: 100 records per insert (configurable in `database.py`)
- **Deduplication**: Automatic via `ON CONFLICT DO NOTHING`
- **Rate Limits**: Reddit API allows 60 requests/minute with OAuth
- **Typical Run**: ~5-10 minutes for all 6 subreddits (100 posts each)

## Error Handling

The system handles:
- Deleted/removed authors → `[deleted]` placeholder
- Missing attributes → None with safe defaults
- Empty strings → Converted to None
- NSFW content → Properly flagged
- Connection failures → Logged and retried next run
- Duplicate posts/comments → Silently skipped
- Invalid subreddits → Logged and skipped
- API rate limits → PRAW handles automatically

## Monitoring

Check logs for:
```
INFO  | Starting ingestion run at 2025-09-30 14:30:00
INFO  | Fetching up to 100 recent posts from r/Ozempic
INFO  | Fetched 42 comments for post abc123
INFO  | Inserted 95 posts (out of 100 total, 5 duplicates skipped)
INFO  | Inserted 423 comments (out of 450 total, 27 duplicates skipped)
INFO  | Total posts inserted: 485
INFO  | Total comments inserted: 2103
```

## Troubleshooting

### "Missing environment variable"
Ensure `.env` file exists in repository root with all required variables.

### "Failed to connect to database"
Check `SUPABASE_URL` and `SUPABASE_DB_PASSWORD` are correct. Test connection:
```bash
cd apps/data-ingestion/migrations
python run_migration.py --help
```

### "Subreddit not accessible"
Some subreddits may be private or banned. Check logs for specific error.

### "No posts inserted (all duplicates)"
Normal if ingestion runs frequently. Posts are deduplicated automatically.

## Reddit API Credentials

1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Select "script" application type
4. Name: `which-glp-ingestion`
5. Redirect URI: `http://localhost:8080` (not used but required)
6. Copy the client ID (under app name) and secret
7. Add to `.env` file

## File Structure

```
apps/data-ingestion/
├── README.md                     # This file
├── setup.py                      # Package configuration
├── pytest.ini                    # Pytest configuration
├── ingestion/                    # Reddit data ingestion
│   ├── __init__.py
│   ├── scheduler.py              # Main orchestrator with APScheduler
│   ├── historical_ingest.py      # Historical data fetching
│   ├── upload_from_backup.py     # Upload from JSON backups
│   ├── client.py                 # PRAW wrapper for Reddit API
│   └── parser.py                 # Safe data extraction with null handling
├── extraction/                   # AI-powered feature extraction
│   ├── __init__.py
│   ├── ai_extraction.py          # Main extraction pipeline
│   ├── ai_client.py              # Claude AI client wrapper
│   ├── prompts.py                # Prompt templates for extraction
│   ├── context.py                # Context builder for nested comments
│   └── schema.py                 # Pydantic models for extracted data
├── shared/                       # Shared utilities
│   ├── __init__.py
│   ├── database.py               # Database operations with psycopg2
│   └── config.py                 # Logging configuration
├── migrations/                   # Database migrations
│   ├── 001_create_reddit_tables.up.sql
│   ├── 002_create_extracted_features.up.sql
│   ├── run_migration.py
│   └── verify_schema.py
├── tests/                        # All tests
│   ├── test_parser.py            # 45 parser unit tests
│   ├── test_mocks.py             # Mock PRAW objects
│   ├── test_migrations.py        # Migration unit tests
│   └── test_integration.py       # Integration tests (require DB)
└── scripts/                      # Utility scripts
    └── praw_test.py              # PRAW testing script
```

## Package Organization

The refactored structure separates three main concerns:

### 1. Ingestion (`ingestion/`)
Handles fetching raw data from Reddit API:
- Real-time ingestion with scheduler
- Historical ingestion for backfilling
- Parsing Reddit objects into database format
- Backup and upload utilities

### 2. Extraction (`extraction/`)
AI-powered feature extraction from ingested data:
- Claude AI integration for structured data extraction
- Prompt engineering for accurate feature detection
- Context building for nested comment threads
- Pydantic schemas for type-safe extraction

### 3. Shared (`shared/`)
Common utilities used across packages:
- Database connection and operations
- Logging configuration
- Shared types and utilities

### 4. Migrations (`migrations/`)
Database schema management:
- SQL migration files (up/down)
- Migration runner script
- Schema verification

## Future Enhancements

- Incremental ingestion (only fetch new posts since last run)
- Tier 2 and Tier 3 subreddit support
- Cloud deployment (AWS Lambda, Cloud Run)
- Prometheus metrics
- Real-time ingestion with webhooks
- Comment update detection (edited comments)
