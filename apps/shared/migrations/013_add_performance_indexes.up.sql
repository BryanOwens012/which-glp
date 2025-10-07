-- Migration 013: Add performance indexes for common query patterns

-- reddit_posts indexes
CREATE INDEX IF NOT EXISTS idx_reddit_posts_post_id ON reddit_posts(post_id);
CREATE INDEX IF NOT EXISTS idx_reddit_posts_subreddit ON reddit_posts(subreddit);
CREATE INDEX IF NOT EXISTS idx_reddit_posts_subreddit_id ON reddit_posts(subreddit_id);
CREATE INDEX IF NOT EXISTS idx_reddit_posts_author ON reddit_posts(author);

-- mv_experiences_denormalized indexes
CREATE INDEX IF NOT EXISTS idx_mv_experiences_post_id ON mv_experiences_denormalized(post_id);
CREATE INDEX IF NOT EXISTS idx_mv_experiences_subreddit ON mv_experiences_denormalized(subreddit);
CREATE INDEX IF NOT EXISTS idx_mv_experiences_author ON mv_experiences_denormalized(author);
CREATE INDEX IF NOT EXISTS idx_mv_experiences_primary_drug ON mv_experiences_denormalized(primary_drug);
