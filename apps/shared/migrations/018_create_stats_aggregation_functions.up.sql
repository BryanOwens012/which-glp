-- Create SQL functions for efficient stats aggregation
-- These functions compute statistics in PostgreSQL rather than fetching all data to TypeScript
-- Migration 018: Stats aggregation functions for drugs, demographics, locations, and platform routers

-- ============================================================================
-- 1. get_drug_stats: Aggregate all drug statistics by primary_drug
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
-- 2. get_demographics_stats: Aggregate age, sex, and weight distributions
-- ============================================================================
CREATE OR REPLACE FUNCTION get_demographics_stats()
RETURNS TABLE (
  category TEXT,
  subcategory TEXT,
  count BIGINT
)
LANGUAGE SQL
STABLE
AS $$
  -- Age distribution
  SELECT
    'age' AS category,
    CASE
      WHEN age >= 18 AND age <= 24 THEN '18-24'
      WHEN age >= 25 AND age <= 34 THEN '25-34'
      WHEN age >= 35 AND age <= 44 THEN '35-44'
      WHEN age >= 45 AND age <= 54 THEN '45-54'
      WHEN age >= 55 AND age <= 64 THEN '55-64'
      WHEN age >= 65 THEN '65+'
    END AS subcategory,
    COUNT(*) AS count
  FROM mv_experiences_denormalized
  WHERE age IS NOT NULL
  GROUP BY subcategory

  UNION ALL

  -- Sex distribution
  SELECT
    'sex' AS category,
    CASE
      WHEN LOWER(sex) IN ('male', 'm') THEN 'Male'
      WHEN LOWER(sex) IN ('female', 'f') THEN 'Female'
      ELSE 'Other'
    END AS subcategory,
    COUNT(*) AS count
  FROM mv_experiences_denormalized
  WHERE sex IS NOT NULL
  GROUP BY subcategory

  UNION ALL

  -- Weight distribution
  SELECT
    'weight' AS category,
    CASE
      WHEN beginning_weight_lbs >= 100 AND beginning_weight_lbs < 150 THEN '100-150'
      WHEN beginning_weight_lbs >= 150 AND beginning_weight_lbs < 200 THEN '150-200'
      WHEN beginning_weight_lbs >= 200 AND beginning_weight_lbs < 250 THEN '200-250'
      WHEN beginning_weight_lbs >= 250 AND beginning_weight_lbs < 300 THEN '250-300'
      WHEN beginning_weight_lbs >= 300 THEN '300+'
    END AS subcategory,
    COUNT(*) AS count
  FROM mv_experiences_denormalized
  WHERE beginning_weight_lbs IS NOT NULL
  GROUP BY subcategory

  ORDER BY category, subcategory;
$$;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION get_demographics_stats() TO authenticated;
GRANT EXECUTE ON FUNCTION get_demographics_stats() TO anon;
GRANT EXECUTE ON FUNCTION get_demographics_stats() TO service_role;

-- ============================================================================
-- 3. get_location_stats: Aggregate statistics by location
-- ============================================================================
CREATE OR REPLACE FUNCTION get_location_stats()
RETURNS TABLE (
  location TEXT,
  count BIGINT,
  avg_cost NUMERIC,
  insurance_rate NUMERIC
)
LANGUAGE SQL
STABLE
AS $$
  SELECT
    location,
    COUNT(*) AS count,
    AVG(cost_per_month) AS avg_cost,
    (COUNT(*) FILTER (WHERE has_insurance = true) * 100.0 / NULLIF(COUNT(*), 0)) AS insurance_rate
  FROM mv_experiences_denormalized
  WHERE location IS NOT NULL
  GROUP BY location
  ORDER BY count DESC;
$$;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION get_location_stats() TO authenticated;
GRANT EXECUTE ON FUNCTION get_location_stats() TO anon;
GRANT EXECUTE ON FUNCTION get_location_stats() TO service_role;

-- ============================================================================
-- 4. get_platform_stats: Get overall platform statistics
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
