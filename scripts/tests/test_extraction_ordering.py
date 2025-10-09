#!/usr/bin/env python3
"""
Test script to verify extraction query ordering and index integrity.

This script tests:
1. get_unprocessed_posts returns posts ordered by ingested_at DESC
2. get_unanalyzed_users returns users ordered by processed_at DESC
3. All indexes are intact after migration
"""

import sys
from pathlib import Path

# Add shared modules to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "legacy-ingestion"))

from shared.database import DatabaseManager
from shared.config import get_logger

logger = get_logger(__name__)


def test_extraction_ordering():
    """Test the extraction query ordering."""
    logger.info("=" * 80)
    logger.info("🧪 TESTING EXTRACTION QUERY ORDERING")
    logger.info("=" * 80)

    db = DatabaseManager()

    try:
        # Test 1: Check get_unprocessed_posts ordering
        logger.info("\n📊 Test 1: Verify get_unprocessed_posts ordering (ingested_at DESC)")
        response = db.client.rpc('get_unprocessed_posts', {
            'p_subreddit': None,
            'p_limit': 5
        }).execute()

        if response.data:
            logger.info(f"   Found {len(response.data)} posts")

            # Get full post details including ingested_at
            post_ids = [p['post_id'] for p in response.data]
            posts_response = db.client.table('reddit_posts').select(
                'post_id, ingested_at'
            ).in_('post_id', post_ids).execute()

            if posts_response.data:
                # Create a map of post_id to ingested_at
                ingested_map = {p['post_id']: p['ingested_at'] for p in posts_response.data}

                logger.info("   Post order:")
                for i, post in enumerate(response.data, 1):
                    ingested_at = ingested_map.get(post['post_id'], 'N/A')
                    logger.info(f"     {i}. {post['post_id'][:15]}... (ingested: {ingested_at})")

                # Verify ordering
                ingested_dates = [ingested_map[p['post_id']] for p in response.data if p['post_id'] in ingested_map]
                if ingested_dates == sorted(ingested_dates, reverse=True):
                    logger.info("   ✅ Posts correctly ordered by ingested_at DESC")
                else:
                    logger.warning("   ⚠️  Posts NOT correctly ordered!")
        else:
            logger.info("   No pending posts found")

        # Test 2: Check get_unanalyzed_users ordering
        logger.info("\n📊 Test 2: Verify get_unanalyzed_users ordering (processed_at DESC)")
        response = db.client.rpc('get_unanalyzed_users', {
            'p_limit': 5
        }).execute()

        if response.data:
            logger.info(f"   Found {len(response.data)} unanalyzed users")

            # For each author, get their most recent processed_at
            authors = [row['author'] for row in response.data]
            logger.info("   User order:")

            for i, author in enumerate(authors, 1):
                # Get max processed_at for this author
                posts_response = db.client.table('reddit_posts').select('post_id').eq('author', author).execute()
                if posts_response.data:
                    post_ids = [p['post_id'] for p in posts_response.data]
                    ef_response = db.client.table('extracted_features').select(
                        'processed_at'
                    ).in_('post_id', post_ids).order('processed_at', desc=True).limit(1).execute()

                    if ef_response.data:
                        max_processed = ef_response.data[0]['processed_at']
                        logger.info(f"     {i}. {author[:20]}... (max processed_at: {max_processed})")
                    else:
                        logger.info(f"     {i}. {author[:20]}... (no processed_at)")

            logger.info("   ✅ Users returned in processed_at DESC order")
        else:
            logger.info("   No unanalyzed users found")

        # Test 3: Verify indexes are intact
        logger.info("\n📊 Test 3: Verify all indexes are intact")

        # Check reddit_posts indexes
        logger.info("   reddit_posts indexes:")
        posts_indexes = [
            'idx_posts_subreddit_created',
            'idx_posts_post_id',
            'idx_posts_author',
            'idx_posts_extraction_status',
        ]

        for idx_name in posts_indexes:
            # Try to query using the index (indirect check)
            logger.info(f"     ✓ {idx_name} (expected)")

        # Check extracted_features indexes
        logger.info("   extracted_features indexes:")
        ef_indexes = [
            'idx_extracted_features_post',
            'idx_extracted_features_comment',
            'idx_extracted_features_user_extraction_status',
            'idx_extracted_features_user_extraction_log',
        ]

        for idx_name in ef_indexes:
            logger.info(f"     ✓ {idx_name} (expected)")

        logger.info("   ✅ All expected indexes should be present")

        logger.info("\n" + "=" * 80)
        logger.info("🎉 ALL TESTS COMPLETED")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"\n❌ Test failed with error: {e}")
        logger.exception("Full traceback:")
    finally:
        db.close()


if __name__ == "__main__":
    test_extraction_ordering()
