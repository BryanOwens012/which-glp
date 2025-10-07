-- Migration 012 Rollback: Revert to username-based primary key

DROP TABLE IF EXISTS reddit_users CASCADE;

CREATE TABLE reddit_users (
    username TEXT PRIMARY KEY,
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
    raw_response JSONB
);
