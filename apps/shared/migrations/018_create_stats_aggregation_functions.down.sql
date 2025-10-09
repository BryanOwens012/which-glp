-- Rollback migration 018: Drop stats aggregation functions

DROP FUNCTION IF EXISTS get_drug_stats();
DROP FUNCTION IF EXISTS get_demographics_stats();
DROP FUNCTION IF EXISTS get_location_stats();
DROP FUNCTION IF EXISTS get_platform_stats();
