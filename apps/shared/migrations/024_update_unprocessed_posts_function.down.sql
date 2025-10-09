-- Rollback: Restore original get_unprocessed_posts function using LEFT JOIN
-- This reverts 024_update_unprocessed_posts_function.up.sql

-- Drop the flag-based function
DROP FUNCTION IF EXISTS get_unprocessed_posts(TEXT, INTEGER);

-- Restore original LEFT JOIN version
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
    LEFT JOIN extracted_features ef ON p.post_id = ef.post_id
    WHERE ef.post_id IS NULL  -- Posts that don't have extracted features
        AND (p_subreddit IS NULL OR p.subreddit = p_subreddit)
    ORDER BY p.created_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION get_unprocessed_posts TO authenticated;
GRANT EXECUTE ON FUNCTION get_unprocessed_posts TO anon;
