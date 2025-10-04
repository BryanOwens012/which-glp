-- Migration: Add 'out-of-pocket' as valid drug_source value
-- This migration updates the CHECK constraint on drug_source to include 'out-of-pocket'
-- without destroying existing records.

-- Drop the existing CHECK constraint
ALTER TABLE extracted_features
  DROP CONSTRAINT IF EXISTS extracted_features_drug_source_check;

-- Add the updated CHECK constraint with 'out-of-pocket' included
ALTER TABLE extracted_features
  ADD CONSTRAINT extracted_features_drug_source_check
  CHECK (drug_source IN ('brand', 'compounded', 'out-of-pocket', 'other'));

-- Update the column comment to reflect the new valid values
COMMENT ON COLUMN extracted_features.drug_source IS 'Brand name, compounded, out-of-pocket, or other (foreign-sourced)';
