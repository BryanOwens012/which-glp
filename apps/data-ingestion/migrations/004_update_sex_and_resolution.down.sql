-- Migration 004 Rollback: Revert sex enum and side_effect_resolution type

-- Revert sex constraint to original values
ALTER TABLE extracted_features
  DROP CONSTRAINT IF EXISTS extracted_features_sex_check;

ALTER TABLE extracted_features
  ADD CONSTRAINT extracted_features_sex_check CHECK (sex IN ('male', 'female', 'other'));

-- Revert side_effect_resolution from NUMERIC to BOOLEAN
ALTER TABLE extracted_features
  DROP COLUMN IF EXISTS side_effect_resolution;

ALTER TABLE extracted_features
  ADD COLUMN side_effect_resolution BOOLEAN;

-- Restore original comments
COMMENT ON COLUMN extracted_features.sex IS 'Biological sex or gender if mentioned (male/female/other)';
COMMENT ON COLUMN extracted_features.side_effect_resolution IS 'Whether side effects improved over time';
