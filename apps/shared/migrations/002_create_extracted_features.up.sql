-- Migration 002: Create extracted_features table for AI-extracted structured data
-- This table stores structured data extracted from Reddit posts/comments using Claude AI

CREATE TABLE extracted_features (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Foreign keys (exactly one must be set)
  post_id TEXT REFERENCES reddit_posts(post_id) ON DELETE CASCADE,
  comment_id TEXT REFERENCES reddit_comments(comment_id) ON DELETE CASCADE,

  -- Extracted summary
  summary TEXT NOT NULL,

  -- Weight data (JSONB with value, unit, confidence)
  beginning_weight JSONB,
  end_weight JSONB,

  -- Duration and cost
  duration_weeks INTEGER,
  cost_per_month NUMERIC(10,2),
  currency TEXT DEFAULT 'USD',

  -- Drug information
  drugs_mentioned TEXT[],
  primary_drug TEXT,
  drug_sentiments JSONB,

  -- Sentiment scores
  sentiment_pre NUMERIC(3,2) CHECK (sentiment_pre >= 0 AND sentiment_pre <= 1),
  sentiment_post NUMERIC(3,2) CHECK (sentiment_post >= 0 AND sentiment_post <= 1),
  recommendation_score NUMERIC(3,2) CHECK (recommendation_score >= 0 AND recommendation_score <= 1),

  -- Insurance data
  has_insurance BOOLEAN,
  insurance_provider TEXT,

  -- Side effects, comorbidities, and location
  side_effects TEXT[],
  comorbidities TEXT[],
  location TEXT,

  -- Demographics (for personalized predictions)
  age INTEGER CHECK (age >= 13 AND age <= 120),
  sex TEXT CHECK (sex IN ('male', 'female', 'ftm', 'mtf', 'other')),
  state TEXT,
  country TEXT,

  -- AI processing metadata
  model_used TEXT NOT NULL,
  confidence_score NUMERIC(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
  processing_cost_usd NUMERIC(10,6),
  tokens_input INTEGER,
  tokens_output INTEGER,
  processing_time_ms INTEGER,
  processed_at TIMESTAMPTZ DEFAULT NOW(),

  -- Raw AI response for debugging
  raw_response JSONB,

  -- Constraints
  CONSTRAINT one_source_only CHECK (
    (post_id IS NOT NULL AND comment_id IS NULL) OR
    (post_id IS NULL AND comment_id IS NOT NULL)
  ),
  CONSTRAINT valid_currency CHECK (currency IN ('USD', 'CAD', 'GBP', 'EUR', 'AUD'))
);

-- Indexes for efficient querying
CREATE INDEX idx_extracted_features_post ON extracted_features(post_id) WHERE post_id IS NOT NULL;
CREATE INDEX idx_extracted_features_comment ON extracted_features(comment_id) WHERE comment_id IS NOT NULL;
CREATE INDEX idx_extracted_features_drugs ON extracted_features USING GIN(drugs_mentioned);
CREATE INDEX idx_extracted_features_primary_drug ON extracted_features(primary_drug) WHERE primary_drug IS NOT NULL;
CREATE INDEX idx_extracted_features_processed_at ON extracted_features(processed_at);
CREATE INDEX idx_extracted_features_model ON extracted_features(model_used);

-- Indexes for demographic filtering (personalized predictions)
CREATE INDEX idx_extracted_features_age ON extracted_features(age) WHERE age IS NOT NULL;
CREATE INDEX idx_extracted_features_sex ON extracted_features(sex) WHERE sex IS NOT NULL;
CREATE INDEX idx_extracted_features_state ON extracted_features(state) WHERE state IS NOT NULL;
CREATE INDEX idx_extracted_features_country ON extracted_features(country) WHERE country IS NOT NULL;

-- Comments for documentation
COMMENT ON TABLE extracted_features IS 'AI-extracted structured data from Reddit posts and comments';
COMMENT ON COLUMN extracted_features.post_id IS 'References reddit_posts.post_id if this extraction is from a post';
COMMENT ON COLUMN extracted_features.comment_id IS 'References reddit_comments.comment_id if this extraction is from a comment';
COMMENT ON COLUMN extracted_features.summary IS 'First-person faithful summary of the user experience';
COMMENT ON COLUMN extracted_features.beginning_weight IS 'JSON: {value: float, unit: "lbs"|"kg", confidence: "high"|"medium"|"low"}';
COMMENT ON COLUMN extracted_features.end_weight IS 'JSON: {value: float, unit: "lbs"|"kg", confidence: "high"|"medium"|"low"}';
COMMENT ON COLUMN extracted_features.drugs_mentioned IS 'Array of all drug names mentioned in the post/comment';
COMMENT ON COLUMN extracted_features.primary_drug IS 'The main drug being discussed';
COMMENT ON COLUMN extracted_features.drug_sentiments IS 'JSON: {"Ozempic": 0.85, "Wegovy": 0.60} - Sentiment toward each drug (0-1)';
COMMENT ON COLUMN extracted_features.sentiment_pre IS 'Quality of life/sentiment BEFORE starting the drug (0-1)';
COMMENT ON COLUMN extracted_features.sentiment_post IS 'Quality of life/sentiment AFTER/while taking the drug (0-1)';
COMMENT ON COLUMN extracted_features.recommendation_score IS 'Likelihood they would recommend this drug to a stranger in similar circumstances (0-1)';
COMMENT ON COLUMN extracted_features.comorbidities IS 'Array of pre-existing conditions (diabetes, pcos, hypertension, etc.)';
COMMENT ON COLUMN extracted_features.age IS 'Age of user if mentioned (13-120)';
COMMENT ON COLUMN extracted_features.sex IS 'Sex/gender identity if mentioned (male/female/ftm/mtf/other). ftm=female-to-male trans, mtf=male-to-female trans';
COMMENT ON COLUMN extracted_features.state IS 'US state if mentioned (for location-specific predictions)';
COMMENT ON COLUMN extracted_features.country IS 'Country if mentioned (for international pricing differences)';
COMMENT ON COLUMN extracted_features.model_used IS 'Claude model used (e.g., "claude-sonnet-4-20250514", "claude-3-5-haiku-20241022")';
COMMENT ON COLUMN extracted_features.confidence_score IS 'Overall confidence score (0-1) for the extraction accuracy';
COMMENT ON COLUMN extracted_features.processing_cost_usd IS 'Cost in USD for this API call';
COMMENT ON COLUMN extracted_features.raw_response IS 'Full Claude API response for debugging';
