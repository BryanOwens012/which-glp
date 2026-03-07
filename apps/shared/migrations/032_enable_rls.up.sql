-- Enable RLS on all base tables
-- With no anon/authenticated policies, the anon key cannot access these tables directly
ALTER TABLE reddit_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE reddit_comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE extracted_features ENABLE ROW LEVEL SECURITY;
ALTER TABLE reddit_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE platform_config ENABLE ROW LEVEL SECURITY;

-- Explicit service_role full-access policies (belt-and-suspenders:
-- service_role already bypasses RLS in Supabase by default, but being explicit is safer)
CREATE POLICY "reddit_posts_service_role_all" ON reddit_posts
  FOR ALL TO service_role USING (TRUE) WITH CHECK (TRUE);
CREATE POLICY "reddit_comments_service_role_all" ON reddit_comments
  FOR ALL TO service_role USING (TRUE) WITH CHECK (TRUE);
CREATE POLICY "extracted_features_service_role_all" ON extracted_features
  FOR ALL TO service_role USING (TRUE) WITH CHECK (TRUE);
CREATE POLICY "reddit_users_service_role_all" ON reddit_users
  FOR ALL TO service_role USING (TRUE) WITH CHECK (TRUE);
CREATE POLICY "platform_config_service_role_all" ON platform_config
  FOR ALL TO service_role USING (TRUE) WITH CHECK (TRUE);

-- Materialized views cannot have RLS — block anon access via REVOKE
-- The API service (service role) retains access
REVOKE SELECT ON mv_experiences_denormalized FROM anon;
REVOKE SELECT ON mv_experiences_denormalized FROM authenticated;
