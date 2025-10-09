-- Migration: Update get_unprocessed_posts to use extraction_status flags
-- Created: 2025-10-08
-- Description: Modify get_unprocessed_posts function to query based on extraction_status instead of LEFT JOIN

-- Drop old function
DROP FUNCTION IF EXISTS get_unprocessed_posts(TEXT, INTEGER);

-- Recreate function using extraction_status flag
CREATE OR REPLACE FUNCTION get_unprocessed_posts(
    p_subreddit TEXT DEFAULT NULL,
    p_limit INTEGER DEFAULT NULL
)
RETURNS TABLE (
    post_id TEXT,
    title TEXT,
    body TEXT,
    subreddit TEXT,
    author_flair_text TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.post_id,
        p.title,
        p.body,
        p.subreddit,
        p.author_flair_text
    FROM reddit_posts p
    WHERE p.extraction_status = 'pending'  -- Only get posts that haven't been attempted yet
        AND (p_subreddit IS NULL OR p.subreddit = p_subreddit)
    ORDER BY p.created_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION get_unprocessed_posts TO authenticated;
GRANT EXECUTE ON FUNCTION get_unprocessed_posts TO anon;

-- Add comment
COMMENT ON FUNCTION get_unprocessed_posts IS 'Returns posts with extraction_status = pending (not yet processed or skipped)';
