-- Migration 020: Filter mv_experiences_denormalized to exclude empty summaries
-- This ensures the materialized view only includes successfully extracted posts/comments
-- with non-null and non-empty summary fields

-- Drop the existing materialized view
DROP MATERIALIZED VIEW IF EXISTS mv_experiences_denormalized CASCADE;

-- Recreate with summary filter added to WHERE clause
CREATE MATERIALIZED VIEW mv_experiences_denormalized AS
SELECT DISTINCT ON (post_id)
  -- Primary keys and references
  ef.id AS feature_id,
  ef.post_id,
  ef.comment_id,
  COALESCE(rp.subreddit, rc.subreddit) AS subreddit,
  ef.processed_at,

  -- Reddit content (from posts or comments)
  COALESCE(rp.title, '') AS post_title,
  COALESCE(rp.body, '') AS post_text,
  COALESCE(rc.body, '') AS comment_text,
  COALESCE(rp.author, rc.author) AS author,
  COALESCE(rp.created_at, rc.created_at) AS created_at,
  COALESCE(rp.score, rc.score, 0) AS score,
  CASE WHEN ef.post_id IS NOT NULL THEN 'post' ELSE 'comment' END AS source_type,

  -- Extracted features
  ef.primary_drug,
  ef.summary,
  ef.sentiment_pre,
  ef.sentiment_post,
  ef.recommendation_score,
  ef.age,
  ef.sex,
  ef.location,
  ef.state,
  ef.country,
  ef.beginning_weight,
  ef.end_weight,
  ef.duration_weeks,
  ef.cost_per_month,
  ef.currency,
  ef.has_insurance,
  ef.insurance_provider,
  ef.side_effects, -- Full JSONB with severity info
  ef.comorbidities,
  ef.drug_source,
  ef.pharmacy_access_issues,
  ef.plateau_mentioned,
  ef.rebound_weight_gain,
  ef.side_effect_timing,
  ef.side_effect_resolution,
  ef.food_intolerances,
  ef.dosage_progression,
  ef.exercise_frequency,
  ef.dietary_changes,
  ef.labs_improvement,
  ef.medication_reduction,
  ef.nsv_mentioned,
  ef.support_system,
  ef.mental_health_impact,

  -- Pre-calculated fields for performance
  -- Weight loss in lbs (extract from JSONB)
  CASE
    WHEN ef.beginning_weight->>'value' IS NOT NULL
      AND ef.end_weight->>'value' IS NOT NULL
      AND ef.beginning_weight->>'unit' = 'lbs'
      AND ef.end_weight->>'unit' = 'lbs'
    THEN (ef.beginning_weight->>'value')::numeric - (ef.end_weight->>'value')::numeric
    WHEN ef.beginning_weight->>'value' IS NOT NULL
      AND ef.end_weight->>'value' IS NOT NULL
      AND ef.beginning_weight->>'unit' = 'kg'
      AND ef.end_weight->>'unit' = 'kg'
    THEN ((ef.beginning_weight->>'value')::numeric - (ef.end_weight->>'value')::numeric) * 2.20462
    ELSE NULL
  END AS weight_loss_lbs,

  -- Weight loss percentage
  CASE
    WHEN ef.beginning_weight->>'value' IS NOT NULL
      AND ef.end_weight->>'value' IS NOT NULL
      AND (ef.beginning_weight->>'value')::numeric > 0
    THEN ((ef.beginning_weight->>'value')::numeric - (ef.end_weight->>'value')::numeric)
         / (ef.beginning_weight->>'value')::numeric * 100
    ELSE NULL
  END AS weight_loss_percentage,

  -- Weight loss speed in lbs per month
  CASE
    WHEN ef.beginning_weight->>'value' IS NOT NULL
      AND ef.end_weight->>'value' IS NOT NULL
      AND ef.duration_weeks IS NOT NULL
      AND ef.duration_weeks > 0
      AND ef.beginning_weight->>'unit' = 'lbs'
      AND ef.end_weight->>'unit' = 'lbs'
    THEN ((ef.beginning_weight->>'value')::numeric - (ef.end_weight->>'value')::numeric)
         / (ef.duration_weeks / 4.33)
    WHEN ef.beginning_weight->>'value' IS NOT NULL
      AND ef.end_weight->>'value' IS NOT NULL
      AND ef.duration_weeks IS NOT NULL
      AND ef.duration_weeks > 0
      AND ef.beginning_weight->>'unit' = 'kg'
      AND ef.end_weight->>'unit' = 'kg'
    THEN (((ef.beginning_weight->>'value')::numeric - (ef.end_weight->>'value')::numeric) * 2.20462)
         / (ef.duration_weeks / 4.33)
    ELSE NULL
  END AS weight_loss_speed_lbs_per_month,

  -- Weight loss speed in percentage per month
  CASE
    WHEN ef.beginning_weight->>'value' IS NOT NULL
      AND ef.end_weight->>'value' IS NOT NULL
      AND ef.duration_weeks IS NOT NULL
      AND ef.duration_weeks > 0
      AND (ef.beginning_weight->>'value')::numeric > 0
    THEN (((ef.beginning_weight->>'value')::numeric - (ef.end_weight->>'value')::numeric)
          / (ef.beginning_weight->>'value')::numeric * 100)
         / (ef.duration_weeks / 4.33)
    ELSE NULL
  END AS weight_loss_speed_percent_per_month,

  -- Beginning weight in lbs
  CASE
    WHEN ef.beginning_weight->>'unit' = 'lbs'
    THEN (ef.beginning_weight->>'value')::numeric
    WHEN ef.beginning_weight->>'unit' = 'kg'
    THEN (ef.beginning_weight->>'value')::numeric * 2.20462
    ELSE NULL
  END AS beginning_weight_lbs,

  -- End weight in lbs
  CASE
    WHEN ef.end_weight->>'unit' = 'lbs'
    THEN (ef.end_weight->>'value')::numeric
    WHEN ef.end_weight->>'unit' = 'kg'
    THEN (ef.end_weight->>'value')::numeric * 2.20462
    ELSE NULL
  END AS end_weight_lbs,

  -- Sentiment change
  CASE
    WHEN ef.sentiment_pre IS NOT NULL AND ef.sentiment_post IS NOT NULL
    THEN ef.sentiment_post - ef.sentiment_pre
    ELSE NULL
  END AS sentiment_change,

  -- Age bucket for demographic analysis
  CASE
    WHEN ef.age < 25 THEN '18-24'
    WHEN ef.age < 35 THEN '25-34'
    WHEN ef.age < 45 THEN '35-44'
    WHEN ef.age < 55 THEN '45-54'
    WHEN ef.age < 65 THEN '55-64'
    ELSE '65+'
  END AS age_bucket,

  -- Top side effects (extract from JSONB array for convenience)
  CASE
    WHEN ef.side_effects IS NOT NULL
    THEN (
      SELECT array_agg(value::text)
      FROM jsonb_array_elements_text(ef.side_effects)
      LIMIT 5
    )
    ELSE ARRAY[]::text[]
  END AS top_side_effects

