"""
Reddit ingestion scheduler

Main orchestrator that:
- Runs on a schedule (every 15 minutes by default)
- Fetches posts from Tier 1 GLP-1 subreddits
- Fetches comments for each post
- Parses data with comprehensive null handling
- Batch inserts to Supabase database
- Logs all operations

Tier 1 Subreddits:
- Ozempic
- Mounjaro
- Wegovy
- zepbound
- semaglutide
- tirzepatidecompound

Usage:
    python scheduler.py              # Run once
    python scheduler.py --schedule   # Run on schedule every 15 minutes
"""

import argparse
import time
from datetime import datetime
from typing import Dict
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from shared.config import setup_logger
from shared.database import Database
from ingestion.client import RedditClient
from ingestion.parser import parse_post, parse_comment, validate_post_data, validate_comment_data

# Initialize logger
logger = setup_logger()

# Tier 1 subreddits to monitor
TIER_1_SUBREDDITS = [
    "Ozempic",
    "Mounjaro",
    "Wegovy",
    "zepbound",
    "semaglutide",
    "tirzepatidecompound"
]

# Number of posts to fetch per subreddit
POSTS_PER_SUBREDDIT = 100


def ingest_subreddit(
    reddit: RedditClient,
    db: Database,
    subreddit_name: str,
    limit: int = POSTS_PER_SUBREDDIT
) -> Dict[str, int]:
    """
    Ingest posts and comments from a single subreddit

    Args:
        reddit: Reddit client instance
        db: Database instance
        subreddit_name: Name of subreddit (without r/ prefix)
        limit: Maximum posts to fetch

    Returns:
        Dictionary with counts: {posts_inserted, comments_inserted}
    """
    logger.info(f"Starting ingestion for r/{subreddit_name}")

    # Check if subreddit exists
    if not reddit.check_subreddit_exists(subreddit_name):
        logger.error(f"Subreddit r/{subreddit_name} not accessible, skipping")
        return {"posts_inserted": 0, "comments_inserted": 0}

    posts_inserted = 0
    comments_inserted = 0

    try:
        # Fetch recent posts
        posts = reddit.get_recent_posts(subreddit_name, limit=limit)

        posts_data = []
        all_comments_data = []

        # Process each post
        for post in posts:
            try:
                # Parse post
                post_data = parse_post(post)

                # Validate post data
                if not validate_post_data(post_data):
                    logger.warning(f"Invalid post data for {post.id}, skipping")
                    continue

                posts_data.append(post_data)

                # Fetch and parse comments for this post
                logger.debug(f"Fetching comments for post {post.id}")
                comments = reddit.get_post_comments(post.id)

                for comment in comments:
                    try:
                        comment_data = parse_comment(comment, post.id)

                        # Validate comment data
                        if not validate_comment_data(comment_data):
                            logger.warning(f"Invalid comment data for {comment.id}, skipping")
                            continue

                        all_comments_data.append(comment_data)

                    except Exception as e:
                        logger.error(f"Error parsing comment {comment.id}: {e}")
                        continue

            except Exception as e:
                logger.error(f"Error processing post {post.id}: {e}")
                continue

        # Batch insert posts
        if posts_data:
            posts_inserted = db.insert_posts_batch(posts_data)
            logger.info(f"Inserted {posts_inserted} posts from r/{subreddit_name}")

        # Batch insert comments
        if all_comments_data:
            comments_inserted = db.insert_comments_batch(all_comments_data)
            logger.info(f"Inserted {comments_inserted} comments from r/{subreddit_name}")

        return {
            "posts_inserted": posts_inserted,
            "comments_inserted": comments_inserted
        }

    except Exception as e:
        logger.error(f"Error ingesting r/{subreddit_name}: {e}")
        return {"posts_inserted": 0, "comments_inserted": 0}


def run_ingestion():
    """
    Run full ingestion cycle for all Tier 1 subreddits
    """
    start_time = time.time()
    logger.info("=" * 60)
    logger.info(f"Starting ingestion run at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    try:
        # Initialize clients
        logger.info("Initializing Reddit client and database connection")
        reddit = RedditClient()
        db = Database()

        total_posts = 0
        total_comments = 0

        # Process each subreddit
        for subreddit in TIER_1_SUBREDDITS:
            try:
                result = ingest_subreddit(reddit, db, subreddit)
                total_posts += result["posts_inserted"]
                total_comments += result["comments_inserted"]

                # Brief pause between subreddits to respect rate limits
                time.sleep(2)

            except Exception as e:
                logger.error(f"Failed to ingest r/{subreddit}: {e}")
                continue

        # Close database connection
        db.close()

        # Summary
        elapsed = time.time() - start_time
        logger.info("=" * 60)
        logger.info(f"Ingestion run completed in {elapsed:.1f} seconds")
        logger.info(f"Total posts inserted: {total_posts}")
        logger.info(f"Total comments inserted: {total_comments}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Fatal error during ingestion: {e}")
        raise


def run_scheduled(interval_minutes: int = 15):
    """
    Run ingestion on a schedule

    Args:
        interval_minutes: Minutes between each run (default: 15)
    """
    logger.info(f"Starting scheduler: running every {interval_minutes} minutes")

    scheduler = BlockingScheduler()

    # Add job with interval trigger
    scheduler.add_job(
        run_ingestion,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="reddit_ingestion",
        name="Reddit Ingestion Job",
        replace_existing=True
    )

    # Run immediately on start
    logger.info("Running initial ingestion...")
    run_ingestion()

    # Start scheduler
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped by user")
        scheduler.shutdown()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Reddit ingestion scheduler for GLP-1 subreddits"
    )
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Run on schedule (every 15 minutes) instead of once"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=15,
        help="Minutes between runs when using --schedule (default: 15)"
    )

    args = parser.parse_args()

    if args.schedule:
        run_scheduled(interval_minutes=args.interval)
    else:
        run_ingestion()


if __name__ == "__main__":
    main()
