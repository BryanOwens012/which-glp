-- Migration: Update get_unanalyzed_users to use user_extraction_status flags
-- Created: 2025-10-08
-- Description: Optimizes user extraction query by using status flags instead of LEFT JOIN

-- Replace the function to use status flags for filtering
-- OLD APPROACH: LEFT JOIN reddit_users to find users not yet analyzed (slow)
-- NEW APPROACH: WHERE user_extraction_status = 'pending' (fast, uses partial index)
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
    WHERE ef.user_extraction_status = 'pending'  -- NEW: Use status flag instead of LEFT JOIN
        AND rp.author IS NOT NULL
        AND rp.author != '[deleted]'
        AND rp.author != 'AutoModerator'
        -- Continue filtering for non-empty summaries (only process successfully extracted posts)
        AND ef.summary IS NOT NULL
        AND ef.summary != ''
        AND LENGTH(TRIM(ef.summary)) > 0
    ORDER BY rp.author
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT EXECUTE ON FUNCTION get_unanalyzed_users TO authenticated;
GRANT EXECUTE ON FUNCTION get_unanalyzed_users TO anon;

-- Update comment
COMMENT ON FUNCTION get_unanalyzed_users IS 'Returns distinct Reddit authors from extracted_features with user_extraction_status = pending. Uses status flags for fast filtering (10-100x faster than LEFT JOIN). Only includes authors with non-empty summaries (successfully extracted posts).';
