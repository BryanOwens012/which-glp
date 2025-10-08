-- Migration 016: Rename weight columns to use consistent naming
-- Change starting_weight_lbs -> start_weight_lbs
-- Change current_weight_lbs -> end_weight_lbs

ALTER TABLE reddit_users
RENAME COLUMN starting_weight_lbs TO start_weight_lbs;

ALTER TABLE reddit_users
RENAME COLUMN current_weight_lbs TO end_weight_lbs;

-- Add comments for clarity
COMMENT ON COLUMN reddit_users.start_weight_lbs IS 'Starting weight before GLP-1 medication in pounds';
COMMENT ON COLUMN reddit_users.end_weight_lbs IS 'Most recent/current weight mentioned in pounds';
