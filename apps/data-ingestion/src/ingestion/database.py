"""
Database operations for storing Reddit data in Supabase

This module handles batch insertion of Reddit posts and comments with:
- Efficient batch inserts (100 records per batch)
- Automatic deduplication using ON CONFLICT
- Connection pooling
- Transaction management
- Error handling and logging

Reference: psycopg2 batch operations
https://www.psycopg.org/docs/extras.html#fast-execution-helpers
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_batch
from psycopg2 import sql

logger = logging.getLogger(__name__)

# Batch size for bulk inserts (tuned for performance)
BATCH_SIZE = 100


class DatabaseConfigurationError(Exception):
    """Raised when database configuration is invalid or incomplete"""
    pass


class DatabaseConnectionError(Exception):
    """Raised when unable to connect to the database"""
    pass


class DatabaseOperationError(Exception):
    """Raised when database operations (insert, query, etc.) fail"""
    pass


class Database:
    """Database connection and operations handler for Supabase Postgres"""

    def __init__(self):
        """
        Initialize database connection

        Raises:
            DatabaseConfigurationError: If configuration is invalid
            DatabaseConnectionError: If unable to connect to database
        """
        self.conn = self._get_connection()
        logger.info("Database connection established")

    def _get_connection(self) -> psycopg2.extensions.connection:
        """
        Create and return a database connection to Supabase Postgres

        Returns:
            Active database connection

        Raises:
            DatabaseConfigurationError: If required environment variables are missing or invalid
            DatabaseConnectionError: If connection to database fails
        """
        # Load environment variables
        env_path = Path(__file__).resolve().parents[3] / ".env"
        if not env_path.exists():
            raise DatabaseConfigurationError(
                f"Database configuration error: .env file not found at expected location: {env_path}\n"
                f"Please create a .env file in the repository root with your Supabase credentials.\n"
                f"See README.md for setup instructions."
            )

        load_dotenv(env_path)

        # Validate required environment variables
        required_vars = ["SUPABASE_URL", "SUPABASE_DB_PASSWORD"]
        missing_vars = [var for var in required_vars if var not in os.environ or not os.environ[var]]

        if missing_vars:
            raise DatabaseConfigurationError(
                f"Supabase configuration incomplete: Missing or empty required environment variables: "
                f"{', '.join(missing_vars)}\n"
                f"Please add these credentials to your .env file.\n"
                f"Get your Supabase credentials from: https://app.supabase.com/project/_/settings/database\n"
                f"See README.md for detailed setup instructions."
            )

        # Extract database connection details from Supabase URL
        supabase_url = os.getenv("SUPABASE_URL")
        if not supabase_url.startswith("https://") or ".supabase.co" not in supabase_url:
            raise DatabaseConfigurationError(
                f"Invalid SUPABASE_URL format: {supabase_url}\n"
                f"Expected format: https://your-project.supabase.co\n"
                f"Check your SUPABASE_URL in .env matches your project URL from Supabase dashboard."
            )

        project_ref = supabase_url.replace("https://", "").replace(".supabase.co", "")

        # Construct connection parameters
        host = f"db.{project_ref}.supabase.co"
        port = 5432
        database = "postgres"
        user = "postgres"
        password = os.getenv("SUPABASE_DB_PASSWORD")

        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
                sslmode="require"
            )
            return conn
        except psycopg2.OperationalError as e:
            raise DatabaseConnectionError(
                f"Failed to establish connection to Supabase database: {e}\n"
                f"Connection details:\n"
                f"  Host: {host}\n"
                f"  Port: {port}\n"
                f"  Database: {database}\n"
                f"  User: {user}\n"
                f"Possible causes:\n"
                f"- Incorrect SUPABASE_DB_PASSWORD in .env\n"
                f"- Database not accessible (check Supabase dashboard)\n"
                f"- Network connectivity issues\n"
                f"- Database migration not yet run"
            ) from e

    def insert_posts_batch(self, posts_data: List[Dict[str, Any]]) -> int:
        """
        Insert multiple posts in a single batch operation

        Uses execute_batch for efficient bulk insert with automatic deduplication.
        Posts with duplicate post_id are silently ignored (ON CONFLICT DO NOTHING).

        Args:
            posts_data: List of dictionaries containing post data from parse_post()

        Returns:
            Number of posts actually inserted (excluding duplicates)

        Raises:
            DatabaseOperationError: If batch insert operation fails
        """
        if not posts_data:
            logger.info("No posts to insert")
            return 0

        # SQL query with deduplication
        query = """
            INSERT INTO reddit_posts (
                post_id, created_at, subreddit, subreddit_id,
                author, author_flair_text, title, body, body_html,
                is_nsfw, score, upvote_ratio, num_comments,
                permalink, url, raw_json
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (post_id) DO NOTHING;
        """

        # Convert dict data to tuple format for execute_batch
        data_tuples = [
            (
                p['post_id'], p['created_at'], p['subreddit'], p['subreddit_id'],
                p['author'], p['author_flair_text'], p['title'], p['body'], p['body_html'],
                p['is_nsfw'], p['score'], p['upvote_ratio'], p['num_comments'],
                p['permalink'], p['url'], psycopg2.extras.Json(p['raw_json'])
            )
            for p in posts_data
        ]

        try:
            with self.conn.cursor() as cursor:
                # Execute batch insert
                execute_batch(cursor, query, data_tuples, page_size=BATCH_SIZE)
                self.conn.commit()

                # Get number of rows inserted (excluding duplicates)
                inserted = cursor.rowcount
                logger.info(f"Inserted {inserted} posts (out of {len(posts_data)} total, {len(posts_data) - inserted} duplicates skipped)")

                return inserted

        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Batch insert operation failed for {len(posts_data)} posts: {e}")
            raise DatabaseOperationError(
                f"Failed to insert batch of {len(posts_data)} posts into database: {e}\n"
                f"The transaction has been rolled back. No data was inserted.\n"
                f"Possible causes:\n"
                f"- Database schema mismatch (check migrations are up to date)\n"
                f"- Invalid data format in posts\n"
                f"- Database connection lost\n"
                f"- Constraint violation"
            ) from e

    def insert_comments_batch(self, comments_data: List[Dict[str, Any]]) -> int:
        """
        Insert multiple comments in a single batch operation

        Uses execute_batch for efficient bulk insert with automatic deduplication.
        Comments with duplicate comment_id are silently ignored (ON CONFLICT DO NOTHING).

        Args:
            comments_data: List of dictionaries containing comment data from parse_comment()

        Returns:
            Number of comments actually inserted (excluding duplicates)

        Raises:
            DatabaseOperationError: If batch insert operation fails
        """
        if not comments_data:
            logger.info("No comments to insert")
            return 0

        # SQL query with deduplication
        query = """
            INSERT INTO reddit_comments (
                comment_id, created_at, post_id, parent_comment_id, depth,
                subreddit, subreddit_id, author, author_flair_text,
                body, body_html, is_nsfw, score, permalink, raw_json
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (comment_id) DO NOTHING;
        """

        # Convert dict data to tuple format for execute_batch
        data_tuples = [
            (
                c['comment_id'], c['created_at'], c['post_id'], c['parent_comment_id'], c['depth'],
                c['subreddit'], c['subreddit_id'], c['author'], c['author_flair_text'],
                c['body'], c['body_html'], c['is_nsfw'], c['score'], c['permalink'],
                psycopg2.extras.Json(c['raw_json'])
            )
            for c in comments_data
        ]

        try:
            with self.conn.cursor() as cursor:
                # Execute batch insert
                execute_batch(cursor, query, data_tuples, page_size=BATCH_SIZE)
                self.conn.commit()

                # Get number of rows inserted (excluding duplicates)
                inserted = cursor.rowcount
                logger.info(f"Inserted {inserted} comments (out of {len(comments_data)} total, {len(comments_data) - inserted} duplicates skipped)")

                return inserted

        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Batch insert operation failed for {len(comments_data)} comments: {e}")
            raise DatabaseOperationError(
                f"Failed to insert batch of {len(comments_data)} comments into database: {e}\n"
                f"The transaction has been rolled back. No data was inserted.\n"
                f"Possible causes:\n"
                f"- Database schema mismatch (check migrations are up to date)\n"
                f"- Invalid data format in comments\n"
                f"- Foreign key constraint violation (post_id does not exist)\n"
                f"- Database connection lost"
            ) from e

    def get_post_count(self, subreddit: str = None) -> int:
        """
        Get count of posts in database

        Args:
            subreddit: Optional subreddit filter

        Returns:
            Number of posts
        """
        try:
            with self.conn.cursor() as cursor:
                if subreddit:
                    cursor.execute(
                        "SELECT COUNT(*) FROM reddit_posts WHERE subreddit = %s;",
                        (subreddit,)
                    )
                else:
                    cursor.execute("SELECT COUNT(*) FROM reddit_posts;")

                return cursor.fetchone()[0]

        except psycopg2.Error as e:
            logger.error(f"Error getting post count: {e}")
            return 0

    def get_comment_count(self, subreddit: str = None) -> int:
        """
        Get count of comments in database

        Args:
            subreddit: Optional subreddit filter

        Returns:
            Number of comments
        """
        try:
            with self.conn.cursor() as cursor:
                if subreddit:
                    cursor.execute(
                        "SELECT COUNT(*) FROM reddit_comments WHERE subreddit = %s;",
                        (subreddit,)
                    )
                else:
                    cursor.execute("SELECT COUNT(*) FROM reddit_comments;")

                return cursor.fetchone()[0]

        except psycopg2.Error as e:
            logger.error(f"Error getting comment count: {e}")
            return 0

    def get_latest_post_time(self, subreddit: str) -> Any:
        """
        Get the created_at timestamp of the most recent post for a subreddit

        Useful for incremental ingestion to avoid re-fetching old posts.

        Args:
            subreddit: Subreddit name

        Returns:
            Datetime of most recent post, or None if no posts exist
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT MAX(created_at)
                    FROM reddit_posts
                    WHERE subreddit = %s;
                    """,
                    (subreddit,)
                )
                result = cursor.fetchone()
                return result[0] if result else None

        except psycopg2.Error as e:
            logger.error(f"Error getting latest post time: {e}")
            return None

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def __del__(self):
        """Cleanup: close connection when object is destroyed"""
        self.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
