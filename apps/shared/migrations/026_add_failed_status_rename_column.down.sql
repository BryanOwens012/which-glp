-- Rollback: Remove 'failed' status and restore extraction_skip_reason column name
-- This reverts 026_add_failed_status_rename_column.up.sql

-- Note: PostgreSQL does not support removing values from enum types
-- We can only mark it as deprecated in comments
-- Posts with status='failed' will need to be manually updated before rollback

-- Rename column back
ALTER TABLE reddit_posts
    RENAME COLUMN extraction_log_message TO extraction_skip_reason;

-- Restore original index
DROP INDEX IF EXISTS idx_posts_extraction_log;
CREATE INDEX idx_posts_skipped_reason ON reddit_posts(extraction_skip_reason)
    WHERE extraction_status = 'skipped';

-- Restore original comments
COMMENT ON COLUMN reddit_posts.extraction_skip_reason IS
    'Reason for skipping (e.g., "keyword_filter: not drug-related", "minimum_field_filter: missing weight")';

COMMENT ON COLUMN reddit_posts.extraction_status IS
    'Status of extraction: pending (not yet attempted), processed (successfully extracted), skipped (filtered out)';

-- Warn about enum value (cannot be removed)
DO $$
BEGIN
    RAISE NOTICE 'WARNING: extraction_status_type still contains ''failed'' value (enum values cannot be removed in PostgreSQL)';
    RAISE NOTICE 'Any posts with status=''failed'' must be updated to another status before using the old schema';
END $$;
