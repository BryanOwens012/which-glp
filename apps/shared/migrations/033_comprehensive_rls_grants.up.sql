-- 033_comprehensive_rls_grants.up.sql
--
-- Make RLS + privilege grants precise and comprehensive for every base table
-- and the denormalized materialized view.
--
-- Threat model / access design:
--   This is a backend data platform. ALL database access happens through the
--   service_role key, used by the tRPC API and the Python extraction/ingestion
--   services. End users never talk to PostgREST directly with the anon or
--   authenticated keys. Therefore:
--     * anon          -> NO direct table/view access
--     * authenticated -> NO direct table/view access
--     * service_role  -> full DML on tables, SELECT on the materialized view
--
-- This migration supersedes the coarse setup in 032 by adding the explicit
-- REVOKE/GRANT statements that 032 omitted (032 only toggled RLS + added
-- service_role policies). Supabase no longer auto-grants privileges to new
-- tables, and PostgREST checks GRANTs BEFORE RLS — so the REVOKEs below are
-- what actually deny anon/authenticated, and the GRANTs are what let
-- service_role through. RLS policies are belt-and-suspenders on top.
--
-- No fail-early data guard is needed: this migration only changes privileges
-- and RLS, introducing no data invariant (unique/FK/NOT NULL) that existing
-- rows could violate.
--
-- All statements are idempotent and safe to run more than once.

-- ---------------------------------------------------------------------------
-- 1. Lock down anon / authenticated / PUBLIC on every base table.
--    REVOKE is the primary access control (PostgREST evaluates grants first).
-- ---------------------------------------------------------------------------
REVOKE ALL ON TABLE reddit_posts        FROM anon, authenticated, PUBLIC;
REVOKE ALL ON TABLE reddit_comments     FROM anon, authenticated, PUBLIC;
REVOKE ALL ON TABLE extracted_features  FROM anon, authenticated, PUBLIC;
REVOKE ALL ON TABLE reddit_users        FROM anon, authenticated, PUBLIC;
REVOKE ALL ON TABLE platform_config     FROM anon, authenticated, PUBLIC;

-- ---------------------------------------------------------------------------
-- 2. Grant service_role exactly the DML it needs on each base table.
--    (service_role bypasses RLS via the BYPASSRLS role attribute, but still
--     requires table-level GRANTs to touch the table at all.)
-- ---------------------------------------------------------------------------
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE reddit_posts        TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE reddit_comments     TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE extracted_features  TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE reddit_users        TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE platform_config     TO service_role;

-- Sequences (serial/identity columns) — service_role needs USAGE+SELECT to
-- insert rows that draw from a sequence. anon/authenticated get nothing.
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon, authenticated, PUBLIC;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO service_role;

-- ---------------------------------------------------------------------------
-- 3. Enable RLS on every base table (idempotent) and (re)create the
--    explicit service_role full-access policies as defense-in-depth.
--    With RLS enabled and NO anon/authenticated policies, those roles are
--    denied even if a stray GRANT ever reappears.
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
-- 4. Materialized view: RLS cannot be applied to a matview, so access is
--    controlled purely by GRANT/REVOKE. Only service_role may read it.
-- ---------------------------------------------------------------------------
REVOKE ALL ON TABLE mv_experiences_denormalized FROM anon, authenticated, PUBLIC;
GRANT SELECT ON TABLE mv_experiences_denormalized TO service_role;

-- NOTE: RPC function access control (EXECUTE grants) and search_path hardening
-- live in migration 034_secure_rpc_functions.
