-- 035_pin_invoker_function_search_path.up.sql
--
-- Pin a fixed (non-mutable) search_path on the SECURITY INVOKER RPC functions.
--
-- These six functions are SECURITY INVOKER, so a mutable search_path cannot
-- cross a privilege boundary (they run as the caller) — the real escalation
-- vector only applies to SECURITY DEFINER functions, which is handled for the
-- one DEFINER function in migration 034. The benefit here is hygiene and
-- determinism: a fixed search_path makes object resolution independent of the
-- caller's session and satisfies the Supabase "function_search_path_mutable"
-- lint.
--
-- We use ALTER FUNCTION ... SET search_path (NOT CREATE OR REPLACE) so the
-- function bodies are left untouched — zero regression risk on the live RPCs.
-- The bodies reference objects in `public` unqualified, so we pin to
-- `pg_catalog, public` rather than ''. pg_catalog is listed FIRST so built-in
-- names can never be shadowed by objects in public.
--
-- No data guard needed: this changes only function configuration, not data or
-- any invariant. Idempotent: re-running sets the same value.

ALTER FUNCTION get_demographics_stats()             SET search_path = pg_catalog, public;
ALTER FUNCTION get_drug_stats()                     SET search_path = pg_catalog, public;
ALTER FUNCTION get_location_stats()                 SET search_path = pg_catalog, public;
ALTER FUNCTION get_platform_stats()                 SET search_path = pg_catalog, public;
ALTER FUNCTION get_unprocessed_posts(text, integer) SET search_path = pg_catalog, public;
ALTER FUNCTION get_unanalyzed_users(integer)        SET search_path = pg_catalog, public;
