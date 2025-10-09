-- Migration 011: Update get_unanalyzed_users function to filter for non-empty summaries
-- This ensures user extraction only processes users whose posts have been successfully extracted
-- (summary is NOT NULL and NOT empty string)

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
        -- NEW FILTER: Only include users whose posts have non-empty summaries
        -- This ensures we only process users with successfully extracted post data
        AND ef.summary IS NOT NULL
        AND ef.summary != ''
        AND LENGTH(TRIM(ef.summary)) > 0
    ORDER BY rp.author
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Grant execute permissions to authenticated users (already granted, but included for completeness)
GRANT EXECUTE ON FUNCTION get_unanalyzed_users TO authenticated;
GRANT EXECUTE ON FUNCTION get_unanalyzed_users TO anon;

-- Add comment explaining the change
COMMENT ON FUNCTION get_unanalyzed_users IS 'Returns distinct Reddit authors from extracted_features who have not yet been analyzed in reddit_users table. Filters for non-empty summaries to ensure only successfully extracted posts are considered.';
