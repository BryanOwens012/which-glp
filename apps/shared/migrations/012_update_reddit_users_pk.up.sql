-- Migration 012: Update reddit_users to use UUID primary key with username index

-- Step 1: Drop existing table (safe since no production data yet)
DROP TABLE IF EXISTS reddit_users CASCADE;

-- Step 2: Recreate with UUID primary key
CREATE TABLE reddit_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT NOT NULL UNIQUE,
    height_inches DECIMAL(5,2),
    starting_weight_lbs DECIMAL(6,2),
    current_weight_lbs DECIMAL(6,2),
    state TEXT,
    country TEXT DEFAULT 'USA',
    age INTEGER,
    sex TEXT CHECK (sex IN ('male', 'female', 'other', 'unknown')),
    comorbidities TEXT[],
    has_insurance BOOLEAN,
    insurance_provider TEXT,
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    post_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    confidence_score DECIMAL(3,2),
    model_used TEXT,
    processing_cost_usd DECIMAL(10,6),
    raw_response JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Step 3: Create index on username for fast lookups
CREATE INDEX idx_reddit_users_username ON reddit_users(username);

-- Step 4: Create index on analyzed_at for sorting recent analyses
CREATE INDEX idx_reddit_users_analyzed_at ON reddit_users(analyzed_at DESC);
