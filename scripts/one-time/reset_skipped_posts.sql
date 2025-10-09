-- One-time query to reset skipped posts for re-extraction
--
-- Context: After adding subreddit name to pre-filters (commit 78fae6c),
-- posts in drug-specific subreddits (r/Zepbound, r/Ozempic, etc.) that
-- were previously skipped due to missing explicit drug mentions should
-- now pass the filter and be processed.
--
-- This query resets all skipped posts to pending status so they can be
-- re-evaluated with the new subreddit-aware filter logic.
--
-- Date: 2025-10-09
-- Author: Claude Code

-- Display current counts before update
SELECT
    extraction_status,
    COUNT(*) as count
FROM reddit_posts
GROUP BY extraction_status
ORDER BY extraction_status;

-- Reset skipped posts to pending
UPDATE reddit_posts
SET
    extraction_status = 'pending',
    extraction_attempted_at = NULL,
    extraction_log_message = NULL
WHERE
    extraction_status = 'skipped';

-- Display updated counts after update
SELECT
    extraction_status,
    COUNT(*) as count
FROM reddit_posts
GROUP BY extraction_status
ORDER BY extraction_status;

-- Show sample of reset posts by subreddit
SELECT
    subreddit,
    COUNT(*) as reset_count
FROM reddit_posts
WHERE extraction_status = 'pending'
GROUP BY subreddit
ORDER BY reset_count DESC
LIMIT 10;
