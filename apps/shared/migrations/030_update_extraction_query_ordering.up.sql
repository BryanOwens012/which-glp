-- Migration: Update extraction query ordering for newest-first processing
-- Created: 2025-10-08
-- Description: Changes ORDER BY clauses to process newest items first (without changing any indexes)

-- Update get_unprocessed_posts: Order by ingested_at DESC (newest first)
-- ONLY CHANGE: ORDER BY p.created_at DESC -> ORDER BY p.ingested_at DESC
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
    ORDER BY p.ingested_at DESC  -- CHANGED: Process newest ingested posts first
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Update get_unanalyzed_users: Order by MAX(processed_at) DESC (newest first)
-- ONLY CHANGE: ORDER BY rp.author -> ORDER BY MAX(ef.processed_at) DESC, rp.author
-- We need to add GROUP BY since we're using MAX aggregate function
CREATE OR REPLACE FUNCTION get_unanalyzed_users(
    p_limit INTEGER DEFAULT NULL
)
RETURNS TABLE (
    author TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT rp.author
    FROM extracted_features ef
    INNER JOIN reddit_posts rp ON ef.post_id = rp.post_id
    WHERE ef.user_extraction_status = 'pending'  -- Use status flag instead of LEFT JOIN
        AND rp.author IS NOT NULL
        AND rp.author != '[deleted]'
        AND rp.author != 'AutoModerator'
        -- Continue filtering for non-empty summaries (only process successfully extracted posts)
        AND ef.summary IS NOT NULL
        AND ef.summary != ''
        AND LENGTH(TRIM(ef.summary)) > 0
    GROUP BY rp.author
    ORDER BY MAX(ef.processed_at) DESC, rp.author  -- CHANGED: Process newest extracted users first
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (re-grant after function replacement)
GRANT EXECUTE ON FUNCTION get_unprocessed_posts TO authenticated;
GRANT EXECUTE ON FUNCTION get_unprocessed_posts TO anon;
GRANT EXECUTE ON FUNCTION get_unanalyzed_users TO authenticated;
GRANT EXECUTE ON FUNCTION get_unanalyzed_users TO anon;

-- Update comments
COMMENT ON FUNCTION get_unprocessed_posts IS 'Returns posts with extraction_status = pending, ordered by ingested_at DESC (newest first)';
COMMENT ON FUNCTION get_unanalyzed_users IS 'Returns distinct Reddit authors from extracted_features with user_extraction_status = pending, ordered by newest processed_at first. Uses status flags for fast filtering (10-100x faster than LEFT JOIN). Only includes authors with non-empty summaries (successfully extracted posts).';

-- NOTE: This migration does NOT create, drop, or modify any indexes
-- All existing indexes remain unchanged
