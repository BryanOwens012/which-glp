-- Migration 016 DOWN: Revert weight column renames

ALTER TABLE reddit_users
RENAME COLUMN start_weight_lbs TO starting_weight_lbs;

ALTER TABLE reddit_users
RENAME COLUMN end_weight_lbs TO current_weight_lbs;

-- Restore original comments
COMMENT ON COLUMN reddit_users.starting_weight_lbs IS 'Starting weight before GLP-1 medication';
COMMENT ON COLUMN reddit_users.current_weight_lbs IS 'Most recent/current weight mentioned';
