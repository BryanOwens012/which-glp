-- Rollback: Remove 'out-of-pocket' from valid drug_source values
-- WARNING: This will fail if any records have drug_source = 'out-of-pocket'

-- Drop the current CHECK constraint
ALTER TABLE extracted_features
  DROP CONSTRAINT IF EXISTS extracted_features_drug_source_check;

-- Restore the original CHECK constraint (without 'out-of-pocket')
ALTER TABLE extracted_features
  ADD CONSTRAINT extracted_features_drug_source_check
  CHECK (drug_source IN ('brand', 'compounded', 'other'));

-- Restore the original column comment
COMMENT ON COLUMN extracted_features.drug_source IS 'Brand name, compounded, or other (foreign-sourced)';
