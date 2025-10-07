-- Migration 011 Rollback: Remove insurance fields from reddit_users

ALTER TABLE reddit_users
DROP COLUMN IF EXISTS has_insurance,
DROP COLUMN IF EXISTS insurance_provider;
