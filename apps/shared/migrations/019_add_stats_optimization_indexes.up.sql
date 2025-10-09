-- Migration 019: Add indexes to optimize stats aggregation functions
-- These indexes significantly improve performance of get_drug_stats(), get_demographics_stats(), and get_location_stats()

-- ============================================================================
-- Indexes for get_drug_stats() function optimization
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

-- ============================================================================
-- Indexes for get_demographics_stats() function optimization
-- ============================================================================

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

-- ============================================================================
-- Indexes for get_location_stats() function optimization
-- ============================================================================

-- Covering index for location GROUP BY with aggregated columns
-- This allows index-only scans for location stats
CREATE INDEX IF NOT EXISTS idx_mv_experiences_location_covering
  ON mv_experiences_denormalized(
    location,
    cost_per_month,
    has_insurance
  ) WHERE location IS NOT NULL;

-- ============================================================================
-- Additional performance optimization: Update statistics
-- ============================================================================

-- Ensure PostgreSQL query planner has up-to-date statistics for optimal query plans
ANALYZE mv_experiences_denormalized;

-- Add comment explaining index strategy
COMMENT ON INDEX idx_mv_experiences_drug_covering IS
  'Covering index for get_drug_stats() - enables index-only scans for drug aggregations';

COMMENT ON INDEX idx_mv_experiences_location_covering IS
  'Covering index for get_location_stats() - enables index-only scans for location aggregations';
