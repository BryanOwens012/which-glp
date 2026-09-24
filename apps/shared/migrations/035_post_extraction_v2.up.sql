-- Migration: post-extraction v2 columns, and the posted date in get_unprocessed_posts
-- Description:
--   1. extracted_features gains the columns the post-v2 extractor writes:
--      extraction_version, post_type, treatment_status, weight_lost (JSONB), drugs (JSONB).
--      All nullable: rows extracted before post-v2 keep NULL, which marks them as such.
--   2. get_unprocessed_posts also returns created_at, so the extractor can resolve
--      relative dates ("since January") against the date the post was written.
--      A changed return type needs DROP + CREATE; the 034 grants and search_path are
--      re-applied.
-- Order: run BEFORE merging. Additive only; the currently deployed extractor ignores the
-- new columns and reads the RPC's result by key, so the extra column is harmless to it.
-- Grants: extracted_features uses table-level grants (033), which cover new columns.

BEGIN;

ALTER TABLE extracted_features
    ADD COLUMN IF NOT EXISTS extraction_version TEXT,
    ADD COLUMN IF NOT EXISTS post_type TEXT,
    ADD COLUMN IF NOT EXISTS treatment_status TEXT,
    ADD COLUMN IF NOT EXISTS weight_lost JSONB,
    ADD COLUMN IF NOT EXISTS drugs JSONB;

-- DROP + ADD rather than IF NOT EXISTS, so a same-named constraint with an older
-- definition is replaced instead of silently kept.
ALTER TABLE extracted_features DROP CONSTRAINT IF EXISTS extracted_features_post_type_check;
ALTER TABLE extracted_features ADD CONSTRAINT extracted_features_post_type_check
    CHECK (post_type IN ('experience_report', 'question', 'advice', 'news_or_discussion', 'other'));

ALTER TABLE extracted_features DROP CONSTRAINT IF EXISTS extracted_features_treatment_status_check;
ALTER TABLE extracted_features ADD CONSTRAINT extracted_features_treatment_status_check
    CHECK (treatment_status IN ('taking', 'paused', 'stopped', 'not_started', 'unknown'));

ALTER TABLE extracted_features DROP CONSTRAINT IF EXISTS extracted_features_drugs_is_array;
ALTER TABLE extracted_features ADD CONSTRAINT extracted_features_drugs_is_array
    CHECK (drugs IS NULL OR jsonb_typeof(drugs) = 'array');

COMMENT ON COLUMN extracted_features.extraction_version IS 'Extractor that wrote the row (e.g. post-v2); NULL for rows written before versioning';
COMMENT ON COLUMN extracted_features.post_type IS 'experience_report, question, advice, news_or_discussion, or other';
COMMENT ON COLUMN extracted_features.treatment_status IS 'The author''s status on their GLP-1: taking, paused, stopped, not_started, or unknown';
COMMENT ON COLUMN extracted_features.weight_lost IS 'Total weight lost since starting: {value, unit, quote} as stated, or {value, unit, quote: null, derived: true} from beginning_weight - end_weight';
COMMENT ON COLUMN extracted_features.drugs IS 'Every drug the post names: [{name, other_name, relation, source, sentiment}]; relation is current, previous, planned, or mentioned_only';

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
    author_flair_text TEXT,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.post_id,
        p.title,
        p.body,
        p.subreddit,
        p.author_flair_text,
        p.created_at
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
COMMENT ON FUNCTION get_unprocessed_posts(text, integer) IS 'Returns posts with extraction_status = pending, with their created_at, ordered by ingested_at DESC (newest first)';

COMMIT;
