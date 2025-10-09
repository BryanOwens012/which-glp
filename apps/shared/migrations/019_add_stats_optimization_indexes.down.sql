-- Rollback migration 019: Drop stats optimization indexes

DROP INDEX IF EXISTS idx_mv_experiences_plateau_mentioned;
DROP INDEX IF EXISTS idx_mv_experiences_rebound_weight_gain;
DROP INDEX IF EXISTS idx_mv_experiences_has_insurance;
DROP INDEX IF EXISTS idx_mv_experiences_drug_source;
DROP INDEX IF EXISTS idx_mv_experiences_drug_covering;
DROP INDEX IF EXISTS idx_mv_experiences_age;
DROP INDEX IF EXISTS idx_mv_experiences_sex;
DROP INDEX IF EXISTS idx_mv_experiences_beginning_weight;
DROP INDEX IF EXISTS idx_mv_experiences_location_covering;
