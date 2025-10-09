-- Rollback migration 011: Restore original get_unanalyzed_users function without summary filter

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
