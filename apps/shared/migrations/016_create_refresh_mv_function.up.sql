-- Create function to refresh materialized view
-- This function can be called via Supabase RPC to refresh materialized views
-- Note: Using concurrent refresh (requires unique index on the view)

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

-- Grant execute permission to authenticated users (or adjust based on your needs)
GRANT EXECUTE ON FUNCTION refresh_materialized_view_function(text) TO authenticated;
GRANT EXECUTE ON FUNCTION refresh_materialized_view_function(text) TO service_role;
