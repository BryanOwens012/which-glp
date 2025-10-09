-- Rollback: Restore original ordering for extraction queries
-- This reverts 030_update_extraction_query_ordering.up.sql

-- Restore get_unprocessed_posts: Order by created_at DESC
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
    WHERE p.extraction_status = 'pending'
        AND (p_subreddit IS NULL OR p.subreddit = p_subreddit)
    ORDER BY p.created_at DESC  -- Original ordering
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Restore get_unanalyzed_users: Order by author only (no GROUP BY)
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
    WHERE ef.user_extraction_status = 'pending'
        AND rp.author IS NOT NULL
        AND rp.author != '[deleted]'
        AND rp.author != 'AutoModerator'
        AND ef.summary IS NOT NULL
        AND ef.summary != ''
        AND LENGTH(TRIM(ef.summary)) > 0
    ORDER BY rp.author  -- Original ordering
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Re-grant permissions
GRANT EXECUTE ON FUNCTION get_unprocessed_posts TO authenticated;
GRANT EXECUTE ON FUNCTION get_unprocessed_posts TO anon;
GRANT EXECUTE ON FUNCTION get_unanalyzed_users TO authenticated;
GRANT EXECUTE ON FUNCTION get_unanalyzed_users TO anon;

-- Restore original comments
COMMENT ON FUNCTION get_unprocessed_posts IS 'Returns posts with extraction_status = pending (not yet processed or skipped)';
COMMENT ON FUNCTION get_unanalyzed_users IS 'Returns distinct Reddit authors from extracted_features with user_extraction_status = pending. Uses status flags for fast filtering (10-100x faster than LEFT JOIN). Only includes authors with non-empty summaries (successfully extracted posts).';
