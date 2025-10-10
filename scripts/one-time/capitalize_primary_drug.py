#!/usr/bin/env python3
"""
One-time script to capitalize (title case) all primary_drug values in extracted_features.

Context: Enforcing title case for drug names to ensure consistency across the database.
Examples: "compounded tirzepatide" → "Compounded Tirzepatide", "ozempic" → "Ozempic"

Date: 2025-10-09
Author: Claude Code
"""

import os
import sys
import argparse
from pathlib import Path

# Add shared modules to path
repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root / "apps" / "shared"))

from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_supabase_client() -> Client:
    """Initialize Supabase client."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

    if not supabase_url or not supabase_key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")

    return create_client(supabase_url, supabase_key)


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Capitalize all primary_drug values in extracted_features")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    print("=" * 80)
    print("CAPITALIZE PRIMARY_DRUG VALUES")
    print("=" * 80)

    # Initialize Supabase client
    supabase = get_supabase_client()

    # Step 1: Get all extracted_features with non-null primary_drug
    print("\n📊 Fetching all rows with primary_drug...")

    # Fetch in batches to handle pagination
    all_rows = []
    offset = 0
    batch_size = 1000

    while True:
        response = supabase.table("extracted_features").select(
            "id, primary_drug"
        ).not_.is_("primary_drug", "null").range(offset, offset + batch_size - 1).execute()

        batch = response.data
        if not batch:
            break

        all_rows.extend(batch)
        offset += batch_size
        print(f"   Fetched {len(all_rows)} rows so far...")

        if len(batch) < batch_size:
            break

    print(f"   Total found: {len(all_rows)} rows with primary_drug")

    if not all_rows:
        print("\n✅ No rows to process. Exiting.")
        return

    # Step 2: Identify rows that need updating
    print("\n🔍 Identifying rows that need capitalization...")

    rows_to_update = []
    for row in all_rows:
        original = row["primary_drug"]
        capitalized = original.strip().title()

        if original != capitalized:
            rows_to_update.append({
                "id": row["id"],
                "original": original,
                "capitalized": capitalized
            })

    print(f"   Found {len(rows_to_update)} rows to update")

    if not rows_to_update:
        print("\n✅ All primary_drug values are already capitalized. Exiting.")
        return

    # Show a sample of what will be updated
    print("\n📋 Sample of updates (first 10):")
    for i, item in enumerate(rows_to_update[:10]):
        print(f"   {i+1}. \"{item['original']}\" → \"{item['capitalized']}\"")

    if len(rows_to_update) > 10:
        print(f"   ... and {len(rows_to_update) - 10} more")

    # Ask for confirmation unless --yes flag is provided
    if not args.yes:
        print("\n⚠️  About to update {} rows. Continue? (yes/no): ".format(len(rows_to_update)), end="")
        confirmation = input().strip().lower()

        if confirmation not in ["yes", "y"]:
            print("❌ Aborted by user.")
            return
    else:
        print(f"\n✓ --yes flag provided, proceeding with {len(rows_to_update)} updates...")

    # Step 3: Update the rows
    print("\n🔄 Updating rows...")

    updated_count = 0
    failed_count = 0
    updates_by_drug = {}

    for item in rows_to_update:
        row_id = item["id"]
        capitalized = item["capitalized"]
        original = item["original"]

        try:
            supabase.table("extracted_features").update({
                "primary_drug": capitalized
            }).eq("id", row_id).execute()

            # Track updates by drug name
            if capitalized not in updates_by_drug:
                updates_by_drug[capitalized] = 0
            updates_by_drug[capitalized] += 1

            updated_count += 1

            if updated_count % 100 == 0:
                print(f"   Updated {updated_count}/{len(rows_to_update)} rows...")

        except Exception as e:
            print(f"   ❌ Error updating row {row_id} (\"{original}\"): {e}")
            failed_count += 1
            continue

    # Step 4: Report results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"Total rows processed: {len(rows_to_update)}")
    print(f"Successfully updated: {updated_count}")
    print(f"Failed: {failed_count}")

    if updates_by_drug:
        print("\n📊 Updates by drug (after capitalization):")
        for drug, count in sorted(updates_by_drug.items(), key=lambda x: x[1], reverse=True):
            print(f"   {drug}: {count} rows")

    print("\n✅ Capitalization complete!")


if __name__ == "__main__":
    main()
