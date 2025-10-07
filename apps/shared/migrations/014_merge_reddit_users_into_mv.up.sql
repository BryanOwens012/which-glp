-- Migration 014: Merge reddit_users data into mv_experiences_denormalized
-- Also add height_inches column which wasn't previously in the view

DROP MATERIALIZED VIEW IF EXISTS mv_experiences_denormalized;

CREATE MATERIALIZED VIEW mv_experiences_denormalized AS
SELECT DISTINCT ON (ef.post_id)
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

  -- Extracted features (merge with reddit_users data via author)
  ef.primary_drug,
  ef.summary,
  ef.sentiment_pre,
  ef.sentiment_post,
  ef.recommendation_score,

  -- Demographics: prefer post-specific data, fall back to user profile
  COALESCE(ef.age, ru.age) AS age,
  COALESCE(ef.sex, ru.sex) AS sex,
  ef.location,
  COALESCE(ef.state, ru.state) AS state,
  COALESCE(ef.country, ru.country) AS country,

  -- Height: only available from user profile
  ru.height_inches,

  -- Weight data (keep original JSONB for compatibility)
  ef.beginning_weight,
  ef.end_weight,
  ef.duration_weeks,

  -- Cost and insurance
  ef.cost_per_month,
  ef.currency,
  COALESCE(ef.has_insurance, ru.has_insurance) AS has_insurance,
  COALESCE(ef.insurance_provider, ru.insurance_provider) AS insurance_provider,

  -- Health data
  ef.side_effects,
  COALESCE(ef.comorbidities, ru.comorbidities) AS comorbidities,
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
  -- Weight loss in lbs (prefer post data, fall back to user profile)
  CASE
    -- If post has both beginning and end weight, use those
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
    -- If post has end weight and user profile has starting weight, use both
    WHEN ef.end_weight->>'value' IS NOT NULL
      AND ru.starting_weight_lbs IS NOT NULL
      AND ef.end_weight->>'unit' = 'lbs'
    THEN ru.starting_weight_lbs - (ef.end_weight->>'value')::numeric
    WHEN ef.end_weight->>'value' IS NOT NULL
      AND ru.starting_weight_lbs IS NOT NULL
      AND ef.end_weight->>'unit' = 'kg'
    THEN ru.starting_weight_lbs - ((ef.end_weight->>'value')::numeric * 2.20462)
    ELSE NULL
  END AS weight_loss_lbs,

  -- Weight loss percentage (using merged beginning weight)
  CASE
    WHEN ef.beginning_weight->>'value' IS NOT NULL
      AND ef.end_weight->>'value' IS NOT NULL
      AND (ef.beginning_weight->>'value')::numeric > 0
    THEN ((ef.beginning_weight->>'value')::numeric - (ef.end_weight->>'value')::numeric)
         / (ef.beginning_weight->>'value')::numeric * 100
    -- Use user profile starting weight if available
    WHEN ef.end_weight->>'value' IS NOT NULL
      AND ru.starting_weight_lbs IS NOT NULL
      AND ru.starting_weight_lbs > 0
      AND ef.end_weight->>'unit' = 'lbs'
    THEN (ru.starting_weight_lbs - (ef.end_weight->>'value')::numeric)
         / ru.starting_weight_lbs * 100
    WHEN ef.end_weight->>'value' IS NOT NULL
      AND ru.starting_weight_lbs IS NOT NULL
      AND ru.starting_weight_lbs > 0
      AND ef.end_weight->>'unit' = 'kg'
    THEN (ru.starting_weight_lbs - ((ef.end_weight->>'value')::numeric * 2.20462))
         / ru.starting_weight_lbs * 100
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
    -- Use user profile starting weight
    WHEN ef.end_weight->>'value' IS NOT NULL
      AND ru.starting_weight_lbs IS NOT NULL
      AND ef.duration_weeks IS NOT NULL
      AND ef.duration_weeks > 0
      AND ef.end_weight->>'unit' = 'lbs'
    THEN (ru.starting_weight_lbs - (ef.end_weight->>'value')::numeric)
         / (ef.duration_weeks / 4.33)
    WHEN ef.end_weight->>'value' IS NOT NULL
      AND ru.starting_weight_lbs IS NOT NULL
      AND ef.duration_weeks IS NOT NULL
      AND ef.duration_weeks > 0
      AND ef.end_weight->>'unit' = 'kg'
    THEN (ru.starting_weight_lbs - ((ef.end_weight->>'value')::numeric * 2.20462))
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
    -- Use user profile starting weight
    WHEN ef.end_weight->>'value' IS NOT NULL
      AND ru.starting_weight_lbs IS NOT NULL
      AND ef.duration_weeks IS NOT NULL
      AND ef.duration_weeks > 0
      AND ru.starting_weight_lbs > 0
      AND ef.end_weight->>'unit' = 'lbs'
    THEN ((ru.starting_weight_lbs - (ef.end_weight->>'value')::numeric)
          / ru.starting_weight_lbs * 100)
         / (ef.duration_weeks / 4.33)
    WHEN ef.end_weight->>'value' IS NOT NULL
      AND ru.starting_weight_lbs IS NOT NULL
      AND ef.duration_weeks IS NOT NULL
      AND ef.duration_weeks > 0
      AND ru.starting_weight_lbs > 0
      AND ef.end_weight->>'unit' = 'kg'
    THEN ((ru.starting_weight_lbs - ((ef.end_weight->>'value')::numeric * 2.20462))
          / ru.starting_weight_lbs * 100)
         / (ef.duration_weeks / 4.33)
    ELSE NULL
  END AS weight_loss_speed_percent_per_month,

  -- Beginning weight in lbs (prefer post data, fall back to user profile)
  COALESCE(
    CASE
      WHEN ef.beginning_weight->>'unit' = 'lbs'
      THEN (ef.beginning_weight->>'value')::numeric
      WHEN ef.beginning_weight->>'unit' = 'kg'
      THEN (ef.beginning_weight->>'value')::numeric * 2.20462
      ELSE NULL
    END,
    ru.starting_weight_lbs
  ) AS beginning_weight_lbs,

  -- End weight in lbs (prefer post data, fall back to user current weight)
  COALESCE(
    CASE
      WHEN ef.end_weight->>'unit' = 'lbs'
      THEN (ef.end_weight->>'value')::numeric
      WHEN ef.end_weight->>'unit' = 'kg'
      THEN (ef.end_weight->>'value')::numeric * 2.20462
      ELSE NULL
    END,
    ru.current_weight_lbs
  ) AS end_weight_lbs,

  -- Sentiment change
  CASE
    WHEN ef.sentiment_pre IS NOT NULL AND ef.sentiment_post IS NOT NULL
    THEN ef.sentiment_post - ef.sentiment_pre
    ELSE NULL
  END AS sentiment_change,

  -- Age bucket for demographic analysis
  CASE
    WHEN COALESCE(ef.age, ru.age) < 25 THEN '18-24'
    WHEN COALESCE(ef.age, ru.age) < 35 THEN '25-34'
    WHEN COALESCE(ef.age, ru.age) < 45 THEN '35-44'
    WHEN COALESCE(ef.age, ru.age) < 55 THEN '45-54'
    WHEN COALESCE(ef.age, ru.age) < 65 THEN '55-64'
    WHEN COALESCE(ef.age, ru.age) >= 65 THEN '65+'
    ELSE NULL
  END AS age_bucket,

  -- Top side effects (extract from JSONB array for convenience)
  (
    SELECT STRING_AGG(effect->>'name', ', ')
    FROM (
      SELECT jsonb_array_elements(ef.side_effects) AS effect
      ORDER BY (effect->>'severity')::int DESC NULLS LAST
      LIMIT 3
    ) top_effects
  ) AS top_side_effects

FROM extracted_features ef
LEFT JOIN reddit_posts rp ON ef.post_id = rp.post_id
LEFT JOIN reddit_comments rc ON ef.comment_id = rc.comment_id
LEFT JOIN reddit_users ru ON COALESCE(rp.author, rc.author) = ru.username
WHERE ef.post_id IS NOT NULL
ORDER BY ef.post_id, ef.processed_at DESC;

-- Create indexes for performance
CREATE INDEX idx_mv_experiences_post_id ON mv_experiences_denormalized(post_id);
CREATE INDEX idx_mv_experiences_subreddit ON mv_experiences_denormalized(subreddit);
CREATE INDEX idx_mv_experiences_author ON mv_experiences_denormalized(author);
CREATE INDEX idx_mv_experiences_primary_drug ON mv_experiences_denormalized(primary_drug);
CREATE INDEX idx_mv_experiences_created_at ON mv_experiences_denormalized(created_at DESC);
