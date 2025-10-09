-- Migration: Add user extraction status tracking to extracted_features table
-- Created: 2025-10-08
-- Description: Adds status tracking for user demographics extraction (analogous to post extraction status)

-- Create enum type for user extraction status
-- States: pending (not yet attempted), processed (successfully extracted),
--         skipped (filtered out - e.g., no content found), failed (error during extraction)
CREATE TYPE user_extraction_status_type AS ENUM ('pending', 'processed', 'skipped', 'failed');

-- Add status tracking columns to extracted_features table
ALTER TABLE extracted_features
    ADD COLUMN user_extraction_status user_extraction_status_type NOT NULL DEFAULT 'pending',
    ADD COLUMN user_extraction_log_message TEXT,
    ADD COLUMN user_extraction_attempted_at TIMESTAMPTZ;

-- Create partial index for pending user extractions (most common query)
-- Only index rows that need processing (pending status)
CREATE INDEX idx_extracted_features_user_extraction_status
    ON extracted_features(user_extraction_status, processed_at DESC)
    WHERE user_extraction_status = 'pending';

-- Create index on log messages for debugging failed/skipped extractions
CREATE INDEX idx_extracted_features_user_extraction_log
    ON extracted_features(user_extraction_log_message)
    WHERE user_extraction_log_message IS NOT NULL;

-- Add column comments
COMMENT ON COLUMN extracted_features.user_extraction_status IS
    'Status of user demographics extraction: pending (not yet attempted), processed (successfully extracted), skipped (filtered out), failed (error during extraction)';

COMMENT ON COLUMN extracted_features.user_extraction_log_message IS
    'Log message for user extraction: skip reason (if skipped), error message (if failed), or NULL (if processed)';

COMMENT ON COLUMN extracted_features.user_extraction_attempted_at IS
    'Timestamp when user demographics extraction was last attempted';
