-- Migration 015: Standardize weight column names across the entire schema
-- Standardize to: start_weight_lbs, end_weight_lbs (not beginning/current)

-- 1. Update reddit_users table
ALTER TABLE reddit_users
  RENAME COLUMN starting_weight_lbs TO start_weight_lbs;

ALTER TABLE reddit_users
  RENAME COLUMN current_weight_lbs TO end_weight_lbs;

-- 2. Rebuild materialized view with standardized terminology
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

  -- Weight data (keep original JSONB for compatibility, but also extract to standardized columns)
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

  -- STANDARDIZED COLUMNS: start_weight_lbs and end_weight_lbs
  -- Start weight in lbs (prefer post data, fall back to user profile)
  COALESCE(
    CASE
      WHEN ef.beginning_weight->>'unit' = 'lbs'
      THEN (ef.beginning_weight->>'value')::numeric
      WHEN ef.beginning_weight->>'unit' = 'kg'
      THEN (ef.beginning_weight->>'value')::numeric * 2.20462
      ELSE NULL
    END,
    ru.start_weight_lbs
  ) AS start_weight_lbs,

  -- End weight in lbs (prefer post data, fall back to user profile)
  COALESCE(
    CASE
      WHEN ef.end_weight->>'unit' = 'lbs'
      THEN (ef.end_weight->>'value')::numeric
      WHEN ef.end_weight->>'unit' = 'kg'
      THEN (ef.end_weight->>'value')::numeric * 2.20462
      ELSE NULL
    END,
    ru.end_weight_lbs
  ) AS end_weight_lbs,

  -- Weight loss in lbs (calculated from standardized columns)
  CASE
    WHEN COALESCE(
      CASE
        WHEN ef.beginning_weight->>'unit' = 'lbs'
        THEN (ef.beginning_weight->>'value')::numeric
        WHEN ef.beginning_weight->>'unit' = 'kg'
        THEN (ef.beginning_weight->>'value')::numeric * 2.20462
        ELSE NULL
      END,
      ru.start_weight_lbs
    ) IS NOT NULL
    AND COALESCE(
      CASE
        WHEN ef.end_weight->>'unit' = 'lbs'
        THEN (ef.end_weight->>'value')::numeric
        WHEN ef.end_weight->>'unit' = 'kg'
        THEN (ef.end_weight->>'value')::numeric * 2.20462
        ELSE NULL
      END,
      ru.end_weight_lbs
    ) IS NOT NULL
    THEN COALESCE(
      CASE
        WHEN ef.beginning_weight->>'unit' = 'lbs'
        THEN (ef.beginning_weight->>'value')::numeric
        WHEN ef.beginning_weight->>'unit' = 'kg'
        THEN (ef.beginning_weight->>'value')::numeric * 2.20462
        ELSE NULL
      END,
      ru.start_weight_lbs
    ) - COALESCE(
      CASE
        WHEN ef.end_weight->>'unit' = 'lbs'
        THEN (ef.end_weight->>'value')::numeric
        WHEN ef.end_weight->>'unit' = 'kg'
        THEN (ef.end_weight->>'value')::numeric * 2.20462
        ELSE NULL
      END,
      ru.end_weight_lbs
    )
    ELSE NULL
  END AS weight_loss_lbs,

  -- Weight loss percentage
  CASE
    WHEN COALESCE(
      CASE
        WHEN ef.beginning_weight->>'unit' = 'lbs'
        THEN (ef.beginning_weight->>'value')::numeric
        WHEN ef.beginning_weight->>'unit' = 'kg'
        THEN (ef.beginning_weight->>'value')::numeric * 2.20462
        ELSE NULL
      END,
      ru.start_weight_lbs
    ) > 0
    AND COALESCE(
      CASE
        WHEN ef.end_weight->>'unit' = 'lbs'
        THEN (ef.end_weight->>'value')::numeric
        WHEN ef.end_weight->>'unit' = 'kg'
        THEN (ef.end_weight->>'value')::numeric * 2.20462
        ELSE NULL
      END,
      ru.end_weight_lbs
    ) IS NOT NULL
    THEN (COALESCE(
      CASE
        WHEN ef.beginning_weight->>'unit' = 'lbs'
        THEN (ef.beginning_weight->>'value')::numeric
        WHEN ef.beginning_weight->>'unit' = 'kg'
        THEN (ef.beginning_weight->>'value')::numeric * 2.20462
        ELSE NULL
      END,
      ru.start_weight_lbs
    ) - COALESCE(
      CASE
        WHEN ef.end_weight->>'unit' = 'lbs'
        THEN (ef.end_weight->>'value')::numeric
        WHEN ef.end_weight->>'unit' = 'kg'
        THEN (ef.end_weight->>'value')::numeric * 2.20462
        ELSE NULL
      END,
      ru.end_weight_lbs
    )) / COALESCE(
      CASE
        WHEN ef.beginning_weight->>'unit' = 'lbs'
        THEN (ef.beginning_weight->>'value')::numeric
        WHEN ef.beginning_weight->>'unit' = 'kg'
        THEN (ef.beginning_weight->>'value')::numeric * 2.20462
        ELSE NULL
      END,
      ru.start_weight_lbs
    ) * 100
    ELSE NULL
  END AS weight_loss_percentage,

  -- Weight loss speed in lbs per month
  CASE
    WHEN ef.duration_weeks > 0
    AND COALESCE(
      CASE
        WHEN ef.beginning_weight->>'unit' = 'lbs'
        THEN (ef.beginning_weight->>'value')::numeric
        WHEN ef.beginning_weight->>'unit' = 'kg'
        THEN (ef.beginning_weight->>'value')::numeric * 2.20462
        ELSE NULL
      END,
      ru.start_weight_lbs
    ) IS NOT NULL
    AND COALESCE(
      CASE
        WHEN ef.end_weight->>'unit' = 'lbs'
        THEN (ef.end_weight->>'value')::numeric
        WHEN ef.end_weight->>'unit' = 'kg'
        THEN (ef.end_weight->>'value')::numeric * 2.20462
        ELSE NULL
      END,
      ru.end_weight_lbs
    ) IS NOT NULL
    THEN (COALESCE(
      CASE
        WHEN ef.beginning_weight->>'unit' = 'lbs'
        THEN (ef.beginning_weight->>'value')::numeric
        WHEN ef.beginning_weight->>'unit' = 'kg'
        THEN (ef.beginning_weight->>'value')::numeric * 2.20462
        ELSE NULL
      END,
      ru.start_weight_lbs
    ) - COALESCE(
      CASE
        WHEN ef.end_weight->>'unit' = 'lbs'
        THEN (ef.end_weight->>'value')::numeric
        WHEN ef.end_weight->>'unit' = 'kg'
        THEN (ef.end_weight->>'value')::numeric * 2.20462
        ELSE NULL
      END,
      ru.end_weight_lbs
    )) / (ef.duration_weeks / 4.33)
    ELSE NULL
  END AS weight_loss_speed_lbs_per_month,

  -- Weight loss speed in percentage per month
  CASE
    WHEN ef.duration_weeks > 0
    AND COALESCE(
      CASE
        WHEN ef.beginning_weight->>'unit' = 'lbs'
        THEN (ef.beginning_weight->>'value')::numeric
        WHEN ef.beginning_weight->>'unit' = 'kg'
        THEN (ef.beginning_weight->>'value')::numeric * 2.20462
        ELSE NULL
      END,
      ru.start_weight_lbs
    ) > 0
    AND COALESCE(
      CASE
        WHEN ef.end_weight->>'unit' = 'lbs'
        THEN (ef.end_weight->>'value')::numeric
        WHEN ef.end_weight->>'unit' = 'kg'
        THEN (ef.end_weight->>'value')::numeric * 2.20462
        ELSE NULL
      END,
      ru.end_weight_lbs
    ) IS NOT NULL
    THEN ((COALESCE(
      CASE
        WHEN ef.beginning_weight->>'unit' = 'lbs'
        THEN (ef.beginning_weight->>'value')::numeric
        WHEN ef.beginning_weight->>'unit' = 'kg'
        THEN (ef.beginning_weight->>'value')::numeric * 2.20462
        ELSE NULL
      END,
      ru.start_weight_lbs
    ) - COALESCE(
      CASE
        WHEN ef.end_weight->>'unit' = 'lbs'
        THEN (ef.end_weight->>'value')::numeric
        WHEN ef.end_weight->>'unit' = 'kg'
        THEN (ef.end_weight->>'value')::numeric * 2.20462
        ELSE NULL
      END,
      ru.end_weight_lbs
    )) / COALESCE(
      CASE
        WHEN ef.beginning_weight->>'unit' = 'lbs'
        THEN (ef.beginning_weight->>'value')::numeric
        WHEN ef.beginning_weight->>'unit' = 'kg'
        THEN (ef.beginning_weight->>'value')::numeric * 2.20462
        ELSE NULL
      END,
      ru.start_weight_lbs
    ) * 100) / (ef.duration_weeks / 4.33)
    ELSE NULL
  END AS weight_loss_speed_percent_per_month,

  -- Legacy column names for backwards compatibility (alias to standardized columns)
  COALESCE(
    CASE
      WHEN ef.beginning_weight->>'unit' = 'lbs'
      THEN (ef.beginning_weight->>'value')::numeric
      WHEN ef.beginning_weight->>'unit' = 'kg'
      THEN (ef.beginning_weight->>'value')::numeric * 2.20462
      ELSE NULL
    END,
    ru.start_weight_lbs
  ) AS beginning_weight_lbs,

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
    SELECT STRING_AGG(se_elem->>'name', ', ')
    FROM (
      SELECT se_elem
      FROM jsonb_array_elements(ef.side_effects) AS se_elem
      ORDER BY
        CASE se_elem->>'severity'
          WHEN 'severe' THEN 3
          WHEN 'moderate' THEN 2
          WHEN 'mild' THEN 1
          ELSE 0
        END DESC
      LIMIT 3
    ) top_se
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
