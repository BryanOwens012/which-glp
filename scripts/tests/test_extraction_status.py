#!/usr/bin/env python3
"""
Test script to verify extraction status flags implementation.

This script tests:
1. Querying posts with extraction_status = 'pending'
2. Marking posts as 'skipped' with reasons
3. Marking posts as 'processed'
4. Verifying get_unprocessed_posts() only returns pending posts
"""

import sys
from pathlib import Path

# Add post-extraction app to path to import shared modules
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "post-extraction"))

from shared.database import DatabaseManager
from shared.config import get_logger

logger = get_logger(__name__)


def test_extraction_status():
    """Test the extraction status flag functionality."""
    logger.info("=" * 80)
    logger.info("🧪 TESTING EXTRACTION STATUS FLAGS")
    logger.info("=" * 80)

    db = DatabaseManager()

    try:
        # Test 1: Query initial pending posts
        logger.info("\n📊 Test 1: Query initial pending posts count")
        response = db.client.rpc('get_unprocessed_posts', {
            'p_subreddit': None,
            'p_limit': None
        }).execute()
        initial_pending = len(response.data) if response.data else 0
        logger.info(f"   Initial pending posts: {initial_pending}")

        # Test 2: Get a sample pending post
        logger.info("\n📝 Test 2: Get a sample pending post")
        response = db.client.rpc('get_unprocessed_posts', {
            'p_subreddit': None,
            'p_limit': 1
        }).execute()

        if not response.data:
            logger.warning("   ⚠️  No pending posts found - cannot test further")
            logger.info("   💡 Tip: Run post ingestion first to create test data")
            return

        test_post = response.data[0]
        post_id = test_post['post_id']
        logger.info(f"   Test post_id: {post_id}")
        logger.info(f"   Title: {test_post['title'][:60]}...")

        # Test 3: Mark post as skipped
        logger.info("\n⏭️  Test 3: Mark post as skipped")
        log_message = "test: keyword_filter: not drug-related"
        db.client.table('reddit_posts').update({
            'extraction_status': 'skipped',
            'extraction_log_message': log_message,
            'extraction_attempted_at': 'now()'
        }).eq('post_id', post_id).execute()
        logger.info(f"   ✅ Marked {post_id} as skipped")

        # Test 4: Verify post is not in unprocessed list
        logger.info("\n🔍 Test 4: Verify post is excluded from unprocessed list")
        response = db.client.rpc('get_unprocessed_posts', {
            'p_subreddit': None,
            'p_limit': None
        }).execute()
        current_pending = len(response.data) if response.data else 0
        logger.info(f"   Pending posts after skip: {current_pending}")
        logger.info(f"   Expected: {initial_pending - 1}")

        if current_pending == initial_pending - 1:
            logger.info("   ✅ Post correctly excluded from unprocessed list")
        else:
            logger.error("   ❌ Post count mismatch!")

        # Test 5: Verify we can read the log message
        logger.info("\n📖 Test 5: Query log message from database")
        response = db.client.table('reddit_posts').select(
            'post_id, extraction_status, extraction_log_message, extraction_attempted_at'
        ).eq('post_id', post_id).execute()

        if response.data:
            post_data = response.data[0]
            logger.info(f"   Status: {post_data['extraction_status']}")
            logger.info(f"   Log message: {post_data['extraction_log_message']}")
            logger.info(f"   Attempted at: {post_data['extraction_attempted_at']}")

            if post_data['extraction_status'] == 'skipped' and post_data['extraction_log_message'] == log_message:
                logger.info("   ✅ Log message correctly saved")
            else:
                logger.error("   ❌ Log message mismatch!")

        # Test 6: Mark post as processed (simulate successful extraction)
        logger.info("\n✅ Test 6: Mark post as processed")
        db.client.table('reddit_posts').update({
            'extraction_status': 'processed',
            'extraction_log_message': None,
            'extraction_attempted_at': 'now()'
        }).eq('post_id', post_id).execute()
        logger.info(f"   ✅ Marked {post_id} as processed")

        # Test 7: Verify processed post is still excluded
        logger.info("\n🔍 Test 7: Verify processed post is excluded from unprocessed list")
        response = db.client.rpc('get_unprocessed_posts', {
            'p_subreddit': None,
            'p_limit': None
        }).execute()
        final_pending = len(response.data) if response.data else 0
        logger.info(f"   Pending posts after processing: {final_pending}")
        logger.info(f"   Expected: {initial_pending - 1}")

        if final_pending == initial_pending - 1:
            logger.info("   ✅ Processed post correctly excluded from unprocessed list")
        else:
            logger.error("   ❌ Post count mismatch!")

        # Test 8: Reset post to pending for cleanup
        logger.info("\n🔄 Test 8: Reset post to pending (cleanup)")
        db.client.table('reddit_posts').update({
            'extraction_status': 'pending',
            'extraction_log_message': None,
            'extraction_attempted_at': None
        }).eq('post_id', post_id).execute()
        logger.info(f"   ✅ Reset {post_id} to pending state")

        # Final verification
        logger.info("\n✅ Test 9: Final verification")
        response = db.client.rpc('get_unprocessed_posts', {
            'p_subreddit': None,
            'p_limit': None
        }).execute()
        restored_pending = len(response.data) if response.data else 0
        logger.info(f"   Pending posts after reset: {restored_pending}")
        logger.info(f"   Expected: {initial_pending}")

        if restored_pending == initial_pending:
            logger.info("   ✅ Post successfully restored to pending state")
        else:
            logger.error("   ❌ Post count mismatch after reset!")

        logger.info("\n" + "=" * 80)
        logger.info("🎉 ALL TESTS COMPLETED")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"\n❌ Test failed with error: {e}")
        logger.exception("Full traceback:")
    finally:
        db.close()


if __name__ == "__main__":
    test_extraction_status()
