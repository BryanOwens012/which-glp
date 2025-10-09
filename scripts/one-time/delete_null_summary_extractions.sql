-- One-time script to delete extracted_features where summary is null or empty string
-- This allows posts to be re-ingested with proper summary extraction
--
-- Run date: 2025-10-09
-- Reason: Early extractions may have null or empty summaries due to extraction bugs.
--         The prompt now requires summary to NEVER be null or empty, so we delete these
--         invalid extractions to allow re-processing.

-- First, check how many rows will be affected
SELECT
    COUNT(*) FILTER (WHERE summary IS NULL) as null_summaries,
    COUNT(*) FILTER (WHERE summary = '') as empty_summaries,
    COUNT(*) as total_to_delete
FROM extracted_features
WHERE summary IS NULL OR summary = '';

-- Delete extracted_features where summary is null or empty string
DELETE FROM extracted_features
WHERE summary IS NULL OR summary = '';

-- Verify deletion
SELECT
    COUNT(*) FILTER (WHERE summary IS NULL) as remaining_null,
    COUNT(*) FILTER (WHERE summary = '') as remaining_empty,
    COUNT(*) as total_remaining
FROM extracted_features
WHERE summary IS NULL OR summary = '';
