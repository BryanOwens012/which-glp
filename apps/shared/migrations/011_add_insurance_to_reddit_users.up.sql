-- Migration 011: Add insurance fields to reddit_users table

ALTER TABLE reddit_users
ADD COLUMN IF NOT EXISTS has_insurance BOOLEAN,
ADD COLUMN IF NOT EXISTS insurance_provider TEXT;

-- Comments
COMMENT ON COLUMN reddit_users.has_insurance IS 'Whether user has insurance coverage for GLP-1 medication';
COMMENT ON COLUMN reddit_users.insurance_provider IS 'Insurance provider name (Blue Cross, Aetna, etc.)';
