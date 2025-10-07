-- Migration 003 Rollback: Remove comprehensive feature extraction columns

-- Drop indexes
DROP INDEX IF EXISTS idx_extracted_features_drug_source;
DROP INDEX IF EXISTS idx_extracted_features_plateau;
DROP INDEX IF EXISTS idx_extracted_features_side_effects;
DROP INDEX IF EXISTS idx_extracted_features_labs;
DROP INDEX IF EXISTS idx_extracted_features_nsv;

-- Remove added columns
ALTER TABLE extracted_features
  DROP COLUMN IF EXISTS dosage_progression,
  DROP COLUMN IF EXISTS exercise_frequency,
  DROP COLUMN IF EXISTS dietary_changes,
  DROP COLUMN IF EXISTS previous_weight_loss_attempts,
  DROP COLUMN IF EXISTS drug_source,
  DROP COLUMN IF EXISTS switching_drugs,
  DROP COLUMN IF EXISTS side_effect_timing,
  DROP COLUMN IF EXISTS side_effect_resolution,
  DROP COLUMN IF EXISTS food_intolerances,
  DROP COLUMN IF EXISTS plateau_mentioned,
  DROP COLUMN IF EXISTS rebound_weight_gain,
  DROP COLUMN IF EXISTS labs_improvement,
  DROP COLUMN IF EXISTS medication_reduction,
  DROP COLUMN IF EXISTS nsv_mentioned,
  DROP COLUMN IF EXISTS support_system,
  DROP COLUMN IF EXISTS pharmacy_access_issues,
  DROP COLUMN IF EXISTS mental_health_impact;

-- Restore side_effects as TEXT[] (reverting from JSONB)
ALTER TABLE extracted_features
  DROP COLUMN IF EXISTS side_effects;

ALTER TABLE extracted_features
  ADD COLUMN side_effects TEXT[];
