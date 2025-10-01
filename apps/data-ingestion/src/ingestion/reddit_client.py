"""
Reddit API client using PRAW (Python Reddit API Wrapper)

This module provides a wrapper around PRAW for fetching Reddit posts and comments
with proper error handling, rate limiting awareness, and logging.

PRAW Documentation: https://praw.readthedocs.io/en/stable/
Reddit API Rate Limits: 60 requests/minute with OAuth
"""

import os
import logging
from pathlib import Path
from typing import Iterator, List
from dotenv import load_dotenv
import praw
from praw.exceptions import PRAWException

logger = logging.getLogger(__name__)


class RedditClient:
    """
    Wrapper around PRAW for Reddit API operations

    Handles authentication, rate limiting, and provides convenient methods
    for fetching posts and comments from subreddits.
    """

    def __init__(self):
        """
        Initialize Reddit client with credentials from environment

        Raises:
            EnvironmentError: If required Reddit API credentials are missing
            PRAWException: If PRAW initialization fails
        """
        self.reddit = self._init_praw()
        logger.info("Reddit client initialized successfully")

    def _init_praw(self) -> praw.Reddit:
        """
        Initialize PRAW Reddit instance using environment variables

        Returns:
            Authenticated PRAW Reddit instance

        Raises:
            EnvironmentError: If required environment variables not found
        """
        # Load environment variables
        env_path = Path(__file__).resolve().parents[3] / ".env"
        if not env_path.exists():
            raise FileNotFoundError(f".env file not found at: {env_path}")

        load_dotenv(env_path)

        # Check for required environment variables
        needed_vars = [
            "REDDIT_API_APP_NAME",
            "REDDIT_API_APP_ID",
            "REDDIT_API_APP_SECRET",
        ]

        missing_vars = [var for var in needed_vars if var not in os.environ or not os.environ[var]]

        if missing_vars:
            raise EnvironmentError(
                f"Missing or empty environment variable(s): {', '.join(missing_vars)}\n"
                f"Please set these in your .env file"
            )

        try:
            # Initialize PRAW with read-only OAuth
            reddit = praw.Reddit(
                client_id=os.getenv("REDDIT_API_APP_ID"),
                client_secret=os.getenv("REDDIT_API_APP_SECRET"),
                user_agent=os.getenv("REDDIT_API_APP_NAME"),
            )

            # Verify authentication by accessing read-only property
            _ = reddit.read_only
            logger.info(f"PRAW authenticated as read-only client")

            return reddit

        except PRAWException as e:
            logger.error(f"Failed to initialize PRAW: {e}")
            raise

    def get_recent_posts(self, subreddit_name: str, limit: int = 100) -> Iterator:
        """
        Fetch recent posts from a subreddit (sorted by new)

        Args:
            subreddit_name: Name of subreddit (without r/ prefix)
            limit: Maximum number of posts to fetch (default 100, max 1000)

        Returns:
            Iterator of PRAW Submission objects

        Raises:
            PRAWException: If subreddit doesn't exist or API error occurs
        """
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            logger.info(f"Fetching up to {limit} recent posts from r/{subreddit_name}")

            # Fetch new posts (most recent first)
            posts = subreddit.new(limit=limit)

            return posts

        except PRAWException as e:
            logger.error(f"Error fetching posts from r/{subreddit_name}: {e}")
            raise

    def get_post_comments(self, post_id: str, limit: int = None) -> List:
        """
        Fetch all comments for a specific post

        Args:
            post_id: Reddit post ID (without t3_ prefix)
            limit: Maximum comments to fetch (None = all comments)

        Returns:
            List of PRAW Comment objects (flattened comment tree)

        Raises:
            PRAWException: If post doesn't exist or API error occurs
        """
        try:
            submission = self.reddit.submission(id=post_id)

            # Replace MoreComments objects with actual comments
            # limit=0 means "replace all MoreComments" (fetches all comments)
            # limit=N means "stop after replacing N MoreComments"
            logger.debug(f"Fetching comments for post {post_id}")
            submission.comments.replace_more(limit=0)

            # Flatten comment tree to list
            all_comments = submission.comments.list()

            logger.info(f"Fetched {len(all_comments)} comments for post {post_id}")

            # Apply limit if specified
            if limit:
                all_comments = all_comments[:limit]

            return all_comments

        except PRAWException as e:
            logger.error(f"Error fetching comments for post {post_id}: {e}")
            raise

    def get_post(self, post_id: str):
        """
        Fetch a single post by ID

        Args:
            post_id: Reddit post ID (without t3_ prefix)

        Returns:
            PRAW Submission object

        Raises:
            PRAWException: If post doesn't exist or API error occurs
        """
        try:
            submission = self.reddit.submission(id=post_id)
            # Access an attribute to trigger fetch
            _ = submission.title
            logger.debug(f"Fetched post {post_id}")
            return submission

        except PRAWException as e:
            logger.error(f"Error fetching post {post_id}: {e}")
            raise

    def check_subreddit_exists(self, subreddit_name: str) -> bool:
        """
        Check if a subreddit exists and is accessible

        Args:
            subreddit_name: Name of subreddit (without r/ prefix)

        Returns:
            True if subreddit exists and is accessible, False otherwise
        """
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            # Try to access a property to trigger fetch
            _ = subreddit.display_name
            logger.info(f"Subreddit r/{subreddit_name} exists and is accessible")
            return True

        except Exception as e:
            logger.warning(f"Subreddit r/{subreddit_name} not accessible: {e}")
            return False

    def get_rate_limit_info(self) -> dict:
        """
        Get current rate limit information

        Returns:
            Dictionary with rate limit info:
            - remaining: Number of requests remaining in current window
            - used: Number of requests used in current window
            - reset_timestamp: Unix timestamp when limit resets
        """
        try:
            # PRAW tracks rate limit info internally
            # Access via reddit.auth.limits
            limits = {
                'remaining': self.reddit.auth.limits.get('remaining'),
                'used': self.reddit.auth.limits.get('used'),
                'reset_timestamp': self.reddit.auth.limits.get('reset_timestamp')
            }

            logger.debug(f"Rate limit info: {limits}")
            return limits

        except Exception as e:
            logger.error(f"Error getting rate limit info: {e}")
            return {}
