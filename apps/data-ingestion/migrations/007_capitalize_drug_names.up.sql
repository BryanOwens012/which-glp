-- Migration: Capitalize all drug names to Title Case in extracted_features
-- This ensures all drug names use consistent Title Case formatting

-- Semaglutide: semaglutide → Semaglutide
UPDATE extracted_features
SET primary_drug = 'Semaglutide'
WHERE primary_drug = 'semaglutide';

-- Tirzepatide: tirzepatide → Tirzepatide
UPDATE extracted_features
SET primary_drug = 'Tirzepatide'
WHERE primary_drug = 'tirzepatide';

-- Liraglutide: liraglutide → Liraglutide
UPDATE extracted_features
SET primary_drug = 'Liraglutide'
WHERE primary_drug = 'liraglutide';

-- Dulaglutide: dulaglutide → Dulaglutide
UPDATE extracted_features
SET primary_drug = 'Dulaglutide'
WHERE primary_drug = 'dulaglutide';

-- Retatrutide: retatrutide → Retatrutide
UPDATE extracted_features
SET primary_drug = 'Retatrutide'
WHERE primary_drug = 'retatrutide';

-- Metformin: metformin → Metformin
UPDATE extracted_features
SET primary_drug = 'Metformin'
WHERE primary_drug = 'metformin';

-- Testosterone: testosterone → Testosterone
UPDATE extracted_features
SET primary_drug = 'Testosterone'
WHERE primary_drug = 'testosterone';

-- Trenbolone: trenbolone → Trenbolone
UPDATE extracted_features
SET primary_drug = 'Trenbolone'
WHERE primary_drug = 'trenbolone';

-- Inositol: inositol → Inositol
UPDATE extracted_features
SET primary_drug = 'Inositol'
WHERE primary_drug = 'inositol';

-- Spironolactone: spironolactone → Spironolactone
UPDATE extracted_features
SET primary_drug = 'Spironolactone'
WHERE primary_drug = 'spironolactone';

-- Mirtazapine: mirtazapine → Mirtazapine
UPDATE extracted_features
SET primary_drug = 'Mirtazapine'
WHERE primary_drug = 'mirtazapine';

-- Levothyroxine: levothyroxine → Levothyroxine
UPDATE extracted_features
SET primary_drug = 'Levothyroxine'
WHERE primary_drug = 'levothyroxine';

-- Phentermine: phentermine → Phentermine
UPDATE extracted_features
SET primary_drug = 'Phentermine'
WHERE primary_drug = 'phentermine';

-- Refresh materialized view (non-concurrent - view doesn't have unique index)
REFRESH MATERIALIZED VIEW mv_experiences_denormalized;
