-- Rollback: Reset user extraction status back to pending
-- This reverts 029_backfill_user_extraction_status.up.sql

-- Reset extracted_features that were marked as processed back to pending
UPDATE extracted_features
SET user_extraction_status = 'pending',
    user_extraction_attempted_at = NULL
WHERE user_extraction_status = 'processed';
