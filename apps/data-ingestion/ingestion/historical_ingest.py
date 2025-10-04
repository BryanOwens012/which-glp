"""
Historical Reddit ingestion for top posts from the past year

This script fetches the top 100 posts from the past year for each Tier 1 subreddit,
along with the top 20 comments for each post. Data is:
- Batch inserted to Supabase database
- Backed up locally to JSON files for safety
- Rate-limited to avoid API bans

Usage:
    python -m reddit_ingestion.historical_ingest
    python -m reddit_ingestion.historical_ingest --subreddit Ozempic  # Single subreddit
    python -m reddit_ingestion.historical_ingest --posts 50 --comments 10  # Custom limits
"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import logging

from shared.config import setup_logger
from shared.database import Database
from ingestion.client import RedditClient
from ingestion.parser import parse_post, parse_comment, validate_post_data, validate_comment_data

# Initialize logger
logger = setup_logger()

# Tier 1 subreddits to monitor (from AGENTS.md)
TIER_1_SUBREDDITS = [
    "Ozempic",
    "Mounjaro",
    "Wegovy",
    "zepbound",
    "semaglutide",
    "tirzepatidecompound"
]

# Default limits
DEFAULT_POSTS_PER_SUBREDDIT = 100
DEFAULT_COMMENTS_PER_POST = 20

# Rate limiting delays (in seconds)
DELAY_BETWEEN_SUBREDDITS = 3  # 3 seconds between subreddits
DELAY_BETWEEN_POSTS = 0.5  # 0.5 seconds between fetching comments for each post
DELAY_AFTER_API_ERROR = 10  # 10 seconds after an API error


class LocalBackup:
    """
    Handle local JSON backup of ingested data

    Stores data in backup/ directory with timestamp-based filenames
    """

    def __init__(self, backup_dir: Path = None):
        """
        Initialize local backup handler

        Args:
            backup_dir: Directory for backups (default: monorepo_root/backups/ingestion/)
        """
        if backup_dir is None:
            # Default: monorepo_root/backups/ingestion
            # From: apps/data-ingestion/ingestion/historical_ingest.py
            # To:   backups/ingestion
            backup_dir = Path(__file__).parent.parent.parent.parent / "backups" / "ingestion"

        self.backup_dir = backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Create timestamped subdirectory for this run
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = self.backup_dir / f"historical_run_{timestamp}"
        self.run_dir.mkdir(exist_ok=True)

        logger.info(f"Local backup directory: {self.run_dir}")

    def save_posts(self, subreddit: str, posts_data: List[Dict[str, Any]]):
        """
        Save posts to local JSON file

        Args:
            subreddit: Subreddit name
            posts_data: List of parsed post dictionaries
        """
        if not posts_data:
            return

        filename = self.run_dir / f"{subreddit}_posts.json"

        # Convert datetime objects to ISO format strings for JSON serialization
        serializable_posts = []
        for post in posts_data:
            post_copy = post.copy()
            if 'created_at' in post_copy:
                post_copy['created_at'] = post_copy['created_at'].isoformat()
            serializable_posts.append(post_copy)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(serializable_posts, f, indent=2, ensure_ascii=False)

        logger.info(f"Backed up {len(posts_data)} posts to {filename}")

    def save_comments(self, subreddit: str, comments_data: List[Dict[str, Any]]):
        """
        Save comments to local JSON file

        Args:
            subreddit: Subreddit name
            comments_data: List of parsed comment dictionaries
        """
        if not comments_data:
            return

        filename = self.run_dir / f"{subreddit}_comments.json"

        # Convert datetime objects to ISO format strings for JSON serialization
        serializable_comments = []
        for comment in comments_data:
            comment_copy = comment.copy()
            if 'created_at' in comment_copy:
                comment_copy['created_at'] = comment_copy['created_at'].isoformat()
            serializable_comments.append(comment_copy)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(serializable_comments, f, indent=2, ensure_ascii=False)

        logger.info(f"Backed up {len(comments_data)} comments to {filename}")

    def save_summary(self, summary: Dict[str, Any]):
        """
        Save ingestion summary to JSON file

        Args:
            summary: Dictionary with run statistics
        """
        filename = self.run_dir / "summary.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved ingestion summary to {filename}")


def ingest_subreddit_historical(
    reddit: RedditClient,
    db: Database,
    backup: LocalBackup,
    subreddit_name: str,
    posts_limit: int = DEFAULT_POSTS_PER_SUBREDDIT,
    comments_limit: int = DEFAULT_COMMENTS_PER_POST
) -> Dict[str, int]:
    """
    Ingest top posts from past year and their top comments from a single subreddit

    Args:
        reddit: Reddit client instance
        db: Database instance
        backup: LocalBackup instance
        subreddit_name: Name of subreddit (without r/ prefix)
        posts_limit: Maximum posts to fetch (top by score)
        comments_limit: Maximum comments per post (top by score)

    Returns:
        Dictionary with counts: {posts_fetched, posts_inserted, comments_fetched, comments_inserted}
    """
    logger.info("=" * 80)
    logger.info(f"Starting historical ingestion for r/{subreddit_name}")
    logger.info(f"Target: Top {posts_limit} posts from past year, top {comments_limit} comments each")
    logger.info("=" * 80)

    # Check if subreddit exists
    if not reddit.check_subreddit_exists(subreddit_name):
        logger.error(f"Subreddit r/{subreddit_name} not accessible, skipping")
        return {
            "posts_fetched": 0,
            "posts_inserted": 0,
            "comments_fetched": 0,
            "comments_inserted": 0
        }

    posts_fetched = 0
    posts_inserted = 0
    comments_fetched = 0
    comments_inserted = 0

    try:
        # Fetch top posts from past year
        logger.info(f"Fetching top {posts_limit} posts from past year from r/{subreddit_name}")
        posts = reddit.get_top_posts(subreddit_name, time_filter="year", limit=posts_limit)

        posts_data = []
        all_comments_data = []

        # Process each post
        for post in posts:
            try:
                # Parse post
                post_data = parse_post(post)
                posts_fetched += 1

                # Validate post data
                if not validate_post_data(post_data):
                    logger.warning(f"Invalid post data for {post.id}, skipping")
                    continue

                posts_data.append(post_data)
                logger.info(f"  [{posts_fetched}/{posts_limit}] Post {post.id}: '{post.title[:60]}...' (score: {post.score})")

                # Extract top comments directly from submission object (no additional API call)
                # This is more efficient than fetching comments separately
                logger.debug(f"Extracting top {comments_limit} comments from post {post.id}")
                comments = reddit.extract_comments_from_submission(post, limit=comments_limit, sort_by_score=True)

                post_comments_count = 0
                for comment in comments:
                    try:
                        comment_data = parse_comment(comment, post.id)
                        comments_fetched += 1
                        post_comments_count += 1

                        # Validate comment data
                        if not validate_comment_data(comment_data):
                            logger.warning(f"Invalid comment data for {comment.id}, skipping")
                            continue

                        all_comments_data.append(comment_data)

                    except Exception as e:
                        logger.error(f"Error parsing comment {getattr(comment, 'id', 'unknown')}: {e}")
                        continue

                logger.info(f"    -> Extracted {post_comments_count} comments from post {post.id}")

                # Rate limiting: brief pause between posts (reduced since we're making fewer API calls now)
                time.sleep(DELAY_BETWEEN_POSTS)

            except Exception as e:
                logger.error(f"Error processing post {getattr(post, 'id', 'unknown')}: {e}")
                # Wait longer after error
                time.sleep(DELAY_AFTER_API_ERROR)
                continue

        # Save to local backup first (before database insertion)
        logger.info(f"Backing up data locally before database insertion")
        backup.save_posts(subreddit_name, posts_data)
        backup.save_comments(subreddit_name, all_comments_data)

        # Batch insert posts to database
        if posts_data:
            logger.info(f"Inserting {len(posts_data)} posts to database")
            posts_inserted = db.insert_posts_batch(posts_data)
            logger.info(f"✓ Inserted {posts_inserted} posts (duplicates skipped: {len(posts_data) - posts_inserted})")

        # Batch insert comments to database
        if all_comments_data:
            logger.info(f"Inserting {len(all_comments_data)} comments to database")
            comments_inserted = db.insert_comments_batch(all_comments_data)
            logger.info(f"✓ Inserted {comments_inserted} comments (duplicates skipped: {len(all_comments_data) - comments_inserted})")

        logger.info("=" * 80)
        logger.info(f"Completed r/{subreddit_name}:")
        logger.info(f"  Posts: {posts_fetched} fetched, {posts_inserted} inserted")
        logger.info(f"  Comments: {comments_fetched} fetched, {comments_inserted} inserted")
        logger.info("=" * 80)

        return {
            "posts_fetched": posts_fetched,
            "posts_inserted": posts_inserted,
            "comments_fetched": comments_fetched,
            "comments_inserted": comments_inserted
        }

    except Exception as e:
        logger.error(f"Error ingesting r/{subreddit_name}: {e}")
        return {
            "posts_fetched": posts_fetched,
            "posts_inserted": posts_inserted,
            "comments_fetched": comments_fetched,
            "comments_inserted": comments_inserted
        }


def run_historical_ingestion(
    subreddits: List[str] = None,
    posts_limit: int = DEFAULT_POSTS_PER_SUBREDDIT,
    comments_limit: int = DEFAULT_COMMENTS_PER_POST
):
    """
    Run historical ingestion for top posts from past year

    Args:
        subreddits: List of subreddit names (defaults to all Tier 1)
        posts_limit: Number of top posts to fetch per subreddit
        comments_limit: Number of top comments to fetch per post
    """
    if subreddits is None:
        subreddits = TIER_1_SUBREDDITS

    start_time = time.time()
    logger.info("=" * 80)
    logger.info("HISTORICAL INGESTION - TOP POSTS FROM PAST YEAR")
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Subreddits: {', '.join(subreddits)}")
    logger.info(f"Posts per subreddit: {posts_limit} (top by score)")
    logger.info(f"Comments per post: {comments_limit} (top by score)")
    logger.info("=" * 80)

    try:
        # Initialize clients
        logger.info("Initializing Reddit client, database connection, and local backup")
        reddit = RedditClient()
        db = Database()
        backup = LocalBackup()

        # Track totals across all subreddits
        total_posts_fetched = 0
        total_posts_inserted = 0
        total_comments_fetched = 0
        total_comments_inserted = 0

        subreddit_results = {}

        # Process each subreddit
        for i, subreddit in enumerate(subreddits, 1):
            logger.info(f"\n[{i}/{len(subreddits)}] Processing r/{subreddit}")

            try:
                result = ingest_subreddit_historical(
                    reddit, db, backup, subreddit,
                    posts_limit=posts_limit,
                    comments_limit=comments_limit
                )

                total_posts_fetched += result["posts_fetched"]
                total_posts_inserted += result["posts_inserted"]
                total_comments_fetched += result["comments_fetched"]
                total_comments_inserted += result["comments_inserted"]

                subreddit_results[subreddit] = result

                # Rate limiting: pause between subreddits to be respectful to API
                if i < len(subreddits):  # Don't wait after last subreddit
                    logger.info(f"Waiting {DELAY_BETWEEN_SUBREDDITS} seconds before next subreddit...")
                    time.sleep(DELAY_BETWEEN_SUBREDDITS)

            except Exception as e:
                logger.error(f"Failed to ingest r/{subreddit}: {e}")
                subreddit_results[subreddit] = {
                    "posts_fetched": 0,
                    "posts_inserted": 0,
                    "comments_fetched": 0,
                    "comments_inserted": 0,
                    "error": str(e)
                }
                continue

        # Close database connection
        db.close()

        # Calculate elapsed time
        elapsed = time.time() - start_time
        elapsed_minutes = elapsed / 60

        # Save summary to backup
        summary = {
            "run_timestamp": datetime.now().isoformat(),
            "elapsed_seconds": elapsed,
            "elapsed_minutes": elapsed_minutes,
            "subreddits": subreddits,
            "posts_limit": posts_limit,
            "comments_limit": comments_limit,
            "totals": {
                "posts_fetched": total_posts_fetched,
                "posts_inserted": total_posts_inserted,
                "comments_fetched": total_comments_fetched,
                "comments_inserted": total_comments_inserted
            },
            "by_subreddit": subreddit_results
        }
        backup.save_summary(summary)

        # Print final summary
        logger.info("\n" + "=" * 80)
        logger.info("HISTORICAL INGESTION COMPLETED")
        logger.info("=" * 80)
        logger.info(f"Total time: {elapsed:.1f} seconds ({elapsed_minutes:.1f} minutes)")
        logger.info(f"Subreddits processed: {len(subreddits)}")
        logger.info(f"")
        logger.info(f"POSTS:")
        logger.info(f"  Fetched: {total_posts_fetched}")
        logger.info(f"  Inserted: {total_posts_inserted}")
        logger.info(f"  Duplicates skipped: {total_posts_fetched - total_posts_inserted}")
        logger.info(f"")
        logger.info(f"COMMENTS:")
        logger.info(f"  Fetched: {total_comments_fetched}")
        logger.info(f"  Inserted: {total_comments_inserted}")
        logger.info(f"  Duplicates skipped: {total_comments_fetched - total_comments_inserted}")
        logger.info(f"")
        logger.info(f"Local backup saved to: {backup.run_dir}")
        logger.info("=" * 80)

        return summary

    except Exception as e:
        logger.error(f"Fatal error during historical ingestion: {e}")
        raise


def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description="Historical ingestion: fetch top posts from past year with top comments"
    )
    parser.add_argument(
        "--subreddit",
        type=str,
        help="Single subreddit to ingest (default: all Tier 1 subreddits)"
    )
    parser.add_argument(
        "--posts",
        type=int,
        default=DEFAULT_POSTS_PER_SUBREDDIT,
        help=f"Number of top posts to fetch per subreddit (default: {DEFAULT_POSTS_PER_SUBREDDIT})"
    )
    parser.add_argument(
        "--comments",
        type=int,
        default=DEFAULT_COMMENTS_PER_POST,
        help=f"Number of top comments to fetch per post (default: {DEFAULT_COMMENTS_PER_POST})"
    )

    args = parser.parse_args()

    # Determine which subreddits to process
    if args.subreddit:
        subreddits = [args.subreddit]
    else:
        subreddits = TIER_1_SUBREDDITS

    # Run ingestion
    run_historical_ingestion(
        subreddits=subreddits,
        posts_limit=args.posts,
        comments_limit=args.comments
    )


if __name__ == "__main__":
    main()
