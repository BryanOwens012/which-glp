-- Migration: Standardize drug names in extracted_features
-- This ensures consistent naming across the database

-- Metformin: Metformin → metformin
UPDATE extracted_features
SET primary_drug = 'metformin'
WHERE primary_drug = 'Metformin';

-- Tirzepatide: Tirzepatide → tirzepatide
UPDATE extracted_features
SET primary_drug = 'tirzepatide'
WHERE primary_drug IN ('Tirzepatide');

-- Semaglutide: Semaglutide → semaglutide
UPDATE extracted_features
SET primary_drug = 'semaglutide'
WHERE primary_drug = 'Semaglutide';

-- Liraglutide: Liraglutide → liraglutide
UPDATE extracted_features
SET primary_drug = 'liraglutide'
WHERE primary_drug = 'Liraglutide';

-- Retatrutide: Retatrutide → retatrutide
UPDATE extracted_features
SET primary_drug = 'retatrutide'
WHERE primary_drug = 'Retatrutide';

-- Testosterone: TRT, Testosterone, Testosterone Replacement Therapy → testosterone
UPDATE extracted_features
SET primary_drug = 'testosterone'
WHERE primary_drug IN ('TRT', 'Testosterone', 'Testosterone Replacement Therapy');

-- Trenbolone: tren → trenbolone
UPDATE extracted_features
SET primary_drug = 'trenbolone'
WHERE primary_drug = 'tren';

-- Compounded Semaglutide: compounded semaglutide → Compounded Semaglutide
UPDATE extracted_features
SET primary_drug = 'Compounded Semaglutide'
WHERE primary_drug = 'compounded semaglutide';

-- Compounded Tirzepatide: Compound Tirzepatide, compounded tirzepatide → Compounded Tirzepatide
UPDATE extracted_features
SET primary_drug = 'Compounded Tirzepatide'
WHERE primary_drug IN ('Compound Tirzepatide', 'compounded tirzepatide');

-- Refresh materialized view (non-concurrent - view doesn't have unique index)
REFRESH MATERIALIZED VIEW mv_experiences_denormalized;
