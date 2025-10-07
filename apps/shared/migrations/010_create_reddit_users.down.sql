-- Migration 010 Rollback: Drop reddit_users table

DROP TABLE IF EXISTS reddit_users CASCADE;
