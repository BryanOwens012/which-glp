-- Rollback: Reset processed posts back to pending
-- This reverts 025_backfill_extraction_status.up.sql

-- Reset posts that were marked as processed back to pending
UPDATE reddit_posts
SET
    extraction_status = 'pending',
    extraction_attempted_at = NULL
WHERE extraction_status = 'processed';
