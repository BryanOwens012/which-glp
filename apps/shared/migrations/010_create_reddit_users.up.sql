-- Migration 010: Create reddit_users table for user demographics
-- This table stores aggregated demographic data extracted from Reddit users' post/comment history

CREATE TABLE IF NOT EXISTS reddit_users (
    -- Primary key
    username TEXT PRIMARY KEY,

    -- Demographic data extracted from user's posts/comments
    height_inches DECIMAL(5,2),  -- Height in inches (e.g., 68.5 for 5'8.5")
    starting_weight_lbs DECIMAL(6,2),  -- Starting weight in pounds
    current_weight_lbs DECIMAL(6,2),  -- Current/most recent weight mentioned
    state TEXT,  -- US state (e.g., "California", "TX")
    country TEXT DEFAULT 'USA',  -- Country
    age INTEGER,  -- Age in years
    sex TEXT CHECK (sex IN ('male', 'female', 'other', 'unknown')),  -- Gender

    -- Medical conditions
    comorbidities TEXT[],  -- Array of conditions (e.g., ["diabetes", "PCOS"])

    -- Metadata
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),  -- When analysis was performed
    post_count INTEGER DEFAULT 0,  -- Number of posts analyzed
    comment_count INTEGER DEFAULT 0,  -- Number of comments analyzed
    confidence_score DECIMAL(3,2),  -- AI confidence (0.00 to 1.00)

    -- AI processing metadata
    model_used TEXT,  -- AI model used for extraction (e.g., "glm-4.5-air")
    processing_cost_usd DECIMAL(10,6),  -- Cost of AI extraction
    raw_response JSONB  -- Full AI response for debugging
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_reddit_users_state ON reddit_users(state);
CREATE INDEX IF NOT EXISTS idx_reddit_users_analyzed_at ON reddit_users(analyzed_at);
CREATE INDEX IF NOT EXISTS idx_reddit_users_confidence ON reddit_users(confidence_score DESC);

-- Comments
COMMENT ON TABLE reddit_users IS 'User demographics extracted from Reddit post/comment history using GLM-4.5-Air';
COMMENT ON COLUMN reddit_users.username IS 'Reddit username (without u/ prefix)';
COMMENT ON COLUMN reddit_users.height_inches IS 'Height in inches (extracted from user posts)';
COMMENT ON COLUMN reddit_users.starting_weight_lbs IS 'Starting weight before GLP-1 medication';
COMMENT ON COLUMN reddit_users.current_weight_lbs IS 'Most recent weight mentioned';
COMMENT ON COLUMN reddit_users.state IS 'US state of residence (if mentioned)';
COMMENT ON COLUMN reddit_users.comorbidities IS 'Array of medical conditions (diabetes, PCOS, etc.)';
COMMENT ON COLUMN reddit_users.confidence_score IS 'AI extraction confidence score (0.0-1.0)';
