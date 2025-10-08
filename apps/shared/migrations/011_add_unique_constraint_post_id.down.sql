-- Rollback: Remove unique constraint on post_id

ALTER TABLE extracted_features
DROP CONSTRAINT IF EXISTS extracted_features_post_id_key;
