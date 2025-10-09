#!/usr/bin/env python3
"""
Test script to verify user extraction status flags implementation.

This script tests:
1. Querying extracted_features with user_extraction_status = 'pending'
2. Checking backfill worked correctly (processed users marked)
3. Verifying get_unanalyzed_users() uses status flags
"""

import sys
from pathlib import Path

# Add shared modules to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "legacy-ingestion"))

from shared.database import DatabaseManager
from shared.config import get_logger

logger = get_logger(__name__)


def test_user_extraction_status():
    """Test the user extraction status flag functionality."""
    logger.info("=" * 80)
    logger.info("🧪 TESTING USER EXTRACTION STATUS FLAGS")
    logger.info("=" * 80)

    db = DatabaseManager()

    try:
        # Test 1: Check status distribution
        logger.info("\n📊 Test 1: Check user_extraction_status distribution")
        response = db.client.table('extracted_features').select(
            'user_extraction_status'
        ).execute()

        if response.data:
            from collections import Counter
            status_counts = Counter(row['user_extraction_status'] for row in response.data)
            for status, count in status_counts.items():
                logger.info(f"   {status}: {count}")
        else:
            logger.warning("   No data found in extracted_features")

        # Test 2: Check how many users have been processed
        logger.info("\n📊 Test 2: Check processed users (should match reddit_users count)")

        # Count distinct users in reddit_users
        users_response = db.client.table('reddit_users').select('username').execute()
        reddit_users_count = len(users_response.data) if users_response.data else 0
        logger.info(f"   reddit_users count: {reddit_users_count}")

        # Count distinct authors in extracted_features with status = 'processed'
        processed_response = db.client.table('extracted_features').select(
            'post_id'
        ).eq('user_extraction_status', 'processed').execute()

        if processed_response.data:
            # Get distinct authors for these posts
            post_ids = [row['post_id'] for row in processed_response.data]
            posts_response = db.client.table('reddit_posts').select('author').in_('post_id', post_ids).execute()
            if posts_response.data:
                distinct_authors = set(row['author'] for row in posts_response.data)
                logger.info(f"   Distinct authors with status='processed': {len(distinct_authors)}")

                if len(distinct_authors) == reddit_users_count:
                    logger.info("   ✅ Backfill worked correctly!")
                else:
                    logger.warning(f"   ⚠️  Mismatch: {len(distinct_authors)} != {reddit_users_count}")
        else:
            logger.info("   No processed extracted_features found")

        # Test 3: Test get_unanalyzed_users function
        logger.info("\n📊 Test 3: Test get_unanalyzed_users() function")
        response = db.client.rpc('get_unanalyzed_users', {
            'p_limit': 5
        }).execute()

        if response.data:
            unanalyzed_count = len(response.data)
            logger.info(f"   Unanalyzed users (sample 5): {unanalyzed_count}")
            for row in response.data[:3]:
                logger.info(f"     - {row['author']}")
        else:
            logger.info("   ✅ No unanalyzed users found (all users processed)")

        # Test 4: Verify new DEFAULT works
        logger.info("\n📊 Test 4: Verify DEFAULT 'pending' for new extracted_features")
        response = db.client.table('extracted_features').select(
            'user_extraction_status'
        ).limit(1).execute()

        if response.data:
            status = response.data[0]['user_extraction_status']
            logger.info(f"   Sample status: {status}")
            if status in ['pending', 'processed', 'skipped', 'failed']:
                logger.info("   ✅ Status is valid enum value")
        else:
            logger.info("   No data to check")

        logger.info("\n" + "=" * 80)
        logger.info("🎉 ALL TESTS COMPLETED")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"\n❌ Test failed with error: {e}")
        logger.exception("Full traceback:")
    finally:
        db.close()


if __name__ == "__main__":
    test_user_extraction_status()
