-- 035_pin_invoker_function_search_path.down.sql
--
-- KEEP IN SYNC with 035_pin_invoker_function_search_path.up.sql.
--
-- Restores the pre-035 state by removing the pinned search_path from each
-- function (RESET reverts to the default, mutable search_path). The function
-- bodies were never modified by the up migration, so nothing else to undo.
--
-- Idempotent: RESET is safe to run more than once.

ALTER FUNCTION get_unanalyzed_users(integer)        RESET search_path;
ALTER FUNCTION get_unprocessed_posts(text, integer) RESET search_path;
ALTER FUNCTION get_platform_stats()                 RESET search_path;
ALTER FUNCTION get_location_stats()                 RESET search_path;
ALTER FUNCTION get_drug_stats()                     RESET search_path;
ALTER FUNCTION get_demographics_stats()             RESET search_path;
