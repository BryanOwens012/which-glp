#!/usr/bin/env python3
"""
Migration script to standardize drug names in Supabase.

This script:
1. Reads all extracted_features records
2. Standardizes primary_drug using the mapping
3. Updates records in batches
4. Refreshes the materialized view

Usage:
    python3 migrations/standardize_drug_names.py [--dry-run]
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.database import Database
from shared.drug_standardization import standardize_drug_name
from shared.config import get_logger

logger = get_logger(__name__)


def standardize_existing_data(dry_run=False):
    """
    Standardize drug names in extracted_features table.

    Args:
        dry_run: If True, only print changes without updating database
    """
    db = Database()

    logger.info("Starting drug name standardization...")

    # Get all records with non-null primary_drug
    query = """
        SELECT id, primary_drug
        FROM extracted_features
        WHERE primary_drug IS NOT NULL
        ORDER BY id
    """

    with db.conn.cursor() as cur:
        cur.execute(query)
        records = cur.fetchall()

    logger.info(f"Found {len(records)} records with drug names")

    # Build update batches
    updates = []
    changes = {}  # Track what changes will be made

    for record_id, current_drug in records:
        standardized = standardize_drug_name(current_drug)

        if standardized != current_drug:
            updates.append((standardized, record_id))

            # Track changes for reporting
            if current_drug not in changes:
                changes[current_drug] = {"to": standardized, "count": 0}
            changes[current_drug]["count"] += 1

    logger.info(f"Found {len(updates)} records needing updates")

    # Print summary of changes
    if changes:
        logger.info("\n" + "=" * 60)
        logger.info("DRUG NAME CHANGES:")
        logger.info("=" * 60)
        for old_name in sorted(changes.keys()):
            new_name = changes[old_name]["to"]
            count = changes[old_name]["count"]
            logger.info(f"  {old_name:40} -> {new_name:30} ({count:3} records)")
        logger.info("=" * 60 + "\n")

    if dry_run:
        logger.info("DRY RUN - No changes made to database")
        return len(updates)

    if not updates:
        logger.info("No updates needed")
        return 0

    # Confirm before proceeding
    response = input(f"\nUpdate {len(updates)} records? (yes/no): ")
    if response.lower() != "yes":
        logger.info("Aborted by user")
        return 0

    # Update in batches
    batch_size = 100
    updated_count = 0

    with db.conn.cursor() as cur:
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i + batch_size]

            # Use psycopg2's execute_batch for efficiency
            from psycopg2.extras import execute_batch

            execute_batch(
                cur,
                "UPDATE extracted_features SET primary_drug = %s WHERE id = %s",
                batch
            )

            updated_count += len(batch)
            logger.info(f"Updated {updated_count}/{len(updates)} records...")

        db.conn.commit()

    logger.info(f"✅ Successfully updated {updated_count} records")

    # Refresh materialized view
    logger.info("Refreshing materialized view...")
    with db.conn.cursor() as cur:
        cur.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_experiences_denormalized")
        db.conn.commit()

    logger.info("✅ Materialized view refreshed")

    return updated_count


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Standardize drug names in database")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without updating database"
    )

    args = parser.parse_args()

    try:
        count = standardize_existing_data(dry_run=args.dry_run)
        if args.dry_run:
            logger.info(f"\n{'='*60}")
            logger.info(f"DRY RUN COMPLETE: Would update {count} records")
            logger.info(f"Run without --dry-run to apply changes")
            logger.info(f"{'='*60}")
        else:
            logger.info(f"\n{'='*60}")
            logger.info(f"MIGRATION COMPLETE: Updated {count} records")
            logger.info(f"{'='*60}")
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        sys.exit(1)
