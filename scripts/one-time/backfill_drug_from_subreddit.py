#!/usr/bin/env python3
"""
One-time script to backfill primary_drug and drugs_mentioned in extracted_features
based on subreddit name for rows where primary_drug is currently null.

Context: After adding subreddit name to GLM prompts (commit 78fae6c), some older
extractions may still have null primary_drug when the drug was only mentioned in
the subreddit name. This script backfills those cases.

Date: 2025-10-09
Author: Claude Code
"""

import os
import sys
from pathlib import Path

# Add shared modules to path
repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root / "apps" / "shared"))

from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Subreddit → Drug mapping (case-insensitive)
SUBREDDIT_DRUG_MAPPING = {
    "ozempic": {"primary_drug": "Ozempic", "drugs_mentioned": ["Ozempic"]},
    "mounjaro": {"primary_drug": "Mounjaro", "drugs_mentioned": ["Mounjaro"]},
    "wegovy": {"primary_drug": "Wegovy", "drugs_mentioned": ["Wegovy"]},
    "zepbound": {"primary_drug": "Zepbound", "drugs_mentioned": ["Zepbound"]},
    "semaglutide": {"primary_drug": "Semaglutide", "drugs_mentioned": ["Semaglutide"]},
    "tirzepatidecompound": {"primary_drug": "Tirzepatide", "drugs_mentioned": ["Tirzepatide"]},
    "ozempicforweightloss": {"primary_drug": "Ozempic", "drugs_mentioned": ["Ozempic"]},
    "wegovyweightloss": {"primary_drug": "Wegovy", "drugs_mentioned": ["Wegovy"]},
    "liraglutide": {"primary_drug": "Liraglutide", "drugs_mentioned": ["Liraglutide"]},
}


def get_supabase_client() -> Client:
    """Initialize Supabase client."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

    if not supabase_url or not supabase_key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")

    return create_client(supabase_url, supabase_key)


def main():
    print("=" * 80)
    print("BACKFILL PRIMARY_DRUG FROM SUBREDDIT NAME")
    print("=" * 80)

    # Initialize Supabase client
    supabase = get_supabase_client()

    # Step 1: Get all extracted_features with null primary_drug
    print("\n📊 Fetching rows with null primary_drug...")

    # Fetch in batches to handle pagination
    all_null_drug_rows = []
    offset = 0
    batch_size = 1000

    while True:
        response = supabase.table("extracted_features").select(
            "id, post_id, comment_id, primary_drug"
        ).is_("primary_drug", "null").range(offset, offset + batch_size - 1).execute()

        batch = response.data
        if not batch:
            break

        all_null_drug_rows.extend(batch)
        offset += batch_size
        print(f"   Fetched {len(all_null_drug_rows)} rows so far...")

        if len(batch) < batch_size:
            break

    null_drug_rows = all_null_drug_rows
    print(f"   Total found: {len(null_drug_rows)} rows with null primary_drug")

    if not null_drug_rows:
        print("\n✅ No rows to backfill. Exiting.")
        return

    # Step 2: Get subreddit for each post_id
    print("\n📊 Fetching subreddit names from reddit_posts...")

    # Get unique post_ids (ignore comments for now - they don't have direct subreddit)
    post_ids = [row["post_id"] for row in null_drug_rows if row["post_id"]]
    unique_post_ids = list(set(post_ids))

    print(f"   Fetching subreddits for {len(unique_post_ids)} unique posts...")

    # Fetch subreddits in batches
    post_subreddit_map = {}
    batch_size = 1000

    for i in range(0, len(unique_post_ids), batch_size):
        batch = unique_post_ids[i:i + batch_size]
        response = supabase.table("reddit_posts").select(
            "post_id, subreddit"
        ).in_("post_id", batch).execute()

        for row in response.data:
            post_subreddit_map[row["post_id"]] = row["subreddit"]

    print(f"   Retrieved {len(post_subreddit_map)} subreddit mappings")

    # Step 3: Match and update
    print("\n🔄 Processing updates...")

    updates_by_subreddit = {}
    updated_count = 0
    skipped_count = 0

    for row in null_drug_rows:
        post_id = row["post_id"]
        row_id = row["id"]

        # Skip if no post_id (comment without post lookup)
        if not post_id:
            skipped_count += 1
            continue

        # Get subreddit for this post
        subreddit = post_subreddit_map.get(post_id)
        if not subreddit:
            skipped_count += 1
            continue

        # Check if subreddit matches our mapping (case-insensitive)
        subreddit_lower = subreddit.lower()
        if subreddit_lower not in SUBREDDIT_DRUG_MAPPING:
            skipped_count += 1
            continue

        # Get the drug data to set
        drug_data = SUBREDDIT_DRUG_MAPPING[subreddit_lower]

        # Update the row
        try:
            supabase.table("extracted_features").update({
                "primary_drug": drug_data["primary_drug"],
                "drugs_mentioned": drug_data["drugs_mentioned"]
            }).eq("id", row_id).execute()

            # Track updates by subreddit
            if subreddit not in updates_by_subreddit:
                updates_by_subreddit[subreddit] = 0
            updates_by_subreddit[subreddit] += 1

            updated_count += 1

            if updated_count % 100 == 0:
                print(f"   Updated {updated_count} rows...")

        except Exception as e:
            print(f"   ❌ Error updating row {row_id}: {e}")
            continue

    # Step 4: Report results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"Total rows with null primary_drug: {len(null_drug_rows)}")
    print(f"Successfully updated: {updated_count}")
    print(f"Skipped (no match): {skipped_count}")

    if updates_by_subreddit:
        print("\n📊 Updates by subreddit:")
        for subreddit, count in sorted(updates_by_subreddit.items(), key=lambda x: x[1], reverse=True):
            drug = SUBREDDIT_DRUG_MAPPING[subreddit.lower()]["primary_drug"]
            print(f"   {subreddit}: {count} rows → {drug}")

    print("\n✅ Backfill complete!")


if __name__ == "__main__":
    main()
