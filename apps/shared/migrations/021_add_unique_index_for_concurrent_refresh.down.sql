-- Migration 021 Rollback: Remove UNIQUE index and restore regular index
--
-- This reverts the changes made in 021_add_unique_index_for_concurrent_refresh.up.sql
-- WARNING: After rolling back, concurrent refreshes will fail. Use blocking refresh instead.

-- Drop the UNIQUE index
DROP INDEX IF EXISTS idx_mv_experiences_post_id_unique;

-- Restore the original non-unique index
CREATE INDEX IF NOT EXISTS idx_mv_experiences_post_id
  ON mv_experiences_denormalized(post_id);

-- Restore the original comment (without concurrent refresh note)
COMMENT ON MATERIALIZED VIEW mv_experiences_denormalized IS
  'Deduplicated view of experiences (one per post_id) with pre-calculated metrics.
   Filters: Only includes records with primary_drug AND non-empty summary (successfully extracted).
   Deduplication strategy: DISTINCT ON (post_id) prioritizing post-level extractions over comments.
   Refresh strategy: REFRESH MATERIALIZED VIEW CONCURRENTLY mv_experiences_denormalized;
   Schedule: Run after batch extraction jobs (daily/weekly depending on ingestion volume).
   This view powers all frontend queries for better performance.';
