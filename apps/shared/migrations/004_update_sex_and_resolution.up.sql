-- Migration 004: Update sex enum and side_effect_resolution type
-- Adds transgender options (ftm/mtf) to sex enum and changes side_effect_resolution to numeric

-- Update sex constraint to include transgender options
ALTER TABLE extracted_features
  DROP CONSTRAINT IF EXISTS extracted_features_sex_check;

ALTER TABLE extracted_features
  ADD CONSTRAINT extracted_features_sex_check CHECK (sex IN ('male', 'female', 'ftm', 'mtf', 'other'));

-- Update side_effect_resolution from BOOLEAN to NUMERIC(3,2)
-- First drop the column and recreate it (safest approach for type change)
ALTER TABLE extracted_features
  DROP COLUMN IF EXISTS side_effect_resolution;

ALTER TABLE extracted_features
  ADD COLUMN side_effect_resolution NUMERIC(3,2) CHECK (side_effect_resolution >= 0 AND side_effect_resolution <= 1);

-- Update comments
COMMENT ON COLUMN extracted_features.sex IS 'Sex/gender identity if mentioned (male/female/ftm/mtf/other). ftm=female-to-male trans, mtf=male-to-female trans';
COMMENT ON COLUMN extracted_features.side_effect_resolution IS 'Degree of side effect improvement (0-1). 0=completely resolved, 0.5=somewhat better, 1=no improvement/worse';
