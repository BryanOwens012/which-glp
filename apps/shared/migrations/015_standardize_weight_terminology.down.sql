-- Migration 015 Rollback: Revert to old column names

ALTER TABLE reddit_users
  RENAME COLUMN start_weight_lbs TO starting_weight_lbs;

ALTER TABLE reddit_users
  RENAME COLUMN end_weight_lbs TO current_weight_lbs;

-- Rebuild view with old schema (copy from migration 009)
DROP MATERIALIZED VIEW IF EXISTS mv_experiences_denormalized;

CREATE MATERIALIZED VIEW mv_experiences_denormalized AS
SELECT DISTINCT ON (post_id)
  -- (same as migration 009)
  ef.id AS feature_id,
  ef.post_id,
  ef.comment_id,
  COALESCE(rp.subreddit, rc.subreddit) AS subreddit,
  ef.processed_at,
  COALESCE(rp.title, '') AS post_title,
  COALESCE(rp.body, '') AS post_text,
  COALESCE(rc.body, '') AS comment_text,
  COALESCE(rp.author, rc.author) AS author,
  COALESCE(rp.created_at, rc.created_at) AS created_at,
  COALESCE(rp.score, rc.score, 0) AS score,
  CASE WHEN ef.post_id IS NOT NULL THEN 'post' ELSE 'comment' END AS source_type,
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
  ef.side_effects,
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
  CASE
    WHEN ef.beginning_weight->>'value' IS NOT NULL
      AND ef.end_weight->>'value' IS NOT NULL
      AND (ef.beginning_weight->>'value')::numeric > 0
    THEN ((ef.beginning_weight->>'value')::numeric - (ef.end_weight->>'value')::numeric)
         / (ef.beginning_weight->>'value')::numeric * 100
    ELSE NULL
  END AS weight_loss_percentage,
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
  CASE
    WHEN ef.beginning_weight->>'unit' = 'lbs'
    THEN (ef.beginning_weight->>'value')::numeric
    WHEN ef.beginning_weight->>'unit' = 'kg'
    THEN (ef.beginning_weight->>'value')::numeric * 2.20462
    ELSE NULL
  END AS beginning_weight_lbs,
  CASE
    WHEN ef.end_weight->>'unit' = 'lbs'
    THEN (ef.end_weight->>'value')::numeric
    WHEN ef.end_weight->>'unit' = 'kg'
    THEN (ef.end_weight->>'value')::numeric * 2.20462
    ELSE NULL
  END AS end_weight_lbs,
  CASE
    WHEN ef.sentiment_pre IS NOT NULL AND ef.sentiment_post IS NOT NULL
    THEN ef.sentiment_post - ef.sentiment_pre
    ELSE NULL
  END AS sentiment_change,
  CASE
    WHEN ef.age < 25 THEN '18-24'
    WHEN ef.age < 35 THEN '25-34'
    WHEN ef.age < 45 THEN '35-44'
    WHEN ef.age < 55 THEN '45-54'
    WHEN ef.age < 65 THEN '55-64'
    ELSE '65+'
  END AS age_bucket,
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
WHERE ef.post_id IS NOT NULL
ORDER BY post_id, ef.processed_at DESC;

CREATE INDEX idx_mv_experiences_post_id ON mv_experiences_denormalized(post_id);
CREATE INDEX idx_mv_experiences_subreddit ON mv_experiences_denormalized(subreddit);
CREATE INDEX idx_mv_experiences_author ON mv_experiences_denormalized(author);
CREATE INDEX idx_mv_experiences_primary_drug ON mv_experiences_denormalized(primary_drug);
CREATE INDEX idx_mv_experiences_created_at ON mv_experiences_denormalized(created_at DESC);
