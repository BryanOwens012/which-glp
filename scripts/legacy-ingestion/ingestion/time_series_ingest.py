#!/usr/bin/env python3
"""
Time-Series Reddit Ingestion for GLP-1 Subreddits

Fetches posts evenly distributed across time periods to enable trend analysis.
Unlike historical_ingest.py which fetches "top posts from past year",
this script samples posts from each month to avoid popularity bias.

Usage:
    cd /Users/bryan/Github/which-glp
    python3 -m reddit_ingestion.time_series_ingest --subreddit Ozempic --months 12 --posts-per-month 30

This will fetch ~30 posts from each of the past 12 months, giving you
360 posts distributed evenly for time-series analysis.
"""

import os
import sys
import time
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.client import RedditClient
from ingestion.parser import parse_post, parse_comment
from shared.database import Database
from shared.config import setup_logger, get_backup_dir

logger = setup_logger(__name__)

# Rate limiting delays
DELAY_BETWEEN_MONTHS = 2  # seconds between fetching different time periods
DELAY_BETWEEN_COMMENTS = 0.5  # seconds between comment fetches
RETRY_DELAY = 10  # seconds to wait after API errors


def get_month_boundaries(months_back: int) -> List[tuple]:
    """
    Generate start/end timestamps for each month going back N months.

    Args:
        months_back: Number of months to go back from today

    Returns:
        List of (start_timestamp, end_timestamp) tuples for each month
    """
    boundaries = []
    now = datetime.now()

    for i in range(months_back):
        # Calculate the first day of the target month
        target_month = now.month - i
        target_year = now.year

        while target_month <= 0:
            target_month += 12
            target_year -= 1

        # First day of the month
        month_start = datetime(target_year, target_month, 1)

        # Last day of the month
        if target_month == 12:
            month_end = datetime(target_year + 1, 1, 1) - timedelta(seconds=1)
        else:
            month_end = datetime(target_year, target_month + 1, 1) - timedelta(seconds=1)

        boundaries.append((
            int(month_start.timestamp()),
            int(month_end.timestamp()),
            month_start.strftime("%Y-%m")
        ))

    return boundaries


def fetch_posts_for_time_period(
    reddit: RedditClient,
    subreddit: str,
    start_ts: int,
    end_ts: int,
    target_count: int
) -> List:
    """
    Fetch posts from a specific time period using Reddit's search.

    Reddit doesn't have a direct "posts between X and Y" API, so we use
    a combination of strategies:
    1. Use subreddit.new() and filter by timestamp
    2. Keep fetching until we have enough posts in the time range

    Args:
        reddit: RedditClient instance
        subreddit: Subreddit name
        start_ts: Start timestamp (Unix epoch)
        end_ts: End timestamp (Unix epoch)
        target_count: Target number of posts to fetch

    Returns:
        List of PRAW submission objects
    """
    logger.info(f"Fetching ~{target_count} posts from {datetime.fromtimestamp(start_ts).strftime('%Y-%m-%d')} to {datetime.fromtimestamp(end_ts).strftime('%Y-%m-%d')}")

    posts_in_range = []
    seen_ids = set()

    try:
        subreddit_obj = reddit.reddit.subreddit(subreddit)

        # Fetch new posts (chronological) and filter by timestamp
        # We'll fetch more than needed to account for filtering
        fetch_limit = target_count * 3  # Fetch 3x to account for date filtering

        for post in subreddit_obj.new(limit=fetch_limit):
            post_time = int(post.created_utc)

            # Skip if we've seen this post
            if post.id in seen_ids:
                continue

            # Check if post is in our target time range
            if start_ts <= post_time <= end_ts:
                posts_in_range.append(post)
                seen_ids.add(post.id)

                # Stop if we have enough
                if len(posts_in_range) >= target_count:
                    break

            # If we're past the end date, stop searching
            elif post_time < start_ts:
                break

        logger.info(f"Found {len(posts_in_range)} posts in time range")
        return posts_in_range

    except Exception as e:
        logger.error(f"Error fetching posts for time period: {e}")
        return posts_in_range


