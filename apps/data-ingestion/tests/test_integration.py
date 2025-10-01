#!/usr/bin/env python3
"""
Integration tests for database migrations
These tests require a real Supabase connection with valid credentials in .env

Run with: pytest test_integration.py -v
Skip with: pytest test_migrations.py -v (skips integration tests)

Mark as integration test:
pytest -m "not integration" test_*.py  # Skip integration tests
pytest -m integration test_*.py        # Run only integration tests
"""

import sys
import pytest
import psycopg2
from pathlib import Path

# Add migrations directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'migrations'))
from run_migration import load_env, get_db_connection, run_migration


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestDatabaseIntegration:
    """Integration tests that require actual database connection"""

    def test_env_file_exists(self):
        """Verify .env file exists before running integration tests"""
        env_path = Path(__file__).resolve().parents[2] / ".env"
        assert env_path.exists(), ".env file not found - cannot run integration tests"

    def test_load_env_integration(self):
        """Test loading real environment variables"""
        load_env()
        import os
        assert "SUPABASE_URL" in os.environ
        assert "SUPABASE_DB_PASSWORD" in os.environ

    def test_database_connection_integration(self):
        """Test establishing real database connection"""
        load_env()
        conn = get_db_connection()

        # Verify connection is active
        assert conn is not None
        assert conn.closed == 0  # 0 means connection is open

        # Test a simple query
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1;")
            result = cursor.fetchone()
            assert result == (1,)

        conn.close()
        assert conn.closed == 1  # 1 means connection is closed

    def test_full_migration_cycle(self):
        """Test complete migration up and down cycle"""
        migration_dir = Path(__file__).parent

        # Step 1: Run down migration (cleanup from previous runs)
        down_file = migration_dir / "001_create_reddit_tables.down.sql"
        if down_file.exists():
            try:
                run_migration(down_file)
                print("✓ Down migration completed (cleanup)")
            except Exception as e:
                print(f"Note: Down migration failed (tables may not exist yet): {e}")

        # Step 2: Run up migration
        up_file = migration_dir / "001_create_reddit_tables.up.sql"
        assert up_file.exists(), "Up migration file not found"

        run_migration(up_file)
        print("✓ Up migration completed")

        # Step 3: Verify tables exist
        load_env()
        conn = get_db_connection()

        with conn.cursor() as cursor:
            # Check reddit_posts table
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'reddit_posts'
                );
            """)
            assert cursor.fetchone()[0] is True, "reddit_posts table not found"

            # Check reddit_comments table
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'reddit_comments'
                );
            """)
            assert cursor.fetchone()[0] is True, "reddit_comments table not found"

        conn.close()
        print("✓ Tables verified")

        # Step 4: Test down migration
        run_migration(down_file)
        print("✓ Down migration completed")

        # Step 5: Verify tables are dropped
        conn = get_db_connection()

        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'reddit_posts'
                );
            """)
            assert cursor.fetchone()[0] is False, "reddit_posts table still exists after rollback"

            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'reddit_comments'
                );
            """)
            assert cursor.fetchone()[0] is False, "reddit_comments table still exists after rollback"

        conn.close()
        print("✓ Tables dropped successfully")

        # Step 6: Re-run up migration for clean state
        run_migration(up_file)
        print("✓ Re-created tables for clean state")

    def test_insert_and_query_data(self):
        """Test inserting and querying data from tables"""
        load_env()
        conn = get_db_connection()

        try:
            with conn.cursor() as cursor:
                # Insert a test post
                cursor.execute("""
                    INSERT INTO reddit_posts (
                        post_id, created_at, subreddit, subreddit_id,
                        author, title, body, is_nsfw, score, num_comments, permalink
                    ) VALUES (
                        'test123', NOW(), 'test_subreddit', 't5_test',
                        'test_user', 'Test Post', 'This is a test', FALSE, 10, 0, '/r/test/test123'
                    ) ON CONFLICT (post_id) DO NOTHING;
                """)
                conn.commit()

                # Insert a test comment
                cursor.execute("""
                    INSERT INTO reddit_comments (
                        comment_id, created_at, post_id, depth,
                        subreddit, subreddit_id, author, body, is_nsfw, score, permalink
                    ) VALUES (
                        'comment123', NOW(), 'test123', 1,
                        'test_subreddit', 't5_test', 'test_commenter', 'Test comment', FALSE, 5, '/r/test/test123/comment123'
                    ) ON CONFLICT (comment_id) DO NOTHING;
                """)
                conn.commit()

                # Query the data
                cursor.execute("SELECT post_id, title FROM reddit_posts WHERE post_id = 'test123';")
                post = cursor.fetchone()
                assert post is not None
                assert post[0] == 'test123'
                assert post[1] == 'Test Post'

                cursor.execute("SELECT comment_id, body FROM reddit_comments WHERE comment_id = 'comment123';")
                comment = cursor.fetchone()
                assert comment is not None
                assert comment[0] == 'comment123'
                assert comment[1] == 'Test comment'

                # Test foreign key relationship
                cursor.execute("""
                    SELECT c.comment_id, p.title
                    FROM reddit_comments c
                    JOIN reddit_posts p ON c.post_id = p.post_id
                    WHERE c.comment_id = 'comment123';
                """)
                joined = cursor.fetchone()
                assert joined is not None
                assert joined[0] == 'comment123'
                assert joined[1] == 'Test Post'

                # Cleanup test data
                cursor.execute("DELETE FROM reddit_comments WHERE comment_id = 'comment123';")
                cursor.execute("DELETE FROM reddit_posts WHERE post_id = 'test123';")
                conn.commit()

                print("✓ Insert and query test passed")

        finally:
            conn.close()

    def test_foreign_key_constraint(self):
        """Test that foreign key constraint is enforced"""
        load_env()
        conn = get_db_connection()

        try:
            with conn.cursor() as cursor:
                # Try to insert comment with non-existent post_id
                with pytest.raises(psycopg2.IntegrityError):
                    cursor.execute("""
                        INSERT INTO reddit_comments (
                            comment_id, created_at, post_id, depth,
                            subreddit, subreddit_id, author, body, is_nsfw, score, permalink
                        ) VALUES (
                            'orphan_comment', NOW(), 'nonexistent_post', 1,
                            'test', 't5_test', 'user', 'orphan', FALSE, 0, '/test'
                        );
                    """)
                    conn.commit()

                conn.rollback()
                print("✓ Foreign key constraint test passed")

        finally:
            conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
