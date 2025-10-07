# Database Migrations

This directory contains database migration scripts and tools for the WhichGLP data ingestion system.

## Files

### Migration Scripts
- `001_create_reddit_tables.up.sql` - Creates reddit_posts and reddit_comments tables
- `001_create_reddit_tables.down.sql` - Drops reddit_posts and reddit_comments tables

### Python Tools
- `run_migration.py` - Executes SQL migration files
- `verify_schema.py` - Verifies database schema after migration

### Tests
- `test_migrations.py` - Unit tests (16 tests)
- `test_integration.py` - Integration tests requiring DB connection (6 tests)
- `pytest.ini` - Pytest configuration

## Running Migrations

### Prerequisites
1. Create `.env` file in project root with:
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_DB_PASSWORD=your-password
   ```

2. Install dependencies:
   ```bash
   pip install psycopg2-binary python-dotenv
   ```

### Up Migration (Create Tables)
```bash
cd apps/shared/migrations
python run_migration.py 001_create_reddit_tables.up.sql
```

### Down Migration (Drop Tables)
```bash
python run_migration.py 001_create_reddit_tables.down.sql
```

### Verify Schema
```bash
python verify_schema.py
```

## Running Tests

### Unit Tests Only (No DB Required)
```bash
pytest test_migrations.py -v
```

### Integration Tests (DB Required)
```bash
pytest test_integration.py -v -m integration
```

### All Tests
```bash
pytest -v
```

### Skip Integration Tests
```bash
pytest -m "not integration" -v
```

## Error Handling

The migration scripts include comprehensive error handling for:
- Missing `.env` file
- Missing or empty environment variables
- Invalid SUPABASE_URL format
- Database connection failures
- Empty or non-existent migration files
- SQL syntax errors (with automatic rollback)

## Database Schema

### reddit_posts
- 18 columns including: post_id, title, body, score, upvote_ratio, num_comments
- 4 indexes for efficient queries
- Stores Reddit posts with metadata

### reddit_comments
- 17 columns including: comment_id, post_id, parent_comment_id, depth
- 6 indexes for parent chain traversal
- Foreign key to reddit_posts for referential integrity

## Migration Naming Convention

- Up migrations: `{number}_{description}.up.sql`
- Down migrations: `{number}_{description}.down.sql`

Example:
- `001_create_reddit_tables.up.sql`
- `001_create_reddit_tables.down.sql`
