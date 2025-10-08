#!/usr/bin/env python3
"""
User demographics analyzer for Reddit users.

This script:
1. Fetches unique usernames from reddit_posts table
2. Uses PRAW to get last 20 posts + 20 comments per user
3. Sends to GLM-4.5-Air for demographic extraction
4. Inserts results to reddit_users table
"""

import sys
import os
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.database import DatabaseManager
from shared.config import get_logger
from glm_client import get_client
from prompts import build_user_prompt
from schema import UserDemographics

# Import PRAW
try:
    import praw
    from praw.exceptions import PRAWException
except ImportError:
    print("ERROR: praw not installed. Run: pip install praw")
    sys.exit(1)

logger = get_logger(__name__)


class RedditUserAnalyzer:
    """
    Analyzes Reddit users to extract demographic information.

    Uses PRAW to fetch user history and GLM-4.5-Air to extract demographics.
    """

    def __init__(self):
        """Initialize analyzer with database and API clients."""
        self.db = DatabaseManager()
        self.glm_client = get_client()
        self.reddit = self._init_reddit()

        logger.info("User analyzer initialized")

    def _init_reddit(self) -> praw.Reddit:
        """Initialize PRAW Reddit instance."""
        try:
            from dotenv import load_dotenv
            env_path = Path(__file__).resolve().parents[2] / ".env"
            load_dotenv(env_path)

            reddit = praw.Reddit(
                client_id=os.getenv("REDDIT_API_APP_ID"),
                client_secret=os.getenv("REDDIT_API_APP_SECRET"),
                user_agent=os.getenv("REDDIT_API_APP_NAME"),
            )

            logger.info("PRAW initialized successfully")
            return reddit

        except Exception as e:
            logger.error(f"Failed to initialize PRAW: {e}")
            raise

    def get_unanalyzed_usernames(self, limit: Optional[int] = None) -> List[str]:
        """
        Get usernames from reddit_posts that haven't been analyzed yet.

        Args:
            limit: Maximum number of usernames to return

        Returns:
            List of usernames (without u/ prefix)
        """
        query = """
            SELECT DISTINCT author
            FROM reddit_posts
            WHERE author NOT IN (
                SELECT username FROM reddit_users
            )
            AND author IS NOT NULL
            AND author != '[deleted]'
            AND author != 'AutoModerator'
            ORDER BY author
        """

        # Get all distinct authors from reddit_posts
        posts_query = self.db.client.table('reddit_posts') \
            .select('author') \
            .not_.is_('author', 'null') \
            .neq('author', '[deleted]') \
            .neq('author', 'AutoModerator')

        posts_response = posts_query.execute()
        all_authors = {post['author'] for post in (posts_response.data if posts_response.data else [])}

        # Get already analyzed users from reddit_users
        users_response = self.db.client.table('reddit_users').select('username').execute()
        analyzed_users = {user['username'] for user in (users_response.data if users_response.data else [])}

        # Get unanalyzed users
        unanalyzed = sorted(list(all_authors - analyzed_users))

        # Apply limit if specified
        if limit:
            unanalyzed = unanalyzed[:limit]

        logger.info(f"Found {len(unanalyzed)} unanalyzed users")
        return unanalyzed

    def fetch_user_history(
        self,
        username: str,
        posts_limit: int = 20,
        comments_limit: int = 20
    ) -> tuple[List[Dict], List[Dict]]:
        """
        Fetch user's recent posts and comments from Reddit.

        Args:
            username: Reddit username (without u/ prefix)
            posts_limit: Number of recent posts to fetch
            comments_limit: Number of recent comments to fetch

        Returns:
            Tuple of (posts_list, comments_list)
        """
        posts = []
        comments = []

        try:
            redditor = self.reddit.redditor(username)

            # Fetch posts
            for submission in redditor.submissions.new(limit=posts_limit):
                posts.append({
                    'title': submission.title,
                    'body': submission.selftext or '',
                })

            # Fetch comments
            for comment in redditor.comments.new(limit=comments_limit):
                comments.append({
                    'body': comment.body or '',
                })

            logger.info(f"Fetched {len(posts)} posts, {len(comments)} comments for u/{username}")

            return posts, comments

        except PRAWException as e:
            logger.error(f"PRAW error fetching u/{username}: {e}")
            return [], []
        except Exception as e:
            logger.error(f"Error fetching u/{username}: {e}")
            return [], []

    def analyze_user(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Analyze a single user and extract demographics.

        Args:
            username: Reddit username

        Returns:
            Dictionary with user data for database insertion, or None if failed
        """
        logger.info(f"Analyzing u/{username}...")

        # Fetch user history
        posts, comments = self.fetch_user_history(username)

        if not posts and not comments:
            logger.warning(f"No content found for u/{username}, skipping")
            return None

        # Build prompt
        prompt = build_user_prompt(username, posts, comments)

        # Extract demographics with GLM
        try:
            demographics, metadata = self.glm_client.extract_demographics(prompt)

            # Build database row
            user_data = {
                'username': username,
                'height_inches': demographics.height_inches,
                'start_weight_lbs': demographics.start_weight_lbs,
                'end_weight_lbs': demographics.end_weight_lbs,
                'state': demographics.state,
                'country': demographics.country,
                'age': demographics.age,
                'sex': demographics.sex,
                'comorbidities': demographics.comorbidities,
                'has_insurance': demographics.has_insurance,
                'insurance_provider': demographics.insurance_provider,
                'analyzed_at': datetime.now(),
                'post_count': len(posts),
                'comment_count': len(comments),
                'confidence_score': demographics.confidence_score,
                'model_used': metadata['model'],
                'processing_cost_usd': metadata['cost_usd'],
                'raw_response': metadata['raw_response'],
            }

            logger.info(
                f"✓ Analyzed u/{username} - "
                f"Confidence: {demographics.confidence_score:.2f}, "
                f"Cost: ${metadata['cost_usd']:.6f}"
            )

            return user_data

        except Exception as e:
            logger.error(f"✗ Failed to analyze u/{username}: {e}")
            return None

    def insert_user(self, user_data: Dict[str, Any]):
        """
        Insert user demographics to database using Supabase client.

        Args:
            user_data: Dictionary with user data
        """
        # Ensure comorbidities is a list (not None)
        if not user_data.get('comorbidities'):
            user_data['comorbidities'] = []

        # Convert datetime objects to ISO format strings for JSON serialization
        if user_data.get('analyzed_at') and hasattr(user_data['analyzed_at'], 'isoformat'):
            user_data['analyzed_at'] = user_data['analyzed_at'].isoformat()

        # Use Supabase upsert (automatically handles conflicts)
        try:
            response = self.db.client.table('reddit_users').upsert(
                user_data,
                on_conflict='username'
            ).execute()

            logger.info(f"✓ Inserted u/{user_data['username']} to database")
        except Exception as e:
            logger.error(f"✗ Failed to insert u/{user_data['username']}: {e}")
            raise

    def run(self, limit: Optional[int] = None, rate_limit_delay: float = 2.0):
        """
        Run the full user analysis pipeline.

        Args:
            limit: Maximum number of users to analyze
            rate_limit_delay: Delay in seconds between users (to avoid rate limits)
        """
        logger.info("=" * 60)
        logger.info("USER DEMOGRAPHICS ANALYSIS PIPELINE")
        logger.info("=" * 60)

        # Get unanalyzed usernames
        usernames = self.get_unanalyzed_usernames(limit=limit)

        if not usernames:
            logger.info("No unanalyzed users found. Exiting.")
            return

        logger.info(f"Processing {len(usernames)} users...")

        # Process each user
        total_cost = 0.0
        success_count = 0
        failed_count = 0

        for i, username in enumerate(usernames, 1):
            logger.info(f"\n[{i}/{len(usernames)}] Processing u/{username}...")

            # Analyze user
            user_data = self.analyze_user(username)

            if user_data:
                # Insert to database
                try:
                    self.insert_user(user_data)
                    success_count += 1
                    total_cost += user_data['processing_cost_usd']
                except Exception as e:
                    logger.error(f"Failed to insert u/{username}: {e}")
                    failed_count += 1
            else:
                failed_count += 1

            # Rate limiting
            if i < len(usernames):
                logger.debug(f"Waiting {rate_limit_delay}s before next user...")
                time.sleep(rate_limit_delay)

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("ANALYSIS COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Total users processed: {len(usernames)}")
        logger.info(f"Successful: {success_count}")
        logger.info(f"Failed: {failed_count}")
        logger.info(f"Total cost: ${total_cost:.4f}")
        logger.info(f"Average cost per user: ${total_cost / success_count:.6f}" if success_count > 0 else "N/A")
        logger.info("=" * 60)


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze Reddit users to extract demographic information"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of users to analyze"
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=2.0,
        help="Delay in seconds between users (default: 2.0)"
    )

    args = parser.parse_args()

    analyzer = RedditUserAnalyzer()

    try:
        analyzer.run(limit=args.limit, rate_limit_delay=args.rate_limit)
    except KeyboardInterrupt:
        logger.warning("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
