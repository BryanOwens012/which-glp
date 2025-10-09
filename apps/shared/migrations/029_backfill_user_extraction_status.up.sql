-- Migration: Backfill user_extraction_status for existing processed users
-- Created: 2025-10-08
-- Description: Marks extracted_features as 'processed' where user demographics have already been extracted

-- Update extracted_features to 'processed' where user demographics exist in reddit_users
-- Join on author from reddit_posts to find which extracted_features have been processed
UPDATE extracted_features ef
SET user_extraction_status = 'processed',
    user_extraction_attempted_at = ru.analyzed_at
FROM reddit_posts rp
INNER JOIN reddit_users ru ON rp.author = ru.username
WHERE ef.post_id = rp.post_id
    AND ef.user_extraction_status = 'pending';

-- Log the count of updated rows
DO $$
DECLARE
    updated_count INTEGER;
BEGIN
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RAISE NOTICE 'Backfilled % extracted_features rows to user_extraction_status = processed', updated_count;
END $$;
