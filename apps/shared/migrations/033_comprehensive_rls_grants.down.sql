-- 033_comprehensive_rls_grants.down.sql
--
-- KEEP IN SYNC with 033_comprehensive_rls_grants.up.sql.
--
-- Rolls back to the pre-033 state (i.e. the state left by migration 032):
-- RLS enabled with service_role full-access policies, the matview readable
-- only by service_role, and the legacy Supabase auto-grants restored on the
-- base tables for anon/authenticated. Operations are applied in reverse order
-- of the up migration.
--
-- All statements are idempotent and safe to run more than once.

-- NOTE: RPC function grants/hardening are owned by migration 034; its own
-- down migration reverses them. Nothing function-related to undo here.

-- ---------------------------------------------------------------------------
-- Reverse step 4 (matview): nothing to undo. 033 only made the existing state
-- explicit — PUBLIC never had matview access, anon/authenticated already lost
-- SELECT in 032, and service_role's SELECT predates 033 (legacy auto-grant).
-- Re-granting matview access to anon/authenticated is intentionally NOT done:
-- 032 owns that revoke, and it must stay revoked at the pre-033 state.
-- ---------------------------------------------------------------------------

-- ---------------------------------------------------------------------------
-- Reverse step 3: keep RLS enabled and the service_role policies in place
-- (they predate 033, having been created by 032). Recreate them idempotently
-- so the rollback is self-consistent.
-- ---------------------------------------------------------------------------
ALTER TABLE reddit_posts        ENABLE ROW LEVEL SECURITY;
ALTER TABLE reddit_comments     ENABLE ROW LEVEL SECURITY;
ALTER TABLE extracted_features  ENABLE ROW LEVEL SECURITY;
ALTER TABLE reddit_users        ENABLE ROW LEVEL SECURITY;
ALTER TABLE platform_config     ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "reddit_posts_service_role_all"       ON reddit_posts;
DROP POLICY IF EXISTS "reddit_comments_service_role_all"    ON reddit_comments;
DROP POLICY IF EXISTS "extracted_features_service_role_all" ON extracted_features;
DROP POLICY IF EXISTS "reddit_users_service_role_all"       ON reddit_users;
DROP POLICY IF EXISTS "platform_config_service_role_all"    ON platform_config;

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

-- ---------------------------------------------------------------------------
-- Reverse step 2: the service_role table/sequence grants are kept (they are
-- the desired backend access and/or predate 033). Restore the sequence access
-- that step 2 of the up revoked from anon/authenticated.
-- ---------------------------------------------------------------------------
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;

-- ---------------------------------------------------------------------------
-- Reverse step 1: restore the legacy Supabase auto-grants that 033 revoked
-- from anon/authenticated on the base tables. (RLS still gates row access;
-- these grants merely restore the privilege state that existed before 033.)
-- ---------------------------------------------------------------------------
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE reddit_posts        TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE reddit_comments     TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE extracted_features  TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE reddit_users        TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE platform_config     TO anon, authenticated;