FROM extracted_features ef
LEFT JOIN reddit_posts rp ON ef.post_id = rp.post_id
LEFT JOIN reddit_comments rc ON ef.comment_id = rc.comment_id
WHERE ef.primary_drug IS NOT NULL -- Only include records with identified drug
  -- NEW FILTERS: Only include records with non-empty summaries (successfully extracted)
  AND ef.summary IS NOT NULL
  AND ef.summary != ''
  AND LENGTH(TRIM(ef.summary)) > 0
ORDER BY
  post_id,
  -- Prioritize post-level extractions (comment_id IS NULL) over comment-level
  CASE WHEN ef.comment_id IS NULL THEN 0 ELSE 1 END,
  -- Then by sentiment_post (prefer records with better data)
  ef.sentiment_post DESC NULLS LAST,
  -- Finally by processed_at (most recent extraction)
  ef.processed_at DESC;

-- Create indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_mv_experiences_drug
  ON mv_experiences_denormalized(primary_drug);

CREATE INDEX IF NOT EXISTS idx_mv_experiences_subreddit
  ON mv_experiences_denormalized(subreddit);

CREATE INDEX IF NOT EXISTS idx_mv_experiences_location
  ON mv_experiences_denormalized(location);

CREATE INDEX IF NOT EXISTS idx_mv_experiences_created
  ON mv_experiences_denormalized(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_mv_experiences_weight_loss
  ON mv_experiences_denormalized(weight_loss_lbs DESC NULLS LAST);

CREATE INDEX IF NOT EXISTS idx_mv_experiences_recommendation
  ON mv_experiences_denormalized(recommendation_score DESC NULLS LAST);

CREATE INDEX IF NOT EXISTS idx_mv_experiences_weight_loss_pct
  ON mv_experiences_denormalized(weight_loss_percentage DESC NULLS LAST);

CREATE INDEX IF NOT EXISTS idx_mv_experiences_weight_loss_speed_lbs
  ON mv_experiences_denormalized(weight_loss_speed_lbs_per_month DESC NULLS LAST);

CREATE INDEX IF NOT EXISTS idx_mv_experiences_weight_loss_speed_pct
  ON mv_experiences_denormalized(weight_loss_speed_percent_per_month DESC NULLS LAST);

CREATE INDEX IF NOT EXISTS idx_mv_experiences_sentiment_post
  ON mv_experiences_denormalized(sentiment_post DESC NULLS LAST);

CREATE INDEX IF NOT EXISTS idx_mv_experiences_post_id
  ON mv_experiences_denormalized(post_id);

-- Index on author for filtering by user
CREATE INDEX IF NOT EXISTS idx_mv_experiences_author
  ON mv_experiences_denormalized(author);

-- Composite index for drug + location filtering
CREATE INDEX IF NOT EXISTS idx_mv_experiences_drug_location
  ON mv_experiences_denormalized(primary_drug, location);

-- Composite index for age demographics
CREATE INDEX IF NOT EXISTS idx_mv_experiences_drug_age
  ON mv_experiences_denormalized(primary_drug, age_bucket);

-- GIN index for JSONB arrays (side_effects, comorbidities)
CREATE INDEX IF NOT EXISTS idx_mv_experiences_side_effects
  ON mv_experiences_denormalized USING gin(side_effects);

CREATE INDEX IF NOT EXISTS idx_mv_experiences_comorbidities
  ON mv_experiences_denormalized USING gin(comorbidities);

-- ============================================================================
-- Stats optimization indexes (from migration 019)
-- ============================================================================

-- Partial indexes for boolean columns used in FILTER clauses
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
CREATE INDEX IF NOT EXISTS idx_mv_experiences_location_covering
  ON mv_experiences_denormalized(
    location,
    cost_per_month,
    has_insurance
  ) WHERE location IS NOT NULL;

-- Comment explaining refresh strategy and new filter
COMMENT ON MATERIALIZED VIEW mv_experiences_denormalized IS
  'Deduplicated view of experiences (one per post_id) with pre-calculated metrics.
   Filters: Only includes records with primary_drug AND non-empty summary (successfully extracted).
   Deduplication strategy: DISTINCT ON (post_id) prioritizing post-level extractions over comments.
   Refresh strategy: REFRESH MATERIALIZED VIEW CONCURRENTLY mv_experiences_denormalized;
   Schedule: Run after batch extraction jobs (daily/weekly depending on ingestion volume).
   This view powers all frontend queries for better performance.';
