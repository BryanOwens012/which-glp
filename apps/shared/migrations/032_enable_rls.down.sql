DROP POLICY IF EXISTS "reddit_posts_service_role_all" ON reddit_posts;
DROP POLICY IF EXISTS "reddit_comments_service_role_all" ON reddit_comments;
DROP POLICY IF EXISTS "extracted_features_service_role_all" ON extracted_features;
DROP POLICY IF EXISTS "reddit_users_service_role_all" ON reddit_users;
DROP POLICY IF EXISTS "platform_config_service_role_all" ON platform_config;

ALTER TABLE reddit_posts DISABLE ROW LEVEL SECURITY;
ALTER TABLE reddit_comments DISABLE ROW LEVEL SECURITY;
ALTER TABLE extracted_features DISABLE ROW LEVEL SECURITY;
ALTER TABLE reddit_users DISABLE ROW LEVEL SECURITY;
ALTER TABLE platform_config DISABLE ROW LEVEL SECURITY;

GRANT SELECT ON mv_experiences_denormalized TO anon;
GRANT SELECT ON mv_experiences_denormalized TO authenticated;
