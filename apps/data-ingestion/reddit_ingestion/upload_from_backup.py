"""
Upload Reddit data from local JSON backups to Supabase database

This script reads the JSON backup files from a historical ingestion run
and uploads them to the Supabase database.

Usage:
    python -m reddit_ingestion.upload_from_backup <backup_directory>

Example:
    python -m reddit_ingestion.upload_from_backup reddit_ingestion/backup/historical_run_20251001_010839
"""

import json
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import logging

from reddit_ingestion.config import setup_logger
from reddit_ingestion.database import Database

# Initialize logger
logger = setup_logger()


def load_posts_from_backup(backup_dir: Path, subreddit: str) -> list:
    """
    Load posts from JSON backup file

    Args:
        backup_dir: Path to backup directory
        subreddit: Subreddit name

    Returns:
        List of post dictionaries
    """
    posts_file = backup_dir / f"{subreddit}_posts.json"

    if not posts_file.exists():
        logger.warning(f"Posts file not found: {posts_file}")
        return []

    with open(posts_file, 'r', encoding='utf-8') as f:
        posts = json.load(f)

    # Convert ISO format timestamps back to datetime objects
    for post in posts:
        if 'created_at' in post and isinstance(post['created_at'], str):
            post['created_at'] = datetime.fromisoformat(post['created_at'])

    logger.info(f"Loaded {len(posts)} posts from {posts_file}")
    return posts


def load_comments_from_backup(backup_dir: Path, subreddit: str) -> list:
    """
    Load comments from JSON backup file

    Args:
        backup_dir: Path to backup directory
        subreddit: Subreddit name

    Returns:
        List of comment dictionaries
    """
    comments_file = backup_dir / f"{subreddit}_comments.json"

    if not comments_file.exists():
        logger.warning(f"Comments file not found: {comments_file}")
        return []

    with open(comments_file, 'r', encoding='utf-8') as f:
        comments = json.load(f)

    # Convert ISO format timestamps back to datetime objects
    for comment in comments:
        if 'created_at' in comment and isinstance(comment['created_at'], str):
            comment['created_at'] = datetime.fromisoformat(comment['created_at'])

    logger.info(f"Loaded {len(comments)} comments from {comments_file}")
    return comments


def upload_backup_to_database(backup_dir: Path):
    """
    Upload all data from backup directory to database

    Args:
        backup_dir: Path to backup directory containing JSON files
    """
    backup_dir = Path(backup_dir)

    if not backup_dir.exists():
        logger.error(f"Backup directory not found: {backup_dir}")
        return

    logger.info("=" * 80)
    logger.info(f"Uploading backup from: {backup_dir}")
    logger.info("=" * 80)

    # Initialize database connection
    db = Database()

    total_posts_inserted = 0
    total_comments_inserted = 0
    total_posts_duplicates = 0
    total_comments_duplicates = 0

    # Find all subreddit post files
    subreddit_files = list(backup_dir.glob("*_posts.json"))
    subreddits = [f.stem.replace("_posts", "") for f in subreddit_files]

    logger.info(f"Found data for {len(subreddits)} subreddits: {', '.join(subreddits)}")
    logger.info("")

    for subreddit in subreddits:
        logger.info(f"Processing {subreddit}...")

        try:
            # Load posts
            posts = load_posts_from_backup(backup_dir, subreddit)

            if posts:
                posts_inserted = db.insert_posts_batch(posts)
                posts_duplicates = len(posts) - posts_inserted
                total_posts_inserted += posts_inserted
                total_posts_duplicates += posts_duplicates
                logger.info(f"  ✓ {posts_inserted} posts inserted ({posts_duplicates} duplicates skipped)")

            # Load comments
            comments = load_comments_from_backup(backup_dir, subreddit)

            if comments:
                comments_inserted = db.insert_comments_batch(comments)
                comments_duplicates = len(comments) - comments_inserted
                total_comments_inserted += comments_inserted
                total_comments_duplicates += comments_duplicates
                logger.info(f"  ✓ {comments_inserted} comments inserted ({comments_duplicates} duplicates skipped)")

            logger.info("")

        except Exception as e:
            logger.error(f"Error processing {subreddit}: {e}")
            continue

    # Close database connection
    db.close()

    # Print summary
    logger.info("=" * 80)
    logger.info("UPLOAD SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Posts inserted:     {total_posts_inserted:5}")
    logger.info(f"Posts duplicates:   {total_posts_duplicates:5}")
    logger.info(f"Comments inserted:  {total_comments_inserted:5}")
    logger.info(f"Comments duplicates: {total_comments_duplicates:5}")
    logger.info("=" * 80)
    logger.info("✓ Upload complete!")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Upload Reddit data from local JSON backup to Supabase"
    )
    parser.add_argument(
        "backup_dir",
        type=str,
        help="Path to backup directory (e.g., reddit_ingestion/backup/historical_run_20251001_010839)"
    )

    args = parser.parse_args()

    upload_backup_to_database(args.backup_dir)


if __name__ == "__main__":
    main()
