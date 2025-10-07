"""
Weekly Reddit ingestion with mixed sorting methods

This script fetches posts from the past week using multiple sorting methods
to reduce bias and capture diverse perspectives:
- Top posts (popular, high engagement)
- New posts (recent, less filtered by votes)
- Controversial posts (edge cases, strong opinions)

Usage:
    python -m ingestion.weekly_ingest
    python -m ingestion.weekly_ingest --subreddit Ozempic  # Single subreddit
    python -m ingestion.weekly_ingest --top 100 --new 50 --controversial 25  # Custom limits
"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Set
import logging

from shared.config import setup_logger, get_backup_dir
from shared.database import Database
from ingestion.client import RedditClient
from ingestion.parser import parse_post, parse_comment, validate_post_data, validate_comment_data

# Initialize logger
logger = setup_logger()

# All subreddits from TECH_SPEC.md
ALL_SUBREDDITS = {
    # Tier 1: Drug-specific subreddits
    "tier1": [
        "Ozempic",
        "Mounjaro",
        "Wegovy",
        "Zepbound",
        "semaglutide",
        "tirzepatidecompound"
    ],
    # Tier 2: General GLP-1 communities
    "tier2": [
        "glp1",
        "GLP1Agonists",
        "ozempicforweightloss",
        "WegovyWeightLoss",
        "liraglutide"
    ],
    # Tier 3: Broader weight loss communities
    "tier3": [
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
        "diabetes_t2"
    ]
}

# Default limits per sorting method
# Strategy: Run twice per week (Wed + Sun) to achieve ~150 new posts/week with better temporal coverage
DEFAULT_TOP_POSTS = 10
DEFAULT_NEW_POSTS = 75
DEFAULT_CONTROVERSIAL_POSTS = 15
DEFAULT_COMMENTS_PER_POST = 5

# Rate limiting delays (in seconds)
DELAY_BETWEEN_SUBREDDITS = 3
DELAY_BETWEEN_POSTS = 0.5
DELAY_AFTER_API_ERROR = 10


def fetch_posts_mixed_sorting(
    client: RedditClient,
    subreddit_name: str,
    top_limit: int,
    new_limit: int,
    controversial_limit: int
) -> List[Any]:
    """
    Fetch posts using multiple sorting methods and deduplicate.

    Args:
        client: RedditClient instance
        subreddit_name: Name of subreddit to fetch from
        top_limit: Number of top posts to fetch
        new_limit: Number of new posts to fetch
        controversial_limit: Number of controversial posts to fetch

    Returns:
        List of unique post objects
    """
    subreddit = client.reddit.subreddit(subreddit_name)
    seen_ids: Set[str] = set()
    unique_posts = []

    # 1. Fetch top posts from past week
    logger.info(f"Fetching {top_limit} top posts from past week...")
    try:
        for post in subreddit.top(time_filter='week', limit=top_limit):
            if post.id not in seen_ids:
                seen_ids.add(post.id)
                unique_posts.append(post)
    except Exception as e:
        logger.error(f"Error fetching top posts: {e}")

    # 2. Fetch new posts
    logger.info(f"Fetching {new_limit} new posts...")
    try:
        for post in subreddit.new(limit=new_limit):
            if post.id not in seen_ids:
                seen_ids.add(post.id)
                unique_posts.append(post)
    except Exception as e:
        logger.error(f"Error fetching new posts: {e}")

    # 3. Fetch controversial posts from past week
    logger.info(f"Fetching {controversial_limit} controversial posts from past week...")
    try:
        for post in subreddit.controversial(time_filter='week', limit=controversial_limit):
            if post.id not in seen_ids:
                seen_ids.add(post.id)
                unique_posts.append(post)
    except Exception as e:
        logger.error(f"Error fetching controversial posts: {e}")

    logger.info(f"Total unique posts: {len(unique_posts)} (from {top_limit + new_limit + controversial_limit} requested)")
    return unique_posts


def ingest_subreddit_weekly(
    client: RedditClient,
    db: Database,
    subreddit_name: str,
    top_limit: int,
    new_limit: int,
    controversial_limit: int,
    comments_per_post: int,
    backup_dir: Path
) -> Dict[str, int]:
    """
    Ingest posts and comments for a single subreddit using mixed sorting.

    Args:
        client: RedditClient instance
        db: Database instance
        subreddit_name: Name of subreddit
        top_limit: Number of top posts
        new_limit: Number of new posts
        controversial_limit: Number of controversial posts
        comments_per_post: Comments to fetch per post
        backup_dir: Directory for backup files

    Returns:
        Dict with statistics (posts_fetched, posts_inserted, comments_fetched, comments_inserted)
    """
    logger.info(f"")
    logger.info(f"{'='*80}")
    logger.info(f"Processing r/{subreddit_name}")
    logger.info(f"{'='*80}")

    stats = {
        "posts_fetched": 0,
        "posts_inserted": 0,
        "comments_fetched": 0,
        "comments_inserted": 0
    }

    # Fetch posts with mixed sorting
    posts = fetch_posts_mixed_sorting(
        client,
        subreddit_name,
        top_limit,
        new_limit,
        controversial_limit
    )
    stats["posts_fetched"] = len(posts)

    if not posts:
        logger.warning(f"No posts found for r/{subreddit_name}")
        return stats

    # Parse and validate posts
    parsed_posts = []
    for post in posts:
        try:
            post_data = parse_post(post)
            if validate_post_data(post_data):
                parsed_posts.append(post_data)
        except Exception as e:
            logger.error(f"Error parsing post {post.id}: {e}")

    # Fetch comments for each post
    all_comments = []
    for i, post in enumerate(posts, 1):
        logger.info(f"Fetching comments for post {i}/{len(posts)}: {post.id}")
        try:
            comments = client.extract_comments_from_submission(post, limit=comments_per_post, sort_by_score=True)
            for comment in comments:
                try:
                    comment_data = parse_comment(comment, post.id)
                    if validate_comment_data(comment_data):
                        all_comments.append(comment_data)
                except Exception as e:
                    logger.error(f"Error parsing comment: {e}")
        except Exception as e:
            logger.error(f"Error fetching comments for post {post.id}: {e}")

        time.sleep(DELAY_BETWEEN_POSTS)

    stats["comments_fetched"] = len(all_comments)

    # Save backups
    posts_backup_path = backup_dir / f"{subreddit_name}_posts.json"
    comments_backup_path = backup_dir / f"{subreddit_name}_comments.json"

    with open(posts_backup_path, 'w') as f:
        json.dump(parsed_posts, f, indent=2, default=str)
    logger.info(f"Backed up {len(parsed_posts)} posts to {posts_backup_path}")

    with open(comments_backup_path, 'w') as f:
        json.dump(all_comments, f, indent=2, default=str)
    logger.info(f"Backed up {len(all_comments)} comments to {comments_backup_path}")

    # Insert to database
    logger.info(f"Inserting {len(parsed_posts)} posts to database")
    stats["posts_inserted"] = db.batch_insert_posts(parsed_posts)

    logger.info(f"Inserting {len(all_comments)} comments to database")
    stats["comments_inserted"] = db.batch_insert_comments(all_comments)

    return stats


def main():
    """Main entry point for weekly ingestion."""
    parser = argparse.ArgumentParser(description="Weekly Reddit ingestion with mixed sorting")
    parser.add_argument(
        "--subreddit",
        type=str,
        help="Single subreddit to ingest (default: all subreddits)"
    )
    parser.add_argument(
        "--tier",
        type=str,
        choices=["tier1", "tier2", "tier3"],
        help="Ingest all subreddits from a specific tier"
    )
    parser.add_argument(
        "--top",
        type=int,
        default=DEFAULT_TOP_POSTS,
        help=f"Number of top posts to fetch (default: {DEFAULT_TOP_POSTS})"
    )
    parser.add_argument(
        "--new",
        type=int,
        default=DEFAULT_NEW_POSTS,
        help=f"Number of new posts to fetch (default: {DEFAULT_NEW_POSTS})"
    )
    parser.add_argument(
        "--controversial",
        type=int,
        default=DEFAULT_CONTROVERSIAL_POSTS,
        help=f"Number of controversial posts to fetch (default: {DEFAULT_CONTROVERSIAL_POSTS})"
    )
    parser.add_argument(
        "--comments",
        type=int,
        default=DEFAULT_COMMENTS_PER_POST,
        help=f"Number of comments per post (default: {DEFAULT_COMMENTS_PER_POST})"
    )

    args = parser.parse_args()

    # Determine which subreddits to process
    if args.subreddit:
        subreddits = [args.subreddit]
    elif args.tier:
        subreddits = ALL_SUBREDDITS[args.tier]
    else:
        # Default: all subreddits
        subreddits = ALL_SUBREDDITS["tier1"] + ALL_SUBREDDITS["tier2"] + ALL_SUBREDDITS["tier3"]

    logger.info(f"")
    logger.info(f"{'='*80}")
    logger.info(f"WEEKLY REDDIT INGESTION - MIXED SORTING")
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"{'='*80}")
    logger.info(f"")
    logger.info(f"Strategy:")
    logger.info(f"  - Top posts (past week): {args.top}")
    logger.info(f"  - New posts: {args.new}")
    logger.info(f"  - Controversial posts (past week): {args.controversial}")
    logger.info(f"  - Comments per post: {args.comments}")
    logger.info(f"  - Total expected unique posts per subreddit: ~{args.top + args.new + args.controversial} (after dedup)")
    logger.info(f"")
    logger.info(f"Subreddits to process: {len(subreddits)}")
    for sub in subreddits:
        logger.info(f"  - r/{sub}")
    logger.info(f"")

    # Initialize clients
    client = RedditClient()
    db = Database()

    # Create backup directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = get_backup_dir("ingestion") / f"weekly_run_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Backup directory: {backup_dir}")
    logger.info(f"")

    # Track overall stats
    overall_stats = {
        "run_timestamp": datetime.now().isoformat(),
        "top_limit": args.top,
        "new_limit": args.new,
        "controversial_limit": args.controversial,
        "comments_limit": args.comments,
        "subreddits": subreddits,
        "totals": {
            "posts_fetched": 0,
            "posts_inserted": 0,
            "comments_fetched": 0,
            "comments_inserted": 0
        },
        "by_subreddit": {}
    }

    start_time = time.time()

    # Process each subreddit
    for i, subreddit_name in enumerate(subreddits, 1):
        logger.info(f"Processing subreddit {i}/{len(subreddits)}: r/{subreddit_name}")

        try:
            stats = ingest_subreddit_weekly(
                client,
                db,
                subreddit_name,
                args.top,
                args.new,
                args.controversial,
                args.comments,
                backup_dir
            )

            # Update overall stats
            overall_stats["totals"]["posts_fetched"] += stats["posts_fetched"]
            overall_stats["totals"]["posts_inserted"] += stats["posts_inserted"]
            overall_stats["totals"]["comments_fetched"] += stats["comments_fetched"]
            overall_stats["totals"]["comments_inserted"] += stats["comments_inserted"]
            overall_stats["by_subreddit"][subreddit_name] = stats

            logger.info(f"✓ Completed r/{subreddit_name}: {stats}")

        except Exception as e:
            logger.error(f"✗ Failed r/{subreddit_name}: {e}")
            overall_stats["by_subreddit"][subreddit_name] = {
                "error": str(e),
                "posts_fetched": 0,
                "posts_inserted": 0,
                "comments_fetched": 0,
                "comments_inserted": 0
            }

        # Delay between subreddits (except after the last one)
        if i < len(subreddits):
            logger.info(f"Waiting {DELAY_BETWEEN_SUBREDDITS} seconds before next subreddit...")
            time.sleep(DELAY_BETWEEN_SUBREDDITS)

    # Calculate elapsed time
    elapsed = time.time() - start_time
    overall_stats["elapsed_seconds"] = elapsed
    overall_stats["elapsed_minutes"] = elapsed / 60

    # Save summary
    summary_path = backup_dir / "summary.json"
    with open(summary_path, 'w') as f:
        json.dump(overall_stats, f, indent=2)

    # Print summary
    logger.info(f"")
    logger.info(f"{'='*80}")
    logger.info(f"WEEKLY INGESTION SUMMARY")
    logger.info(f"{'='*80}")
    logger.info(f"Total posts fetched:    {overall_stats['totals']['posts_fetched']}")
    logger.info(f"Total posts inserted:   {overall_stats['totals']['posts_inserted']}")
    logger.info(f"Total comments fetched: {overall_stats['totals']['comments_fetched']}")
    logger.info(f"Total comments inserted: {overall_stats['totals']['comments_inserted']}")
    logger.info(f"Elapsed time: {elapsed/60:.1f} minutes")
    logger.info(f"")
    logger.info(f"Summary saved to: {summary_path}")
    logger.info(f"{'='*80}")


if __name__ == "__main__":
    main()
