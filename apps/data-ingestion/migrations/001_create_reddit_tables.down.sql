-- Rollback Migration: Drop Reddit Posts and Comments Tables
-- Created: 2025-09-30
-- Description: Drops reddit_posts and reddit_comments tables and all associated indexes

-- Drop comments table first (due to foreign key constraint)
DROP TABLE IF EXISTS reddit_comments CASCADE;

-- Drop posts table
DROP TABLE IF EXISTS reddit_posts CASCADE;

-- Note: Indexes and constraints are automatically dropped with CASCADE
