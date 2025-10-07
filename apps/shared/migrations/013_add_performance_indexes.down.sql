-- Migration 013 Rollback: Remove performance indexes

-- reddit_posts indexes
DROP INDEX IF EXISTS idx_reddit_posts_post_id;
DROP INDEX IF EXISTS idx_reddit_posts_subreddit;
DROP INDEX IF EXISTS idx_reddit_posts_subreddit_id;
DROP INDEX IF EXISTS idx_reddit_posts_author;

-- mv_experiences_denormalized indexes
DROP INDEX IF EXISTS idx_mv_experiences_post_id;
DROP INDEX IF EXISTS idx_mv_experiences_subreddit;
DROP INDEX IF EXISTS idx_mv_experiences_author;
DROP INDEX IF EXISTS idx_mv_experiences_primary_drug;
