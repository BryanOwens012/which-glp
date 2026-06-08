-- 034_harden_refresh_function_search_path.up.sql
--
-- Harden the SECURITY DEFINER matview-refresh function against search_path
-- injection. A SECURITY DEFINER function runs with the owner's (superuser)
-- privileges; if its search_path is mutable, a caller could prepend a schema
-- containing malicious objects and hijack name resolution inside the function.
--
-- Fix: pin an empty search_path and fully-qualify the target object.
--   * SET search_path = '' makes the function ignore the caller's search_path.
--   * pg_catalog is ALWAYS searched implicitly, so format() still resolves.
--   * the matview is referenced as public.%I (fully qualified), so it resolves
--     without relying on search_path.
--
-- CREATE OR REPLACE preserves the EXECUTE grants already set by migration 033
-- (service_role only), so this does not re-open the function to anon/auth.
--
-- Idempotent: CREATE OR REPLACE is safe to run more than once.

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
