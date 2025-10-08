-- Add unique constraint on post_id in extracted_features table
-- This allows upsert operations to use ON CONFLICT (post_id)

-- First, remove any duplicate post_ids that might exist
-- Keep only the most recent extraction for each post_id
DELETE FROM extracted_features ef1
USING extracted_features ef2
WHERE ef1.id < ef2.id
  AND ef1.post_id = ef2.post_id
  AND ef1.post_id IS NOT NULL;

-- Now add the unique constraint
ALTER TABLE extracted_features
ADD CONSTRAINT extracted_features_post_id_key UNIQUE (post_id);
