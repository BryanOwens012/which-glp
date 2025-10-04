"""
AI extraction pipeline for Reddit posts and comments.

This script:
1. Exports unprocessed posts/comments from Supabase (bulk query)
2. Builds in-memory lookup for fast context building
3. Processes each item with Claude AI
4. Batch inserts results back to Supabase

Hybrid approach: minimize DB queries, maximize in-memory processing.
"""

import sys
import os
import time
import argparse
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import psycopg2.extras

from shared.database import DatabaseManager
from shared.config import get_logger
from extraction.context import build_context_from_db_rows, ContextBuilder
from extraction.ai_client import get_client
from extraction.prompts import build_post_prompt, build_comment_prompt
from extraction.schema import ExtractionResult, ProcessingStats
from extraction.filters import should_process_post, should_process_comment

logger = get_logger(__name__)


class AIExtractionPipeline:
    """
    Main pipeline for AI-powered extraction from Reddit data.

    Uses hybrid approach: bulk export → in-memory processing → batch insert
    """

    def __init__(
        self,
        subreddit: Optional[str] = None,
        limit: Optional[int] = None,
        dry_run: bool = False,
        posts_only: bool = False
    ):
        """
        Initialize extraction pipeline.

        Args:
            subreddit: Filter by subreddit (e.g., 'Zepbound')
            limit: Max items to process (for testing)
            dry_run: If True, don't insert results to database
            posts_only: If True, only process posts (skip comments)
        """
        self.subreddit = subreddit
        self.limit = limit
        self.dry_run = dry_run
        self.posts_only = posts_only

        self.db = DatabaseManager()
        self.ai_client = get_client()
        self.context_builder: Optional[ContextBuilder] = None
        self.stats = ProcessingStats()

        logger.info(
            f"Pipeline initialized - Subreddit: {subreddit or 'all'}, "
            f"Limit: {limit or 'none'}, Dry run: {dry_run}, "
            f"Posts only: {posts_only}"
        )

    def export_unprocessed_data(self) -> tuple[List[tuple], List[tuple], List[tuple]]:
        """
        Export unprocessed posts and comments from Supabase.

        Performs a bulk query to get all posts/comments that haven't been processed yet.

        Returns:
            Tuple of (posts_rows, comments_rows, all_comments_rows)
        """
        logger.info("Exporting unprocessed data from Supabase...")

        with self.db.conn.cursor() as cursor:
            # Query unprocessed posts
            if self.subreddit:
                posts_query = """
                    SELECT post_id, title, body, subreddit, author_flair_text
                    FROM reddit_posts
                    WHERE post_id NOT IN (
                        SELECT post_id FROM extracted_features
                        WHERE post_id IS NOT NULL
                    )
                    AND subreddit = %s
                    ORDER BY created_at DESC
                """
                if self.limit:
                    posts_query += " LIMIT %s"
                    cursor.execute(posts_query, (self.subreddit, self.limit))
                else:
                    cursor.execute(posts_query, (self.subreddit,))
            else:
                posts_query = """
                    SELECT post_id, title, body, subreddit, author_flair_text
                    FROM reddit_posts
                    WHERE post_id NOT IN (
                        SELECT post_id FROM extracted_features
                        WHERE post_id IS NOT NULL
                    )
                    ORDER BY created_at DESC
                """
                if self.limit:
                    posts_query += " LIMIT %s"
                    cursor.execute(posts_query, (self.limit,))
                else:
                    cursor.execute(posts_query)

            posts_rows = cursor.fetchall()

            # Query unprocessed comments
            if self.subreddit:
                comments_query = """
                    SELECT
                        c.comment_id,
                        c.post_id,
                        c.parent_comment_id,
                        c.body,
                        c.author,
                        c.depth,
                        c.author_flair_text
                    FROM reddit_comments c
                    INNER JOIN reddit_posts p ON c.post_id = p.post_id
                    WHERE c.comment_id NOT IN (
                        SELECT comment_id FROM extracted_features
                        WHERE comment_id IS NOT NULL
                    )
                    AND p.subreddit = %s
                    ORDER BY c.created_at DESC
                """
                if self.limit:
                    comments_query += " LIMIT %s"
                    cursor.execute(comments_query, (self.subreddit, self.limit))
                else:
                    cursor.execute(comments_query, (self.subreddit,))
            else:
                comments_query = """
                    SELECT
                        c.comment_id,
                        c.post_id,
                        c.parent_comment_id,
                        c.body,
                        c.author,
                        c.depth,
                        c.author_flair_text
                    FROM reddit_comments c
                    INNER JOIN reddit_posts p ON c.post_id = p.post_id
                    WHERE c.comment_id NOT IN (
                        SELECT comment_id FROM extracted_features
                        WHERE comment_id IS NOT NULL
                    )
                    ORDER BY c.created_at DESC
                """
                if self.limit:
                    comments_query += " LIMIT %s"
                    cursor.execute(comments_query, (self.limit,))
                else:
                    cursor.execute(comments_query)

            comments_rows = cursor.fetchall()

            # Get ALL comments for posts that have unprocessed comments (for chain building)
            # We need parent comments to build full context
            if comments_rows:
                # Get unique post IDs from unprocessed comments
                comment_post_ids = list(set(row[1] for row in comments_rows))

                all_comments_query = """
                    SELECT comment_id, post_id, parent_comment_id, body, author, depth, author_flair_text
                    FROM reddit_comments
                    WHERE post_id = ANY(%s)
                """
                cursor.execute(all_comments_query, (comment_post_ids,))
                all_comments_rows = cursor.fetchall()
            elif posts_rows:
                # If only posts, get their comments too
                post_ids = [row[0] for row in posts_rows]

                all_comments_query = """
                    SELECT comment_id, post_id, parent_comment_id, body, author, depth, author_flair_text
                    FROM reddit_comments
                    WHERE post_id = ANY(%s)
                """
                cursor.execute(all_comments_query, (post_ids,))
                all_comments_rows = cursor.fetchall()
            else:
                all_comments_rows = []

        logger.info(
            f"Exported {len(posts_rows)} unprocessed posts, "
            f"{len(comments_rows)} unprocessed comments, "
            f"{len(all_comments_rows)} total comments for context"
        )

        return posts_rows, comments_rows, all_comments_rows

    def build_context_lookup(
        self,
        posts_rows: List[tuple],
        all_comments_rows: List[tuple]
    ):
        """
        Build in-memory context lookup from exported data.

        Args:
            posts_rows: All posts (processed + unprocessed)
            all_comments_rows: All comments for context building
        """
        logger.info("Building in-memory context lookup...")

        # Fetch missing posts for comments (P1 fix)
        # Comments may belong to already-processed posts not in posts_rows
        existing_post_ids = set(row[0] for row in posts_rows)
        comment_post_ids = set(row[1] for row in all_comments_rows)
        missing_post_ids = comment_post_ids - existing_post_ids

        if missing_post_ids:
            logger.info(f"Fetching {len(missing_post_ids)} missing posts for comment context...")
            with self.db.conn.cursor() as cursor:
                fetch_posts_query = """
                    SELECT post_id, title, body, subreddit, author_flair_text
                    FROM reddit_posts
                    WHERE post_id = ANY(%s)
                """
                cursor.execute(fetch_posts_query, (list(missing_post_ids),))
                missing_posts_rows = cursor.fetchall()

                # Union missing posts with existing posts
                posts_rows = list(posts_rows) + missing_posts_rows
                logger.info(f"Added {len(missing_posts_rows)} missing posts to context")

        self.context_builder = build_context_from_db_rows(posts_rows, all_comments_rows)

    def process_post(self, post_row: tuple) -> Optional[ExtractionResult]:
        """
        Process a single post with Claude AI.

        Args:
            post_row: (post_id, title, body, subreddit, author_flair_text)

        Returns:
            ExtractionResult or None if failed
        """
        post_id, title, body, subreddit, author_flair = post_row

        try:
            # Get context
            context = self.context_builder.get_post_context(post_id)
            if not context:
                logger.error(f"Failed to build context for post {post_id}")
                return None

            # Skip posts with insufficient content (title + body < 20 chars)
            content_length = len((title or "").strip()) + len((body or "").strip())
            if content_length < 20:
                logger.info(f"Skipping post {post_id} - insufficient content ({content_length} chars)")
                return None

            # Build prompt
            prompt = build_post_prompt(title, body or "", author_flair or "")

            # Call Claude API
            features, metadata = self.ai_client.extract_features(prompt)

            # Build result
            result = ExtractionResult(
                post_id=post_id,
                comment_id=None,
                features=features,
                model_used=metadata["model"],
                processing_cost_usd=metadata["cost_usd"],
                tokens_input=metadata["tokens_input"],
                tokens_output=metadata["tokens_output"],
                processing_time_ms=metadata["processing_time_ms"],
                raw_response=metadata["raw_response"],
            )

            logger.info(f"✓ Processed post {post_id} from r/{subreddit}")
            return result

        except Exception as e:
            logger.error(f"✗ Failed to process post {post_id}: {e}")
            return None

    def process_comment(self, comment_row: tuple) -> Optional[ExtractionResult]:
        """
        Process a single comment with Claude AI.

        Args:
            comment_row: (comment_id, post_id, parent_comment_id, body, author, depth, author_flair_text)

        Returns:
            ExtractionResult or None if failed
        """
        comment_id, post_id, parent_comment_id, body, author, depth, author_flair = comment_row

        try:
            # Get context
            context = self.context_builder.get_comment_context(comment_id)
            if not context:
                logger.error(f"Failed to build context for comment {comment_id}")
                return None

            # Get post context for post author flair
            post = self.context_builder.posts.get(post_id, {})
            post_author_flair = post.get("author_flair", "")

            # Build prompt
            prompt = build_comment_prompt(
                post_title=context["post_title"],
                post_body=context["post_body"],
                comment_chain=context["comment_chain"],
                target_comment_id=comment_id,
                post_author_flair=post_author_flair
            )

            # Call Claude API
            features, metadata = self.ai_client.extract_features(prompt)

            # Build result
            result = ExtractionResult(
                post_id=None,
                comment_id=comment_id,
                features=features,
                model_used=metadata["model"],
                processing_cost_usd=metadata["cost_usd"],
                tokens_input=metadata["tokens_input"],
                tokens_output=metadata["tokens_output"],
                processing_time_ms=metadata["processing_time_ms"],
                raw_response=metadata["raw_response"],
            )

            logger.info(f"✓ Processed comment {comment_id} (depth {depth})")
            return result

        except Exception as e:
            logger.error(f"✗ Failed to process comment {comment_id}: {e}")
            return None

    def save_backup(self, results: List[ExtractionResult]):
        """
        Save extraction results to local JSON backup file.

        Args:
            results: List of ExtractionResult objects
        """
        if not results:
            logger.warning("No results to backup")
            return

        # Create extraction_backups directory if it doesn't exist
        # Use environment variable if set, otherwise use default location
        backup_path = os.getenv('EXTRACTION_BACKUP_DIR')
        if backup_path:
            backup_dir = Path(backup_path)
        else:
            # Default: use absolute path to avoid issues with working directory
            backup_dir = Path(__file__).parent.parent / "extraction_backups"
        backup_dir.mkdir(exist_ok=True, parents=True)

        # Generate filename with timestamp and subreddit
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        subreddit_suffix = f"_{self.subreddit}" if self.subreddit else ""
        filename = f"extraction_backup{subreddit_suffix}_{timestamp}.json"
        filepath = backup_dir / filename

        # Convert results to JSON-serializable format
        backup_data = {
            "metadata": {
                "timestamp": timestamp,
                "subreddit": self.subreddit,
                "total_results": len(results),
                "stats": {
                    "total_processed": self.stats.total_processed,
                    "total_success": self.stats.total_success,
                    "total_failed": self.stats.total_failed,
                    "total_cost_usd": self.stats.total_cost_usd,
                    "total_tokens": self.stats.total_tokens_input + self.stats.total_tokens_output,
                }
            },
            "results": []
        }

        for result in results:
            backup_data["results"].append({
                "post_id": result.post_id,
                "comment_id": result.comment_id,
                "features": result.features.model_dump(),
                "model_used": result.model_used,
                "processing_cost_usd": result.processing_cost_usd,
                "tokens_input": result.tokens_input,
                "tokens_output": result.tokens_output,
                "processing_time_ms": result.processing_time_ms,
                "processed_at": result.processed_at.isoformat() if result.processed_at else None,
            })

        # Write to file
        with open(filepath, 'w') as f:
            json.dump(backup_data, f, indent=2)

        logger.info(f"✓ Backup saved to {filepath} ({len(results)} results)")

    def insert_results(self, results: List[ExtractionResult]):
        """
        Batch insert extraction results to Supabase.

        Args:
            results: List of ExtractionResult objects
        """
        if not results:
            logger.warning("No results to insert")
            return

        if self.dry_run:
            logger.info(f"DRY RUN: Would insert {len(results)} results")
            return

        logger.info(f"Inserting {len(results)} results to database...")

        insert_query = """
            INSERT INTO extracted_features (
                post_id, comment_id, summary,
                beginning_weight, end_weight, duration_weeks,
                cost_per_month, currency, drugs_mentioned, primary_drug, drug_sentiments,
                sentiment_pre, sentiment_post, recommendation_score,
                has_insurance, insurance_provider, side_effects, comorbidities, location,
                age, sex, state, country,
                dosage_progression, exercise_frequency, dietary_changes, previous_weight_loss_attempts,
                drug_source, switching_drugs,
                side_effect_timing, side_effect_resolution, food_intolerances,
                plateau_mentioned, rebound_weight_gain,
                labs_improvement, medication_reduction, nsv_mentioned,
                support_system, pharmacy_access_issues, mental_health_impact,
                model_used, confidence_score, processing_cost_usd,
                tokens_input, tokens_output, processing_time_ms,
                processed_at, raw_response
            ) VALUES (
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s
            )
            ON CONFLICT DO NOTHING
        """

        rows = []
        for result in results:
            f = result.features

            # Convert side_effects list of SideEffectData to JSON
            side_effects_json = None
            if f.side_effects:
                side_effects_json = psycopg2.extras.Json([se.model_dump() for se in f.side_effects])

            rows.append((
                result.post_id,
                result.comment_id,
                f.summary,
                psycopg2.extras.Json(f.beginning_weight.model_dump()) if f.beginning_weight else None,
                psycopg2.extras.Json(f.end_weight.model_dump()) if f.end_weight else None,
                f.duration_weeks,
                f.cost_per_month,
                f.currency,
                f.drugs_mentioned,
                f.primary_drug,
                psycopg2.extras.Json(f.drug_sentiments) if f.drug_sentiments else None,
                f.sentiment_pre,
                f.sentiment_post,
                f.recommendation_score,
                f.has_insurance,
                f.insurance_provider,
                side_effects_json,
                f.comorbidities,
                f.location,
                f.age,
                f.sex,
                f.state,
                f.country,
                f.dosage_progression,
                f.exercise_frequency,
                f.dietary_changes,
                f.previous_weight_loss_attempts,
                f.drug_source,
                f.switching_drugs,
                f.side_effect_timing,
                f.side_effect_resolution,
                f.food_intolerances,
                f.plateau_mentioned,
                f.rebound_weight_gain,
                f.labs_improvement,
                f.medication_reduction,
                f.nsv_mentioned,
                f.support_system,
                f.pharmacy_access_issues,
                f.mental_health_impact,
                result.model_used,
                f.confidence_score,
                result.processing_cost_usd,
                result.tokens_input,
                result.tokens_output,
                result.processing_time_ms,
                result.processed_at,
                psycopg2.extras.Json(result.raw_response) if result.raw_response else None,
            ))

        with self.db.conn.cursor() as cursor:
            cursor.executemany(insert_query, rows)
            self.db.conn.commit()

        logger.info(f"✓ Inserted {len(results)} results")

    def run(self):
        """
        Run the full extraction pipeline.

        1. Export unprocessed data
        2. Build in-memory lookups
        3. Process all items
        4. Batch insert results
        """
        start_time = time.time()
        logger.info("=" * 60)
        logger.info("Starting AI extraction pipeline")
        logger.info("=" * 60)

        # Export data
        posts_rows, comments_rows, all_comments_rows = self.export_unprocessed_data()

        if not posts_rows and not comments_rows:
            logger.info("No unprocessed data found. Exiting.")
            return

        # Build context lookup
        self.build_context_lookup(posts_rows, all_comments_rows)

        # Process posts
        post_results = []
        skipped_count = 0
        for i, post_row in enumerate(posts_rows, 1):
            # post_row format: (post_id, title, body, subreddit, author_flair_text)
            post_subreddit = post_row[3]

            # Apply content filter to save API costs
            if not should_process_post(post_row, post_subreddit):
                logger.info(f"Skipping post {i}/{len(posts_rows)} (no drug/medical keywords)")
                skipped_count += 1
                continue

            logger.info(f"Processing post {i}/{len(posts_rows)}...")
            result = self.process_post(post_row)
            if result:
                post_results.append(result)
                self.stats.total_success += 1
                self.stats.total_cost_usd += result.processing_cost_usd or 0
                self.stats.total_tokens_input += result.tokens_input or 0
                self.stats.total_tokens_output += result.tokens_output or 0
                self.stats.total_time_seconds += (result.processing_time_ms or 0) / 1000
            else:
                self.stats.total_failed += 1

            self.stats.total_processed += 1

            # Rate limiting: 1 request per second
            time.sleep(1)

        if skipped_count > 0:
            logger.info(f"Skipped {skipped_count} posts without drug/medical keywords")

        # Process comments (unless posts_only mode)
        comment_results = []
        if not self.posts_only:
            for i, comment_row in enumerate(comments_rows, 1):
                logger.info(f"Processing comment {i}/{len(comments_rows)}...")
                result = self.process_comment(comment_row)
                if result:
                    comment_results.append(result)
                    self.stats.total_success += 1
                    self.stats.total_cost_usd += result.processing_cost_usd or 0
                    self.stats.total_tokens_input += result.tokens_input or 0
                    self.stats.total_tokens_output += result.tokens_output or 0
                    self.stats.total_time_seconds += (result.processing_time_ms or 0) / 1000
                else:
                    self.stats.total_failed += 1

                self.stats.total_processed += 1

                # Rate limiting: 1 request per second
                time.sleep(1)
        else:
            logger.info("Skipping comment processing (posts_only=True)")

        # Insert all results
        all_results = post_results + comment_results
        if all_results:
            # Save backup before inserting to database
            self.save_backup(all_results)
            self.insert_results(all_results)

        # Print summary
        self.stats.mark_completed()
        elapsed = time.time() - start_time
        avg = self.stats.calculate_averages()

        logger.info("=" * 60)
        logger.info("EXTRACTION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Total processed: {self.stats.total_processed}")
        logger.info(f"Successful: {self.stats.total_success}")
        logger.info(f"Failed: {self.stats.total_failed}")
        logger.info(f"Total cost: ${self.stats.total_cost_usd:.4f}")
        logger.info(f"Total tokens: {self.stats.total_tokens_input + self.stats.total_tokens_output:,}")
        logger.info(f"Avg cost per item: ${avg['avg_cost_per_item']:.6f}")
        logger.info(f"Avg tokens per item: {avg['avg_tokens_per_item']:.0f}")
        logger.info(f"Total time: {elapsed:.1f}s")
        logger.info("=" * 60)


def main():
    """Command-line entry point"""
    parser = argparse.ArgumentParser(
        description="AI extraction pipeline for Reddit data"
    )
    parser.add_argument(
        "--subreddit",
        type=str,
        default=None,
        help="Filter by subreddit (e.g., 'Zepbound')"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max items to process (for testing)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't insert results to database"
    )
    parser.add_argument(
        "--posts-only",
        action="store_true",
        help="Only process posts, skip comments"
    )

    args = parser.parse_args()

    # Run pipeline
    pipeline = AIExtractionPipeline(
        subreddit=args.subreddit,
        limit=args.limit,
        dry_run=args.dry_run,
        posts_only=args.posts_only
    )

    try:
        pipeline.run()
    except KeyboardInterrupt:
        logger.warning("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
