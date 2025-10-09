-- Migration 021: Add UNIQUE index on post_id to enable concurrent materialized view refresh
--
-- PROBLEM:
-- The cron job was failing with error:
--   "cannot refresh materialized view 'public.mv_experiences_denormalized' concurrently"
--
-- ROOT CAUSE:
-- PostgreSQL requires a UNIQUE index on a materialized view to support
-- REFRESH MATERIALIZED VIEW CONCURRENTLY. Without it, only blocking (non-concurrent)
-- refreshes are possible.
--
-- Migration 020 created a regular index on post_id (line 217-218), but not a UNIQUE index.
-- Since the view uses DISTINCT ON (post_id), we know post_id is unique in the result set,
-- but PostgreSQL needs an explicit UNIQUE constraint to enable concurrent refreshes.
--
-- SOLUTION:
-- Drop the existing regular index and replace it with a UNIQUE index on post_id.
-- This enables concurrent refreshes without blocking queries to the materialized view.
--
-- REFERENCES:
-- https://www.postgresql.org/docs/current/sql-refreshmaterializedview.html
-- "CONCURRENTLY: Refresh the materialized view without locking out concurrent selects on
--  the materialized view. Without this option a refresh which affects a lot of rows will
--  tend to use fewer resources and complete more quickly, but could block other connections
--  which are trying to read from the materialized view. This option may be faster in cases
--  where a small number of rows are affected. This option is only allowed if there is at
--  least one UNIQUE index on the materialized view which uses only column names and includes
--  all rows; that is, it must not index on any expressions nor include a WHERE clause."

-- Drop the existing non-unique index
DROP INDEX IF EXISTS idx_mv_experiences_post_id;

-- Create a UNIQUE index on post_id
-- This is safe because the view uses DISTINCT ON (post_id), guaranteeing uniqueness
CREATE UNIQUE INDEX idx_mv_experiences_post_id_unique
  ON mv_experiences_denormalized(post_id);

-- Update the comment to reflect the concurrent refresh capability
COMMENT ON MATERIALIZED VIEW mv_experiences_denormalized IS
  'Deduplicated view of experiences (one per post_id) with pre-calculated metrics.
   Filters: Only includes records with primary_drug AND non-empty summary (successfully extracted).
   Deduplication strategy: DISTINCT ON (post_id) prioritizing post-level extractions over comments.
   Refresh strategy: REFRESH MATERIALIZED VIEW CONCURRENTLY mv_experiences_denormalized;
   Concurrent refresh enabled by UNIQUE index on post_id (idx_mv_experiences_post_id_unique).
   Schedule: Run after batch extraction jobs (daily/weekly depending on ingestion volume).
   This view powers all frontend queries for better performance.';
