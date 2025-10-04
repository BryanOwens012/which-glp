-- Migration 003: Add comprehensive feature extraction columns
-- Adds lifestyle, medical journey, drug sourcing, health improvements, and social factors

-- Change side_effects from TEXT[] to JSONB for structured data (name, severity, confidence)
ALTER TABLE extracted_features
  DROP COLUMN IF EXISTS side_effects;

ALTER TABLE extracted_features
  ADD COLUMN side_effects JSONB;

-- Add lifestyle and medical journey columns
ALTER TABLE extracted_features
  ADD COLUMN dosage_progression TEXT,
  ADD COLUMN exercise_frequency TEXT,
  ADD COLUMN dietary_changes TEXT,
  ADD COLUMN previous_weight_loss_attempts TEXT[];

-- Add drug sourcing and switching columns
ALTER TABLE extracted_features
  ADD COLUMN drug_source TEXT CHECK (drug_source IN ('brand', 'compounded', 'other')),
  ADD COLUMN switching_drugs TEXT;

-- Add side effect detail columns
ALTER TABLE extracted_features
  ADD COLUMN side_effect_timing TEXT,
  ADD COLUMN side_effect_resolution NUMERIC(3,2) CHECK (side_effect_resolution >= 0 AND side_effect_resolution <= 1),
  ADD COLUMN food_intolerances TEXT[];

-- Add weight loss journey detail columns
ALTER TABLE extracted_features
  ADD COLUMN plateau_mentioned BOOLEAN,
  ADD COLUMN rebound_weight_gain BOOLEAN;

-- Add health improvement columns
ALTER TABLE extracted_features
  ADD COLUMN labs_improvement TEXT[],
  ADD COLUMN medication_reduction TEXT[],
  ADD COLUMN nsv_mentioned TEXT[];

-- Add social and practical factor columns
ALTER TABLE extracted_features
  ADD COLUMN support_system TEXT,
  ADD COLUMN pharmacy_access_issues BOOLEAN,
  ADD COLUMN mental_health_impact TEXT;

-- Add comments for documentation
COMMENT ON COLUMN extracted_features.side_effects IS 'JSON array: [{"name": "nausea", "severity": "moderate", "confidence": "high"}, ...]';
COMMENT ON COLUMN extracted_features.dosage_progression IS 'How dose changed over time (e.g., "started 2.5mg, now 7.5mg")';
COMMENT ON COLUMN extracted_features.exercise_frequency IS 'Exercise frequency mentioned (e.g., "3x/week", "daily", "none")';
COMMENT ON COLUMN extracted_features.dietary_changes IS 'Dietary changes mentioned (e.g., "low carb", "calorie counting")';
COMMENT ON COLUMN extracted_features.previous_weight_loss_attempts IS 'Prior weight loss methods tried';
COMMENT ON COLUMN extracted_features.drug_source IS 'Brand name, compounded, or other (foreign-sourced)';
COMMENT ON COLUMN extracted_features.switching_drugs IS 'If they switched GLP-1s and reasons';
COMMENT ON COLUMN extracted_features.side_effect_timing IS 'When side effects occurred (e.g., "first 2 weeks")';
COMMENT ON COLUMN extracted_features.side_effect_resolution IS 'Degree of side effect improvement (0-1). 0=completely resolved, 0.5=somewhat better, 1=no improvement/worse';
COMMENT ON COLUMN extracted_features.food_intolerances IS 'Specific foods they can no longer tolerate';
COMMENT ON COLUMN extracted_features.plateau_mentioned IS 'Whether they mention hitting a weight plateau';
COMMENT ON COLUMN extracted_features.rebound_weight_gain IS 'If they mention regaining weight after stopping';
COMMENT ON COLUMN extracted_features.labs_improvement IS 'Lab improvements mentioned (A1C, cholesterol, etc.)';
COMMENT ON COLUMN extracted_features.medication_reduction IS 'Medications they were able to reduce/stop';
COMMENT ON COLUMN extracted_features.nsv_mentioned IS 'Non-scale victories (energy, clothes fit, mobility)';
COMMENT ON COLUMN extracted_features.support_system IS 'Mentions of support or lack thereof';
COMMENT ON COLUMN extracted_features.pharmacy_access_issues IS 'Difficulty finding medication in stock';
COMMENT ON COLUMN extracted_features.mental_health_impact IS 'Mental health changes mentioned';

-- Create indexes for commonly queried fields
CREATE INDEX idx_extracted_features_drug_source ON extracted_features(drug_source) WHERE drug_source IS NOT NULL;
CREATE INDEX idx_extracted_features_plateau ON extracted_features(plateau_mentioned) WHERE plateau_mentioned IS NOT NULL;
CREATE INDEX idx_extracted_features_side_effects ON extracted_features USING GIN(side_effects);
CREATE INDEX idx_extracted_features_labs ON extracted_features USING GIN(labs_improvement);
CREATE INDEX idx_extracted_features_nsv ON extracted_features USING GIN(nsv_mentioned);
