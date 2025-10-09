-- Rollback: Remove user extraction status tracking from extracted_features table
-- This reverts 027_add_user_extraction_status_flags.up.sql

-- Drop indexes
DROP INDEX IF EXISTS idx_extracted_features_user_extraction_status;
DROP INDEX IF EXISTS idx_extracted_features_user_extraction_log;

-- Drop columns
ALTER TABLE extracted_features
    DROP COLUMN IF EXISTS user_extraction_status,
    DROP COLUMN IF EXISTS user_extraction_log_message,
    DROP COLUMN IF EXISTS user_extraction_attempted_at;

-- Drop enum type
DROP TYPE IF EXISTS user_extraction_status_type;
