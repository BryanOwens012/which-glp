-- Rollback: Drop denormalized materialized view

DROP MATERIALIZED VIEW IF EXISTS mv_experiences_denormalized CASCADE;