def ingest_time_series(
    subreddit_name: str,
    months_back: int = 12,
    posts_per_month: int = 30,
    comments_per_post: int = 20
):
    """
    Main time-series ingestion function.

    Fetches posts evenly distributed across N months for trend analysis.

    Args:
        subreddit_name: Name of subreddit (without r/ prefix)
        months_back: Number of months to go back from today
        posts_per_month: Target number of posts per month
        comments_per_post: Number of top comments per post
    """
    logger.info("=" * 80)
    logger.info("TIME-SERIES INGESTION - EVENLY SAMPLED POSTS FOR TREND ANALYSIS")
    logger.info("=" * 80)
    logger.info(f"Subreddit: r/{subreddit_name}")
    logger.info(f"Time period: Past {months_back} months")
    logger.info(f"Target: ~{posts_per_month} posts per month")
    logger.info(f"Comments: Top {comments_per_post} per post")
    logger.info(f"Total expected posts: ~{months_back * posts_per_month}")
    logger.info("=" * 80)

    # Initialize clients
    reddit = RedditClient()
    db = Database()

    # Get month boundaries
    month_boundaries = get_month_boundaries(months_back)

    all_posts_data = []
    all_comments_data = []

    # Fetch posts for each month
    for start_ts, end_ts, month_label in month_boundaries:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing {month_label}")
        logger.info(f"{'='*60}")

        # Fetch posts for this month
        posts = fetch_posts_for_time_period(
            reddit, subreddit_name, start_ts, end_ts, posts_per_month
        )

        if not posts:
            logger.warning(f"No posts found for {month_label}, skipping")
            continue

        # Parse posts
        month_posts_data = []
        for post in posts:
            try:
                post_data = parse_post(post)
                month_posts_data.append(post_data)
                logger.debug(f"Parsed post: {post.id} from {datetime.fromtimestamp(post.created_utc).strftime('%Y-%m-%d')}")
            except Exception as e:
                logger.error(f"Error parsing post {post.id}: {e}")
                continue

        all_posts_data.extend(month_posts_data)

        # Fetch comments for posts in this month
        logger.info(f"Fetching top {comments_per_post} comments for {len(month_posts_data)} posts")

        month_comments_data = []
        for i, post in enumerate(posts, 1):
            try:
                # Fetch top comments
                post.comment_sort = 'top'
                post.comments.replace_more(limit=0)  # Don't expand "load more" comments
                top_comments = post.comments[:comments_per_post]

                # Parse comments
                for comment in top_comments:
                    try:
                        comment_data = parse_comment(comment, post.id)
                        month_comments_data.append(comment_data)
                    except Exception as e:
                        logger.error(f"Error parsing comment {comment.id}: {e}")
                        continue

                logger.debug(f"[{i}/{len(posts)}] Fetched {len(top_comments)} comments for post {post.id}")

                # Rate limiting
                time.sleep(DELAY_BETWEEN_COMMENTS)

            except Exception as e:
                logger.error(f"Error fetching comments for post {post.id}: {e}")
                continue

        all_comments_data.extend(month_comments_data)

        logger.info(f"Month {month_label}: {len(month_posts_data)} posts, {len(month_comments_data)} comments")

        # Rate limiting between months
        time.sleep(DELAY_BETWEEN_MONTHS)

    # Insert into database
    logger.info("\n" + "=" * 80)
    logger.info("DATABASE INSERTION")
    logger.info("=" * 80)

    if all_posts_data:
        logger.info(f"Inserting {len(all_posts_data)} posts...")
        posts_inserted = db.insert_posts_batch(all_posts_data)
        logger.info(f"✓ Inserted {posts_inserted} new posts (duplicates skipped)")
    else:
        logger.warning("No posts to insert")

    if all_comments_data:
        logger.info(f"Inserting {len(all_comments_data)} comments...")
        comments_inserted = db.insert_comments_batch(all_comments_data)
        logger.info(f"✓ Inserted {comments_inserted} new comments (duplicates skipped)")
    else:
        logger.warning("No comments to insert")

    # Create backup
    backup_dir = get_backup_dir('ingestion') / f"time_series_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{subreddit_name}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    import json

    # Save posts
    posts_file = backup_dir / "posts.json"
    with open(posts_file, 'w') as f:
        json.dump(all_posts_data, f, indent=2, default=str)
    logger.info(f"✓ Backed up posts to: {posts_file}")

    # Save comments
    comments_file = backup_dir / "comments.json"
    with open(comments_file, 'w') as f:
        json.dump(all_comments_data, f, indent=2, default=str)
    logger.info(f"✓ Backed up comments to: {comments_file}")

    # Save summary
    summary = {
        'subreddit': subreddit_name,
        'months_back': months_back,
        'posts_per_month_target': posts_per_month,
        'comments_per_post': comments_per_post,
        'total_posts_fetched': len(all_posts_data),
        'total_comments_fetched': len(all_comments_data),
        'posts_inserted': posts_inserted if all_posts_data else 0,
        'comments_inserted': comments_inserted if all_comments_data else 0,
        'timestamp': datetime.now().isoformat(),
        'month_breakdown': []
    }

    # Add per-month breakdown
    for start_ts, end_ts, month_label in month_boundaries:
        month_posts = [p for p in all_posts_data
                      if start_ts <= p['created_at'].timestamp() <= end_ts]
        summary['month_breakdown'].append({
            'month': month_label,
            'posts': len(month_posts),
            'start_date': datetime.fromtimestamp(start_ts).isoformat(),
            'end_date': datetime.fromtimestamp(end_ts).isoformat()
        })

    summary_file = backup_dir / "summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    logger.info(f"✓ Saved summary to: {summary_file}")

    # Final summary
    logger.info("\n" + "=" * 80)
    logger.info("TIME-SERIES INGESTION COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Subreddit: r/{subreddit_name}")
    logger.info(f"Time period: {months_back} months")
    logger.info(f"Total posts fetched: {len(all_posts_data)}")
    logger.info(f"Total comments fetched: {len(all_comments_data)}")
    logger.info(f"Posts inserted: {posts_inserted if all_posts_data else 0}")
    logger.info(f"Comments inserted: {comments_inserted if all_comments_data else 0}")
    logger.info(f"Backup location: {backup_dir}")
    logger.info("=" * 80)

    db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Fetch Reddit posts evenly across time periods for trend analysis"
    )
    parser.add_argument(
        "--subreddit",
        required=True,
        help="Subreddit name (without r/ prefix)"
    )
    parser.add_argument(
        "--months",
        type=int,
        default=12,
        help="Number of months to go back (default: 12)"
    )
    parser.add_argument(
        "--posts-per-month",
        type=int,
        default=30,
        help="Target number of posts per month (default: 30)"
    )
    parser.add_argument(
        "--comments",
        type=int,
        default=20,
        help="Number of top comments per post (default: 20)"
    )

    args = parser.parse_args()

    try:
        ingest_time_series(
            subreddit_name=args.subreddit,
            months_back=args.months,
            posts_per_month=args.posts_per_month,
            comments_per_post=args.comments
        )
    except KeyboardInterrupt:
        logger.info("\n\nIngestion interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
