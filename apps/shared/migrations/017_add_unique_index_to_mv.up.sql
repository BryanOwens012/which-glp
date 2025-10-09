-- Add unique index to materialized view to enable concurrent refresh
-- This allows REFRESH MATERIALIZED VIEW CONCURRENTLY to work

CREATE UNIQUE INDEX IF NOT EXISTS mv_experiences_denormalized_post_id_idx
ON mv_experiences_denormalized (post_id);
