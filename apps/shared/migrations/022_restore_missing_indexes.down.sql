-- Migration 022 Rollback: Remove restored indexes
--
-- This reverts the changes made in 022_restore_missing_indexes.up.sql
-- WARNING: After rolling back, stats queries will be slower and author filtering will be inefficient

-- Drop author index
DROP INDEX IF EXISTS idx_mv_experiences_author;

-- Drop stats optimization indexes
DROP INDEX IF EXISTS idx_mv_experiences_plateau_mentioned;
DROP INDEX IF EXISTS idx_mv_experiences_rebound_weight_gain;
DROP INDEX IF EXISTS idx_mv_experiences_has_insurance;
DROP INDEX IF EXISTS idx_mv_experiences_drug_source;
DROP INDEX IF EXISTS idx_mv_experiences_drug_covering;
DROP INDEX IF EXISTS idx_mv_experiences_age;
DROP INDEX IF EXISTS idx_mv_experiences_sex;
DROP INDEX IF EXISTS idx_mv_experiences_beginning_weight;
DROP INDEX IF EXISTS idx_mv_experiences_location_covering;
