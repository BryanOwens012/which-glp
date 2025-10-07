-- Migration: Create Reddit Posts and Comments Tables
-- Created: 2025-09-30
-- Description: Creates tables for storing ingested Reddit posts and comments with proper relationships

-- Posts table
CREATE TABLE reddit_posts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id text NOT NULL UNIQUE,  -- Reddit's post ID (without t3_ prefix)

    -- Timestamps
    ingested_at timestamptz NOT NULL DEFAULT now(),
    created_at timestamptz NOT NULL,

    -- Subreddit info
    subreddit text NOT NULL,
    subreddit_id text NOT NULL,

    -- Author info
    author text NOT NULL,
    author_flair_text text,

    -- Content
    title text NOT NULL,
    body text,  -- selftext, nullable for link posts
    body_html text,

    -- Metadata
    is_nsfw boolean NOT NULL DEFAULT false,
    score integer NOT NULL,
    upvote_ratio numeric(3,2),
    num_comments integer NOT NULL DEFAULT 0,

    -- URLs
    permalink text NOT NULL,
    url text,  -- external URL for link posts

    raw_json jsonb,

    CONSTRAINT valid_upvote_ratio CHECK (upvote_ratio >= 0 AND upvote_ratio <= 1)
);

-- Comments table
CREATE TABLE reddit_comments (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    comment_id text NOT NULL UNIQUE,  -- Reddit's comment ID (without t1_ prefix)

    -- Timestamps
    ingested_at timestamptz NOT NULL DEFAULT now(),
    created_at timestamptz NOT NULL,

    -- Hierarchy - foreign key to post
    post_id text NOT NULL REFERENCES reddit_posts(post_id) ON DELETE CASCADE,
    parent_comment_id text,  -- NULL for top-level comments, otherwise references another comment
    depth integer NOT NULL DEFAULT 1,  -- 1 = top-level, 2+ = nested replies

    -- Subreddit info (denormalized for convenience)
    subreddit text NOT NULL,
    subreddit_id text NOT NULL,

    -- Author info
    author text NOT NULL,
    author_flair_text text,

    -- Content
    body text NOT NULL,
    body_html text,

    -- Metadata
    is_nsfw boolean NOT NULL DEFAULT false,
    score integer NOT NULL,

    -- URLs
    permalink text NOT NULL,

    raw_json jsonb,

    CONSTRAINT top_level_has_no_parent CHECK (
        (depth = 1 AND parent_comment_id IS NULL) OR
        (depth > 1 AND parent_comment_id IS NOT NULL)
    )
);

-- Indexes for posts
CREATE INDEX idx_posts_subreddit_created ON reddit_posts(subreddit, created_at DESC);
CREATE INDEX idx_posts_post_id ON reddit_posts(post_id);
CREATE INDEX idx_posts_author ON reddit_posts(author);

-- Indexes for comments
CREATE INDEX idx_comments_post_id ON reddit_comments(post_id);
CREATE INDEX idx_comments_parent_comment_id ON reddit_comments(parent_comment_id) WHERE parent_comment_id IS NOT NULL;
CREATE INDEX idx_comments_comment_id ON reddit_comments(comment_id);
CREATE INDEX idx_comments_subreddit ON reddit_comments(subreddit);
CREATE INDEX idx_comments_depth ON reddit_comments(depth);

-- Composite index for efficient "all comments in a post" queries
CREATE INDEX idx_comments_post_depth_created ON reddit_comments(post_id, depth, created_at);

-- Add comments
COMMENT ON TABLE reddit_posts IS 'Stores Reddit posts ingested from the Reddit API';
COMMENT ON TABLE reddit_comments IS 'Stores Reddit comments ingested from the Reddit API, with parent relationships';
COMMENT ON COLUMN reddit_posts.post_id IS 'Reddit post ID without t3_ prefix (e.g., 1nsx6gz)';
COMMENT ON COLUMN reddit_comments.comment_id IS 'Reddit comment ID without t1_ prefix';
COMMENT ON COLUMN reddit_comments.depth IS 'Comment nesting level: 1 = top-level, 2+ = nested replies';
