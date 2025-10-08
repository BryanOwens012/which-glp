-- Rollback migration: Drop the unprocessed query functions

DROP FUNCTION IF EXISTS get_unprocessed_posts(TEXT, INTEGER);
DROP FUNCTION IF EXISTS get_unanalyzed_users(INTEGER);
