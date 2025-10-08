#!/usr/bin/env python3
"""
Recent Reddit Post Ingestion (No Comments)

Fetches the 100 most recent posts from tier 1-3 subreddits.
Unlike historical_ingest.py which fetches "top" posts, this fetches "new" posts.
No comments are fetched - posts only.

Usage:
    cd /Users/bryan/Github/which-glp
    python3 -m apps.post-ingestion.recent_ingest --subreddit Ozempic
    python3 -m apps.post-ingestion.recent_ingest --all-tier1  # Process all tier 1 subreddits
"""

import os
import sys
import time
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import List

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from client import RedditClient
from parser import parse_post
from shared.database import DatabaseManager
from shared.config import setup_logger, get_backup_dir

logger = setup_logger(__name__)

# Rate limiting
DELAY_BETWEEN_SUBREDDITS = 3  # seconds
RETRY_DELAY = 10  # seconds after API errors

# Tier 1-3 subreddits from TECH_SPEC.md
TIER1_SUBREDDITS = [
    "Ozempic",
    "Mounjaro",
    "Wegovy",
    "zepbound",
    "semaglutide",
    "tirzepatidecompound",
]

TIER2_SUBREDDITS = [
    "glp1",
    "ozempicforweightloss",
    "WegovyWeightLoss",
    "liraglutide",
]

TIER3_SUBREDDITS = [
    "loseit",
    "progresspics",
    "intermittentfasting",
    "1200isplenty",
    "fasting",
    "CICO",
    "1500isplenty",
    "PCOS",
    "Brogress",
    "diabetes",
    "obesity",
    "peptides",
    "SuperMorbidlyObese",
    "diabetes_t2",
]


def ingest_recent_posts(
    subreddit_name: str,
    posts_limit: int = 100
):
    """
    Fetch recent posts from a subreddit (no comments).

    Args:
        subreddit_name: Name of subreddit (without r/ prefix)
        posts_limit: Number of recent posts to fetch (default 100)
    """
    logger.info("=" * 80)
    logger.info(f"RECENT POST INGESTION - r/{subreddit_name}")
    logger.info("=" * 80)
    logger.info(f"Fetching {posts_limit} most recent posts (NO COMMENTS)")
    logger.info("=" * 80)

    # Initialize clients
    reddit = RedditClient()
    db = DatabaseManager()

    # Fetch recent posts (sorted by new)
    logger.info(f"Fetching {posts_limit} recent posts from r/{subreddit_name}...")

    try:
        posts = reddit.get_recent_posts(subreddit_name, limit=posts_limit)
    except Exception as e:
        logger.error(f"Failed to fetch posts: {e}")
        return

    # Parse posts
    posts_data = []
    for post in posts:
        try:
            post_data = parse_post(post)
            posts_data.append(post_data)
            logger.debug(
                f"Parsed post: {post.id} - {post.title[:50]}... "
                f"({datetime.fromtimestamp(post.created_utc).strftime('%Y-%m-%d')})"
            )
        except Exception as e:
            logger.error(f"Error parsing post {post.id}: {e}")
            continue

    logger.info(f"Parsed {len(posts_data)} posts")

    # Insert posts to database
    if posts_data:
        logger.info(f"Inserting {len(posts_data)} posts to database...")
        try:
            posts_inserted = db.insert_posts_batch(posts_data)
            logger.info(f"✓ Inserted {posts_inserted} new posts (duplicates skipped)")
        except Exception as e:
            logger.error(f"Database insertion failed: {e}")
    else:
        logger.warning("No posts to insert")

    # Create backup (skip if running in Railway/ephemeral environment)
    try:
        backup_dir = get_backup_dir('post_ingestion') / f"recent_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{subreddit_name}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        import json

        # Save posts
        posts_file = backup_dir / "posts.json"
        with open(posts_file, 'w') as f:
            json.dump(posts_data, f, indent=2, default=str)
        logger.info(f"✓ Backed up posts to: {posts_file}")

        # Save summary
        summary = {
            'subreddit': subreddit_name,
            'posts_limit': posts_limit,
            'total_posts_fetched': len(posts_data),
            'posts_inserted': posts_inserted if posts_data else 0,
            'timestamp': datetime.now().isoformat(),
        }

        summary_file = backup_dir / "summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        logger.info(f"✓ Saved summary to: {summary_file}")
    except Exception as e:
        logger.warning(f"⚠️  Could not create backup (running in ephemeral environment?): {e}")

    # Final summary
    logger.info("\n" + "=" * 80)
    logger.info("INGESTION COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Subreddit: r/{subreddit_name}")
    logger.info(f"Posts fetched: {len(posts_data)}")
    logger.info(f"Posts inserted: {posts_inserted if posts_data else 0}")
    logger.info(f"Backup location: {backup_dir}")
    logger.info("=" * 80)

    db.close()


def ingest_multiple_subreddits(subreddits: List[str], posts_limit: int = 100):
    """
    Ingest recent posts from multiple subreddits.

    Args:
        subreddits: List of subreddit names
        posts_limit: Number of posts per subreddit
    """
    logger.info(f"Processing {len(subreddits)} subreddits...")

    for i, subreddit in enumerate(subreddits, 1):
        logger.info(f"\n[{i}/{len(subreddits)}] Processing r/{subreddit}...")

        try:
            ingest_recent_posts(subreddit, posts_limit)
        except Exception as e:
            logger.error(f"Failed to process r/{subreddit}: {e}")

        # Rate limiting between subreddits
        if i < len(subreddits):
            logger.info(f"Waiting {DELAY_BETWEEN_SUBREDDITS}s before next subreddit...")
            time.sleep(DELAY_BETWEEN_SUBREDDITS)

    logger.info("\n" + "=" * 80)
    logger.info("ALL SUBREDDITS PROCESSED")
    logger.info("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch recent Reddit posts (no comments) from subreddits"
    )
    parser.add_argument(
        "--subreddit",
        type=str,
        help="Single subreddit to process"
    )
    parser.add_argument(
        "--posts",
        type=int,
        default=100,
        help="Number of recent posts to fetch (default: 100)"
    )
    parser.add_argument(
        "--all-tier1",
        action="store_true",
        help="Process all tier 1 subreddits"
    )
    parser.add_argument(
        "--all-tier2",
        action="store_true",
        help="Process all tier 2 subreddits"
    )
    parser.add_argument(
        "--all-tier3",
        action="store_true",
        help="Process all tier 3 subreddits"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all tier 1-3 subreddits"
    )

    args = parser.parse_args()

    try:
        if args.all:
            subreddits = TIER1_SUBREDDITS + TIER2_SUBREDDITS + TIER3_SUBREDDITS
            ingest_multiple_subreddits(subreddits, args.posts)
        elif args.all_tier1:
            ingest_multiple_subreddits(TIER1_SUBREDDITS, args.posts)
        elif args.all_tier2:
            ingest_multiple_subreddits(TIER2_SUBREDDITS, args.posts)
        elif args.all_tier3:
            ingest_multiple_subreddits(TIER3_SUBREDDITS, args.posts)
        elif args.subreddit:
            ingest_recent_posts(args.subreddit, args.posts)
        else:
            parser.print_help()
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("\n\nIngestion interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
