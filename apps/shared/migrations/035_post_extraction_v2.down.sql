-- Keep in sync with 035_post_extraction_v2.up.sql.
-- Reverses it in reverse order: restores get_unprocessed_posts as 030 defined it (with
-- 034's grants and search_path), then drops the post-v2 columns. Data in those columns
-- is lost.

BEGIN;

DROP FUNCTION IF EXISTS get_unprocessed_posts(text, integer);

CREATE FUNCTION get_unprocessed_posts(
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
    ORDER BY p.ingested_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

REVOKE ALL ON FUNCTION get_unprocessed_posts(text, integer) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION get_unprocessed_posts(text, integer) TO service_role;
ALTER FUNCTION get_unprocessed_posts(text, integer) SET search_path = pg_catalog, public;
COMMENT ON FUNCTION get_unprocessed_posts(text, integer) IS 'Returns posts with extraction_status = pending, ordered by ingested_at DESC (newest first)';

ALTER TABLE extracted_features DROP CONSTRAINT IF EXISTS extracted_features_drugs_is_array;
ALTER TABLE extracted_features DROP CONSTRAINT IF EXISTS extracted_features_treatment_status_check;
ALTER TABLE extracted_features DROP CONSTRAINT IF EXISTS extracted_features_post_type_check;

ALTER TABLE extracted_features
    DROP COLUMN IF EXISTS drugs,
    DROP COLUMN IF EXISTS weight_lost,
    DROP COLUMN IF EXISTS treatment_status,
    DROP COLUMN IF EXISTS post_type,
    DROP COLUMN IF EXISTS extraction_version;

COMMIT;
