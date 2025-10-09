-- Rollback migration: Remove extraction status tracking from reddit_posts
-- This reverts 023_add_extraction_status_flags.up.sql

-- Drop indexes
DROP INDEX IF EXISTS idx_posts_extraction_status;
DROP INDEX IF EXISTS idx_posts_skipped_reason;

-- Drop columns
ALTER TABLE reddit_posts
    DROP COLUMN IF EXISTS extraction_status,
    DROP COLUMN IF EXISTS extraction_skip_reason,
    DROP COLUMN IF EXISTS extraction_attempted_at;

-- Drop enum type
DROP TYPE IF EXISTS extraction_status_type;
