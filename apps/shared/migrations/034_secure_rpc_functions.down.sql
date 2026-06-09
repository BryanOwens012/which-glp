-- 034_secure_rpc_functions.down.sql
--
-- KEEP IN SYNC with 034_secure_rpc_functions.up.sql.
--
-- Restores the pre-034 state, undoing the up migration's operations in reverse
-- order (reverse Part 2, then reverse Part 1; within each, reverse sub-steps).
-- NOTE: this intentionally restores the broad/insecure prior grants and the
-- mutable search_path; it is not a recommendation to keep them.
--
-- All statements are idempotent.

-- ===========================================================================
-- Reverse Part 2: SECURITY INVOKER RPCs
-- ===========================================================================

-- Reverse 2b: drop the pinned search_path (revert to the default mutable path).
ALTER FUNCTION get_unanalyzed_users(integer)        RESET search_path;
ALTER FUNCTION get_unprocessed_posts(text, integer) RESET search_path;
ALTER FUNCTION get_platform_stats()                 RESET search_path;
ALTER FUNCTION get_location_stats()                 RESET search_path;
ALTER FUNCTION get_drug_stats()                     RESET search_path;
ALTER FUNCTION get_demographics_stats()             RESET search_path;

-- Reverse 2a: restore the default PUBLIC EXECUTE plus the explicit
-- anon/authenticated grants. (service_role keeps EXECUTE.)
GRANT EXECUTE ON FUNCTION get_unanalyzed_users(integer)        TO PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION get_unprocessed_posts(text, integer) TO PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION get_platform_stats()                 TO PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION get_location_stats()                 TO PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION get_drug_stats()                     TO PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION get_demographics_stats()             TO PUBLIC, anon, authenticated;

-- ===========================================================================
-- Reverse Part 1: SECURITY DEFINER refresh function
-- ===========================================================================

-- Reverse 1b: restore the migration 016 definition (mutable search_path,
-- unqualified view name). CREATE OR REPLACE preserves the grants.
CREATE OR REPLACE FUNCTION refresh_materialized_view_function(view_name text)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  -- Use EXECUTE to dynamically refresh the materialized view
  -- Concurrent refresh (doesn't lock the view during refresh)
  EXECUTE format('REFRESH MATERIALIZED VIEW CONCURRENTLY %I', view_name);
END;
$$;

-- Reverse 1a: restore the default PUBLIC EXECUTE plus the explicit
-- `authenticated` grant from migration 016. (service_role keeps EXECUTE.)
GRANT EXECUTE ON FUNCTION refresh_materialized_view_function(text) TO PUBLIC;
GRANT EXECUTE ON FUNCTION refresh_materialized_view_function(text) TO authenticated;
