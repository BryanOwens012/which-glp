-- Migration: Add extraction status tracking to reddit_posts
-- Created: 2025-10-08
-- Description: Add columns to track whether posts have been processed, skipped, or are pending extraction

-- Create enum type for extraction status
CREATE TYPE extraction_status_type AS ENUM ('pending', 'processed', 'skipped');

-- Add columns to reddit_posts table
ALTER TABLE reddit_posts
    ADD COLUMN extraction_status extraction_status_type NOT NULL DEFAULT 'pending',
    ADD COLUMN extraction_skip_reason TEXT,
    ADD COLUMN extraction_attempted_at TIMESTAMPTZ;

-- Add partial index for efficient querying of unprocessed posts
-- This only indexes 'pending' rows, making it extremely fast and small
CREATE INDEX idx_posts_extraction_status ON reddit_posts(extraction_status, created_at DESC)
    WHERE extraction_status = 'pending';

-- Add partial index for skipped posts (useful for debugging/analysis)
CREATE INDEX idx_posts_skipped_reason ON reddit_posts(extraction_skip_reason)
    WHERE extraction_status = 'skipped';

-- Add comments for documentation
COMMENT ON COLUMN reddit_posts.extraction_status IS 'Status of extraction: pending (not yet attempted), processed (successfully extracted), skipped (filtered out)';
COMMENT ON COLUMN reddit_posts.extraction_skip_reason IS 'Reason for skipping (e.g., "keyword_filter: not drug-related", "minimum_field_filter: missing weight")';
COMMENT ON COLUMN reddit_posts.extraction_attempted_at IS 'Timestamp of last extraction attempt (successful or skipped)';
