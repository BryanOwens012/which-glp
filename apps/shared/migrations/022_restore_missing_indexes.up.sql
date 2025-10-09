-- Migration 022: Restore missing indexes that were dropped by migration 020
--
-- PROBLEM:
-- Migration 020 used "DROP MATERIALIZED VIEW ... CASCADE" which dropped ALL indexes
-- on the materialized view, including:
-- 1. Index on 'author' column (from migration 013)
-- 2. UNIQUE index on 'post_id' (from migration 017, needed for concurrent refresh)
-- 3. All stats optimization indexes (from migration 019)
--
-- Migration 020 only recreated the basic indexes but missed these critical ones,
-- causing:
-- - Slow queries filtering by author
-- - Concurrent refresh failures (missing UNIQUE index)
-- - Slow stats aggregation queries (missing covering/partial indexes)
--
-- SOLUTION:
-- Add all missing indexes back to the materialized view:
-- - Author index for user filtering
-- - Stats optimization indexes (partial indexes, covering indexes)
--
-- Note: UNIQUE index for concurrent refresh is handled by migration 021.

-- ============================================================================
-- Missing index from migration 013
-- ============================================================================

-- Index on author for filtering by user
CREATE INDEX IF NOT EXISTS idx_mv_experiences_author
  ON mv_experiences_denormalized(author);

-- ============================================================================
-- Missing indexes from migration 019 (stats optimization)
-- ============================================================================

-- Partial indexes for boolean columns used in FILTER clauses
-- These are much smaller than full indexes since they only index TRUE values
CREATE INDEX IF NOT EXISTS idx_mv_experiences_plateau_mentioned
  ON mv_experiences_denormalized(plateau_mentioned)
  WHERE plateau_mentioned = true;

CREATE INDEX IF NOT EXISTS idx_mv_experiences_rebound_weight_gain
  ON mv_experiences_denormalized(rebound_weight_gain)
  WHERE rebound_weight_gain = true;

CREATE INDEX IF NOT EXISTS idx_mv_experiences_has_insurance
  ON mv_experiences_denormalized(has_insurance)
  WHERE has_insurance IS NOT NULL;

-- Index on drug_source for filtering brand/compounded counts
CREATE INDEX IF NOT EXISTS idx_mv_experiences_drug_source
  ON mv_experiences_denormalized(drug_source)
  WHERE drug_source IS NOT NULL;

-- Covering index for primary_drug GROUP BY with commonly aggregated columns
-- This allows PostgreSQL to satisfy the entire query from the index (index-only scan)
CREATE INDEX IF NOT EXISTS idx_mv_experiences_drug_covering
  ON mv_experiences_denormalized(
    primary_drug,
    weight_loss_percentage,
    weight_loss_lbs,
    duration_weeks,
    cost_per_month,
    sentiment_pre,
    sentiment_post,
    recommendation_score
  ) WHERE primary_drug IS NOT NULL;

-- Index on age for age distribution bucketing
-- WHERE clause makes this a partial index (smaller, faster)
CREATE INDEX IF NOT EXISTS idx_mv_experiences_age
  ON mv_experiences_denormalized(age)
  WHERE age IS NOT NULL;

-- Index on sex for sex distribution
CREATE INDEX IF NOT EXISTS idx_mv_experiences_sex
  ON mv_experiences_denormalized(LOWER(sex))
  WHERE sex IS NOT NULL;

-- Index on beginning_weight_lbs for weight distribution bucketing
CREATE INDEX IF NOT EXISTS idx_mv_experiences_beginning_weight
  ON mv_experiences_denormalized(beginning_weight_lbs)
  WHERE beginning_weight_lbs IS NOT NULL;

-- Covering index for location GROUP BY with aggregated columns
-- This allows index-only scans for location stats
CREATE INDEX IF NOT EXISTS idx_mv_experiences_location_covering
  ON mv_experiences_denormalized(
    location,
    cost_per_month,
    has_insurance
  ) WHERE location IS NOT NULL;

-- ============================================================================
-- Update statistics for query planner
-- ============================================================================

-- Ensure PostgreSQL query planner has up-to-date statistics for optimal query plans
ANALYZE mv_experiences_denormalized;

-- Add comments explaining index strategy
COMMENT ON INDEX idx_mv_experiences_drug_covering IS
  'Covering index for get_drug_stats() - enables index-only scans for drug aggregations';

COMMENT ON INDEX idx_mv_experiences_location_covering IS
  'Covering index for get_location_stats() - enables index-only scans for location aggregations';
