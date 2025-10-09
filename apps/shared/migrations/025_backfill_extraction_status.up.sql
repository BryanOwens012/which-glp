-- Migration: Backfill extraction_status for already-processed posts
-- Created: 2025-10-08
-- Description: Set extraction_status='processed' for posts that already have extracted_features

-- Update posts that have been extracted to mark them as processed
UPDATE reddit_posts
SET
    extraction_status = 'processed',
    extraction_attempted_at = ef.processed_at
FROM extracted_features ef
WHERE reddit_posts.post_id = ef.post_id
    AND reddit_posts.extraction_status = 'pending';

-- Report the changes
DO $$
DECLARE
    updated_count INTEGER;
BEGIN
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RAISE NOTICE 'Updated % posts from pending to processed', updated_count;
END $$;
