-- 034_harden_refresh_function_search_path.down.sql
--
-- KEEP IN SYNC with 034_harden_refresh_function_search_path.up.sql.
--
-- Restores the migration 016 definition of refresh_materialized_view_function:
-- mutable (default) search_path and an unqualified view name. CREATE OR REPLACE
-- preserves the EXECUTE grants set by migration 033.
--
-- Idempotent: CREATE OR REPLACE is safe to run more than once.

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
