"""
Database operations for storing Reddit data in Supabase

This module handles batch insertion of Reddit posts and comments using
the Supabase Python client (REST API) instead of direct PostgreSQL connections.

Benefits:
- Works on IPv4 networks (Railway compatible)
- Automatic connection pooling and retry logic
- No manual SSL/network configuration needed
- Consistent with rec-engine service

Reference: https://supabase.com/docs/reference/python/introduction
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from supabase import create_client, Client

logger = logging.getLogger(__name__)

# Batch size for bulk inserts
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
    """Database connection and operations handler for Supabase"""

    def __init__(self):
        """
        Initialize Supabase client

        Raises:
            DatabaseConfigurationError: If configuration is invalid
            DatabaseConnectionError: If unable to connect to database
        """
        self.client = self._get_client()
        logger.info("Supabase client initialized")

    def _get_client(self) -> Client:
        """
        Create and return a Supabase client

        Returns:
            Authenticated Supabase client

        Raises:
            DatabaseConfigurationError: If required environment variables are missing or invalid
        """
        # Load environment variables from .env if it exists
        # In Railway/production, environment variables are set via Railway UI
        try:
            env_path = Path(__file__).resolve().parents[3] / ".env"
            if env_path.exists():
                load_dotenv(env_path)
        except Exception:
            # In Railway/production, .env may not exist or path resolution may fail
            # Environment variables should be set via Railway UI
            pass

        # Validate required environment variables
        required_vars = ["SUPABASE_URL", "SUPABASE_SERVICE_KEY"]
        missing_vars = [var for var in required_vars if var not in os.environ or not os.environ[var]]

        if missing_vars:
            raise DatabaseConfigurationError(
                f"Supabase configuration incomplete: Missing or empty required environment variables: "
                f"{', '.join(missing_vars)}\n"
                f"Please add these credentials to your environment.\n"
                f"Get your Supabase credentials from: https://app.supabase.com/project/_/settings/api\n"
                f"Note: Use SUPABASE_SERVICE_KEY for write operations (not SUPABASE_ANON_KEY)"
            )

        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

        # Validate URL format
        if not supabase_url or not supabase_url.startswith("https://") or ".supabase.co" not in supabase_url:
            raise DatabaseConfigurationError(
                f"Invalid SUPABASE_URL format: {supabase_url}\n"
                f"Expected format: https://your-project.supabase.co\n"
                f"Check your SUPABASE_URL in environment variables."
            )

        try:
            client = create_client(supabase_url, supabase_key)
            logger.info("✓ Supabase client created successfully")
            return client
        except Exception as e:
            logger.error(f"Failed to create Supabase client: {e}")
            raise DatabaseConnectionError(
                f"Failed to create Supabase client: {e}\n"
                f"Please verify your credentials are correct."
            ) from e

    def insert_posts_batch(self, posts_data: List[Dict[str, Any]]) -> int:
        """
        Insert multiple posts using Supabase client

        Uses upsert for automatic deduplication (ON CONFLICT DO NOTHING equivalent).
        If batch insert fails, tries individual inserts to skip problematic records.

        Args:
            posts_data: List of dictionaries containing post data from parse_post()

        Returns:
            Number of posts actually inserted (excluding duplicates and failed records)

        Raises:
            DatabaseOperationError: If all records fail to insert
        """
        if not posts_data:
            logger.info("No posts to insert")
            return 0

        try:
            # Try batch insert first (most efficient)
            response = self.client.table('reddit_posts').upsert(
                posts_data,
                on_conflict='post_id',
                count='exact'
            ).execute()

            inserted = len(response.data) if response.data else 0
            logger.info(f"Inserted {inserted} posts (out of {len(posts_data)} total)")

            return inserted

        except Exception as batch_error:
            logger.warning(f"Batch insert failed, attempting individual inserts: {batch_error}")

            # Fall back to individual inserts
            successful = 0
            failed = 0

            for post in posts_data:
                try:
                    response = self.client.table('reddit_posts').upsert(
                        post,
                        on_conflict='post_id'
                    ).execute()
                    successful += 1
                except Exception as e:
                    failed += 1
                    post_id = post.get('post_id', 'unknown')
                    logger.error(f"Failed to insert post {post_id}: {e}")

            logger.info(f"Individual inserts: {successful} successful, {failed} failed (out of {len(posts_data)} total)")

            if successful == 0:
                raise DatabaseOperationError(
                    f"Failed to insert any posts into database. All {len(posts_data)} records failed.\n"
                    f"Last error: {batch_error}"
                ) from batch_error

            return successful

    def insert_comments_batch(self, comments_data: List[Dict[str, Any]]) -> int:
        """
        Insert multiple comments using Supabase client

        Uses upsert for automatic deduplication (ON CONFLICT DO NOTHING equivalent).
        If batch insert fails, tries individual inserts to skip problematic records.

        Args:
            comments_data: List of dictionaries containing comment data from parse_comment()

        Returns:
            Number of comments actually inserted (excluding duplicates and failed records)

        Raises:
            DatabaseOperationError: If all records fail to insert
        """
        if not comments_data:
            logger.info("No comments to insert")
            return 0

        try:
            # Try batch insert first (most efficient)
            response = self.client.table('reddit_comments').upsert(
                comments_data,
                on_conflict='comment_id',
                count='exact'
            ).execute()

            inserted = len(response.data) if response.data else 0
            logger.info(f"Inserted {inserted} comments (out of {len(comments_data)} total)")

            return inserted

        except Exception as batch_error:
            logger.warning(f"Batch insert failed, attempting individual inserts: {batch_error}")

            # Fall back to individual inserts
            successful = 0
            failed = 0

            for comment in comments_data:
                try:
                    response = self.client.table('reddit_comments').upsert(
                        comment,
                        on_conflict='comment_id'
                    ).execute()
                    successful += 1
                except Exception as e:
                    failed += 1
                    comment_id = comment.get('comment_id', 'unknown')
                    logger.error(f"Failed to insert comment {comment_id}: {e}")

            logger.info(f"Individual inserts: {successful} successful, {failed} failed (out of {len(comments_data)} total)")

            if successful == 0:
                raise DatabaseOperationError(
                    f"Failed to insert any comments into database. All {len(comments_data)} records failed.\n"
                    f"Last error: {batch_error}"
                ) from batch_error

            return successful

    def get_post_count(self, subreddit: str = None) -> int:
        """
        Get count of posts in database

        Args:
            subreddit: Optional subreddit filter

        Returns:
            Number of posts
        """
        try:
            query = self.client.table('reddit_posts').select('*', count='exact')

            if subreddit:
                query = query.eq('subreddit', subreddit)

            response = query.execute()
            return response.count if response.count is not None else 0

        except Exception as e:
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
            query = self.client.table('reddit_comments').select('*', count='exact')

            if subreddit:
                query = query.eq('subreddit', subreddit)

            response = query.execute()
            return response.count if response.count is not None else 0

        except Exception as e:
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
            response = self.client.table('reddit_posts') \
                .select('created_at') \
                .eq('subreddit', subreddit) \
                .order('created_at', desc=True) \
                .limit(1) \
                .execute()

            if response.data and len(response.data) > 0:
                return response.data[0]['created_at']
            return None

        except Exception as e:
            logger.error(f"Error getting latest post time: {e}")
            return None

    def close(self):
        """Close database connection (no-op for Supabase client)"""
        # Supabase client doesn't require explicit cleanup
        logger.info("Database client cleanup (no-op)")

    def __del__(self):
        """Cleanup: close connection when object is destroyed"""
        self.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    # Maintain compatibility with psycopg2-style conn attribute for legacy code
    @property
    def conn(self):
        """Compatibility property - returns self for code that expects conn.cursor()"""
        return self


# Alias for compatibility with ai_extraction module
DatabaseManager = Database
