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

from shared.config import get_monorepo_root

logger = logging.getLogger(__name__)


class RedditClientConfigurationError(Exception):
    """Raised when Reddit client configuration is invalid or incomplete"""
    pass


class RedditAPIError(Exception):
    """Raised when Reddit API requests fail"""
    pass


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
            RedditClientConfigurationError: If required Reddit API credentials are missing or invalid
            RedditAPIError: If PRAW initialization or authentication fails
        """
        self.reddit = self._init_praw()
        logger.info("Reddit client initialized successfully")

    def _init_praw(self) -> praw.Reddit:
        """
        Initialize PRAW Reddit instance using environment variables

        Returns:
            Authenticated PRAW Reddit instance

        Raises:
            RedditClientConfigurationError: If .env file or required credentials are missing
            RedditAPIError: If PRAW initialization or authentication fails
        """
        # Load environment variables from monorepo root
        # Uses shared.config.get_monorepo_root() for robust path resolution
        # that works regardless of whether module is run directly or as editable install
        try:
            env_path = get_monorepo_root() / ".env"
        except RuntimeError as e:
            raise RedditClientConfigurationError(
                f"Configuration error: Could not locate monorepo root: {e}\n"
                f"Please ensure you are running from within the git repository."
            )

        if not env_path.exists():
            raise RedditClientConfigurationError(
                f"Configuration error: .env file not found at expected location: {env_path}\n"
                f"Please create a .env file in the repository root with your Reddit API credentials.\n"
                f"See README.md for setup instructions."
            )

        load_dotenv(env_path)

        # Check for required environment variables
        needed_vars = [
            "REDDIT_API_APP_NAME",
            "REDDIT_API_APP_ID",
            "REDDIT_API_APP_SECRET",
        ]

        missing_vars = [var for var in needed_vars if var not in os.environ or not os.environ[var]]

        if missing_vars:
            raise RedditClientConfigurationError(
                f"Reddit API configuration incomplete: Missing or empty required environment variables: "
                f"{', '.join(missing_vars)}\n"
                f"Please add these credentials to your .env file.\n"
                f"To get Reddit API credentials, visit: https://www.reddit.com/prefs/apps\n"
                f"See README.md for detailed setup instructions."
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
            logger.error(f"Reddit API authentication failed: {e}")
            raise RedditAPIError(
                f"Failed to authenticate with Reddit API: {e}\n"
                f"Please verify your Reddit API credentials in .env are correct.\n"
                f"Check that REDDIT_API_APP_ID and REDDIT_API_APP_SECRET match your app at "
                f"https://www.reddit.com/prefs/apps"
            ) from e

    def get_recent_posts(self, subreddit_name: str, limit: int = 100) -> Iterator:
        """
        Fetch recent posts from a subreddit (sorted by new)

        Args:
            subreddit_name: Name of subreddit (without r/ prefix)
            limit: Maximum number of posts to fetch (default 100, max 1000)

        Returns:
            Iterator of PRAW Submission objects

        Raises:
            RedditAPIError: If subreddit doesn't exist, is private, or API error occurs
        """
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            logger.info(f"Fetching up to {limit} recent posts from r/{subreddit_name}")

            # Fetch new posts (most recent first)
            posts = subreddit.new(limit=limit)

            return posts

        except PRAWException as e:
            logger.error(f"Failed to fetch posts from r/{subreddit_name}: {e}")
            raise RedditAPIError(
                f"Unable to fetch posts from r/{subreddit_name}: {e}\n"
                f"Possible causes:\n"
                f"- Subreddit does not exist\n"
                f"- Subreddit is private or banned\n"
                f"- Rate limit exceeded (60 requests/minute)\n"
                f"- Reddit API is temporarily unavailable"
            ) from e

    def get_top_posts(self, subreddit_name: str, time_filter: str = "year", limit: int = 100) -> Iterator:
        """
        Fetch top posts from a subreddit by score within a time period

        Args:
            subreddit_name: Name of subreddit (without r/ prefix)
            time_filter: Time period filter - one of: "hour", "day", "week", "month", "year", "all"
            limit: Maximum number of posts to fetch (default 100, max 1000)

        Returns:
            Iterator of PRAW Submission objects sorted by score (descending)

        Raises:
            RedditAPIError: If subreddit doesn't exist, is private, or API error occurs
        """
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            logger.info(f"Fetching top {limit} posts from past {time_filter} from r/{subreddit_name}")

            # Fetch top posts by score within time period
            posts = subreddit.top(time_filter=time_filter, limit=limit)

            return posts

        except PRAWException as e:
            logger.error(f"Failed to fetch top posts from r/{subreddit_name}: {e}")
            raise RedditAPIError(
                f"Unable to fetch top posts from r/{subreddit_name}: {e}\n"
                f"Possible causes:\n"
                f"- Subreddit does not exist\n"
                f"- Subreddit is private or banned\n"
                f"- Invalid time_filter parameter\n"
                f"- Rate limit exceeded (60 requests/minute)\n"
                f"- Reddit API is temporarily unavailable"
            ) from e

    def get_post_comments(self, post_id: str, limit: int = None, sort_by_score: bool = False) -> List:
        """
        Fetch comments for a specific post

        Args:
            post_id: Reddit post ID (without t3_ prefix)
            limit: Maximum comments to fetch (None = all comments)
            sort_by_score: If True and limit is set, return top N comments by score (default: False)

        Returns:
            List of PRAW Comment objects (flattened comment tree)

        Raises:
            RedditAPIError: If post doesn't exist or API error occurs
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

            # Sort by score if requested
            if sort_by_score and limit:
                # Sort comments by score (descending)
                all_comments = sorted(all_comments, key=lambda c: c.score, reverse=True)
                logger.debug(f"Sorted {len(all_comments)} comments by score for post {post_id}")

            # Apply limit if specified
            if limit:
                all_comments = all_comments[:limit]

            logger.info(f"Fetched {len(all_comments)} comments for post {post_id}")

            return all_comments

        except PRAWException as e:
            logger.error(f"Failed to fetch comments for post {post_id}: {e}")
            raise RedditAPIError(
                f"Unable to fetch comments for post {post_id}: {e}\n"
                f"The post may have been deleted, or the Reddit API may be unavailable."
            ) from e

    def extract_comments_from_submission(self, submission, limit: int = None, sort_by_score: bool = False) -> List:
        """
        Extract comments directly from a submission object (no additional API call)

        This is more efficient than get_post_comments() when you already have the submission object,
        as it avoids an extra API call to fetch the submission.

        Args:
            submission: PRAW Submission object (already fetched)
            limit: Maximum comments to extract (None = all comments)
            sort_by_score: If True and limit is set, return top N comments by score (default: False)

        Returns:
            List of PRAW Comment objects (flattened comment tree)

        Raises:
            RedditAPIError: If comment extraction fails
        """
        try:
            # Replace MoreComments objects with actual comments
            # limit=0 means "replace all MoreComments" (fetches all comments)
            logger.debug(f"Extracting comments from submission {submission.id}")
            submission.comments.replace_more(limit=0)

            # Flatten comment tree to list
            all_comments = submission.comments.list()

            # Sort by score if requested
            if sort_by_score and limit:
                # Sort comments by score (descending)
                all_comments = sorted(all_comments, key=lambda c: c.score, reverse=True)
                logger.debug(f"Sorted {len(all_comments)} comments by score")

            # Apply limit if specified
            if limit:
                all_comments = all_comments[:limit]

            logger.debug(f"Extracted {len(all_comments)} comments from submission {submission.id}")

            return all_comments

        except PRAWException as e:
            logger.error(f"Failed to extract comments from submission {submission.id}: {e}")
            raise RedditAPIError(
                f"Unable to extract comments from submission {submission.id}: {e}\n"
                f"The submission object may be incomplete or comments may be unavailable."
            ) from e

    def get_post(self, post_id: str):
        """
        Fetch a single post by ID

        Args:
            post_id: Reddit post ID (without t3_ prefix)

        Returns:
            PRAW Submission object

        Raises:
            RedditAPIError: If post doesn't exist or API error occurs
        """
        try:
            submission = self.reddit.submission(id=post_id)
            # Access an attribute to trigger fetch
            _ = submission.title
            logger.debug(f"Fetched post {post_id}")
            return submission

        except PRAWException as e:
            logger.error(f"Failed to fetch post {post_id}: {e}")
            raise RedditAPIError(
                f"Unable to fetch post {post_id}: {e}\n"
                f"The post may have been deleted or does not exist."
            ) from e

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
