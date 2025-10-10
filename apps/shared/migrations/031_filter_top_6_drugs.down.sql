-- Rollback: Restore original stats functions without top N filter
-- Migration 031 rollback

-- ============================================================================
-- 1. Drop platform_config table
-- ============================================================================
DROP TABLE IF EXISTS platform_config;

-- ============================================================================
-- 2. Restore original get_drug_stats (all drugs)
-- ============================================================================
CREATE OR REPLACE FUNCTION get_drug_stats()
RETURNS TABLE (
  drug TEXT,
  count BIGINT,
  avg_weight_loss_percentage NUMERIC,
  avg_weight_loss_lbs NUMERIC,
  avg_duration_weeks NUMERIC,
  avg_cost_per_month NUMERIC,
  avg_sentiment_pre NUMERIC,
  avg_sentiment_post NUMERIC,
  avg_recommendation_score NUMERIC,
  plateau_rate NUMERIC,
  rebound_rate NUMERIC,
  insurance_coverage_rate NUMERIC,
  brand_count BIGINT,
  compounded_count BIGINT,
  out_of_pocket_count BIGINT
)
LANGUAGE SQL
STABLE
AS $$
  SELECT
    primary_drug AS drug,
    COUNT(*) AS count,
    AVG(weight_loss_percentage) AS avg_weight_loss_percentage,
    AVG(weight_loss_lbs) AS avg_weight_loss_lbs,
    AVG(duration_weeks) AS avg_duration_weeks,
    AVG(cost_per_month) AS avg_cost_per_month,
    AVG(sentiment_pre) AS avg_sentiment_pre,
    AVG(sentiment_post) AS avg_sentiment_post,
    AVG(recommendation_score) AS avg_recommendation_score,
    (COUNT(*) FILTER (WHERE plateau_mentioned = true) * 100.0 / NULLIF(COUNT(*), 0)) AS plateau_rate,
    (COUNT(*) FILTER (WHERE rebound_weight_gain = true) * 100.0 / NULLIF(COUNT(*), 0)) AS rebound_rate,
    (COUNT(*) FILTER (WHERE has_insurance = true) * 100.0 / NULLIF(COUNT(*), 0)) AS insurance_coverage_rate,
    COUNT(*) FILTER (WHERE drug_source = 'brand') AS brand_count,
    COUNT(*) FILTER (WHERE drug_source = 'compounded') AS compounded_count,
    COUNT(*) FILTER (WHERE cost_per_month IS NOT NULL AND has_insurance = false) AS out_of_pocket_count
  FROM mv_experiences_denormalized
  WHERE primary_drug IS NOT NULL
  GROUP BY primary_drug
  ORDER BY count DESC;
$$;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION get_drug_stats() TO authenticated;
GRANT EXECUTE ON FUNCTION get_drug_stats() TO anon;
GRANT EXECUTE ON FUNCTION get_drug_stats() TO service_role;

-- ============================================================================
-- 3. Restore original get_platform_stats (all drugs)
-- ============================================================================
CREATE OR REPLACE FUNCTION get_platform_stats()
RETURNS TABLE (
  total_experiences BIGINT,
  unique_drugs BIGINT,
  locations_tracked BIGINT
)
LANGUAGE SQL
STABLE
AS $$
  SELECT
    COUNT(*) AS total_experiences,
    COUNT(DISTINCT primary_drug) FILTER (WHERE primary_drug IS NOT NULL) AS unique_drugs,
    COUNT(DISTINCT location) FILTER (WHERE location IS NOT NULL) AS locations_tracked
  FROM mv_experiences_denormalized;
$$;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION get_platform_stats() TO authenticated;
GRANT EXECUTE ON FUNCTION get_platform_stats() TO anon;
GRANT EXECUTE ON FUNCTION get_platform_stats() TO service_role;
