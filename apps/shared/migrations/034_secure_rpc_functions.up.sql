-- 034_secure_rpc_functions.up.sql
--
-- Secure every RPC function exposed via PostgREST: restrict who may EXECUTE
-- each one (service_role only) and harden how it executes (fixed search_path).
-- This consolidates all FUNCTION-level security in one place; migration 033
-- covers TABLE/matview/sequence access control.
--
-- Background:
--   * All RPC callers use the service_role key — the tRPC API
--     (SUPABASE_SERVICE_KEY) and the Python services (SUPABASE_SERVICE_KEY).
--     The frontend only talks to the tRPC API, never Supabase directly, so no
--     anon/authenticated EXECUTE is needed on any function.
--   * Postgres grants EXECUTE to PUBLIC by default on every function, so the
--     REVOKE ... FROM PUBLIC below is what actually closes the public surface.
--   * A mutable search_path is a privilege-escalation vector on a SECURITY
--     DEFINER function (it runs as the owner); on SECURITY INVOKER functions it
--     is only a determinism/lint concern. Both are pinned below.
--
-- No data guard needed: this changes only function privileges and config, not
-- data or any invariant. All statements are idempotent.

-- ===========================================================================
-- Part 1: refresh_materialized_view_function(text) — SECURITY DEFINER
-- ===========================================================================

-- 1a. Restrict EXECUTE to service_role. It was executable by PUBLIC (default)
--     and `authenticated` (migration 016), letting any anon/authenticated
--     caller trigger refreshes of arbitrary matviews. Nothing calls this RPC
--     (the view-refresher cron refreshes directly as the postgres role via the
--     session pooler), so lock it to service_role.
REVOKE ALL ON FUNCTION refresh_materialized_view_function(text) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION refresh_materialized_view_function(text) TO service_role;

-- 1b. Harden against search_path injection: pin an empty search_path and fully
--     qualify the target (pg_catalog is always implicitly searched, so format()
--     still resolves). CREATE OR REPLACE preserves the grant set in 1a.
CREATE OR REPLACE FUNCTION refresh_materialized_view_function(view_name text)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
  -- Concurrent refresh (doesn't lock the view during refresh).
  -- Fully-qualified to public so an empty search_path still resolves the view.
  EXECUTE format('REFRESH MATERIALIZED VIEW CONCURRENTLY public.%I', view_name);
END;
$$;

-- ===========================================================================
-- Part 2: read/operational RPCs — SECURITY INVOKER
-- ===========================================================================

-- 2a. Restrict EXECUTE to service_role (revoke the default PUBLIC grant plus the
--     explicit anon/authenticated grants from earlier migrations).
REVOKE ALL ON FUNCTION get_demographics_stats()             FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION get_drug_stats()                     FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION get_location_stats()                 FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION get_platform_stats()                 FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION get_unprocessed_posts(text, integer) FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION get_unanalyzed_users(integer)        FROM PUBLIC, anon, authenticated;

GRANT EXECUTE ON FUNCTION get_demographics_stats()             TO service_role;
GRANT EXECUTE ON FUNCTION get_drug_stats()                     TO service_role;
GRANT EXECUTE ON FUNCTION get_location_stats()                 TO service_role;
GRANT EXECUTE ON FUNCTION get_platform_stats()                 TO service_role;
GRANT EXECUTE ON FUNCTION get_unprocessed_posts(text, integer) TO service_role;
GRANT EXECUTE ON FUNCTION get_unanalyzed_users(integer)        TO service_role;

-- 2b. Pin a fixed search_path. These are SECURITY INVOKER, so use ALTER FUNCTION
--     (no body rewrite, zero regression risk on the live RPCs). The bodies
--     reference public objects unqualified, so pin to `pg_catalog, public`
--     (pg_catalog FIRST so built-in names can't be shadowed) rather than ''.
ALTER FUNCTION get_demographics_stats()             SET search_path = pg_catalog, public;
ALTER FUNCTION get_drug_stats()                     SET search_path = pg_catalog, public;
ALTER FUNCTION get_location_stats()                 SET search_path = pg_catalog, public;
ALTER FUNCTION get_platform_stats()                 SET search_path = pg_catalog, public;
ALTER FUNCTION get_unprocessed_posts(text, integer) SET search_path = pg_catalog, public;
ALTER FUNCTION get_unanalyzed_users(integer)        SET search_path = pg_catalog, public;
