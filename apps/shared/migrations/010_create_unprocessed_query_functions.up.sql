-- Create PostgreSQL functions for efficient unprocessed data queries
-- These functions perform JOINs at the database level instead of transferring data to Python

-- Function to get unprocessed posts (posts not in extracted_features)
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

-- Function to get unanalyzed users (authors with extracted features but not in reddit_users)
-- Note: extracted_features only has post_id (not author), so we join with reddit_posts to get author
CREATE OR REPLACE FUNCTION get_unanalyzed_users(
    p_limit INTEGER DEFAULT NULL
)
RETURNS TABLE (
    author TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT rp.author
    FROM extracted_features ef
    INNER JOIN reddit_posts rp ON ef.post_id = rp.post_id
    LEFT JOIN reddit_users ru ON rp.author = ru.username
    WHERE ru.username IS NULL  -- Authors who haven't been analyzed
        AND rp.author IS NOT NULL
        AND rp.author != '[deleted]'
        AND rp.author != 'AutoModerator'
    ORDER BY rp.author
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Grant execute permissions to authenticated users
GRANT EXECUTE ON FUNCTION get_unprocessed_posts TO authenticated;
GRANT EXECUTE ON FUNCTION get_unprocessed_posts TO anon;
GRANT EXECUTE ON FUNCTION get_unanalyzed_users TO authenticated;
GRANT EXECUTE ON FUNCTION get_unanalyzed_users TO anon;
