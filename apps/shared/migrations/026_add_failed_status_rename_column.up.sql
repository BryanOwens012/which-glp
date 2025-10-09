-- Migration: Add 'failed' status and rename extraction_skip_reason to extraction_log_message
-- Created: 2025-10-08
-- Description: Adds 'failed' to extraction_status enum and renames skip_reason column for broader use

-- Add 'failed' to the enum type (must be in its own transaction)
ALTER TYPE extraction_status_type ADD VALUE 'failed';

-- Rename extraction_skip_reason to extraction_log_message
ALTER TABLE reddit_posts
    RENAME COLUMN extraction_skip_reason TO extraction_log_message;

-- Update the index name for clarity
-- Index on extraction_log_message for non-NULL values (skipped or failed posts)
DROP INDEX IF EXISTS idx_posts_skipped_reason;
CREATE INDEX idx_posts_extraction_log ON reddit_posts(extraction_log_message)
    WHERE extraction_log_message IS NOT NULL;

-- Update column comment
COMMENT ON COLUMN reddit_posts.extraction_log_message IS
    'Log message for extraction: skip reason (if skipped), error message (if failed), or NULL (if processed)';

-- Update extraction_status comment to include 'failed'
COMMENT ON COLUMN reddit_posts.extraction_status IS
    'Status of extraction: pending (not yet attempted), processed (successfully extracted), skipped (filtered out), failed (error during extraction)';
