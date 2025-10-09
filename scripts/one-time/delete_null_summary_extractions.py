#!/usr/bin/env python3
"""
One-time script to delete extracted_features where summary is null or empty string.

This allows posts to be re-ingested with proper summary extraction.

Run date: 2025-10-09
Reason: Early extractions may have null or empty summaries due to extraction bugs.
        The prompt now requires summary to NEVER be null or empty, so we delete these
        invalid extractions to allow re-processing.
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def main():
    """Delete all extracted_features where summary is null or empty string."""

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Delete extracted_features with null or empty summaries')
    parser.add_argument('--yes', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()

    # Load environment variables
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        print("   Check your .env file or environment variables")
        sys.exit(1)

    # Create Supabase client
    print(f"Connecting to Supabase at {supabase_url}...")
    client: Client = create_client(supabase_url, supabase_key)

    # First, check how many rows will be deleted (null OR empty string)
    print("\n1. Checking how many rows have null or empty summaries...")
    try:
        # Count null summaries
        null_response = client.table('extracted_features') \
            .select('*', count='exact') \
            .is_('summary', 'null') \
            .execute()
        null_count = null_response.count if null_response.count is not None else 0

        # Count empty string summaries
        empty_response = client.table('extracted_features') \
            .select('*', count='exact') \
            .eq('summary', '') \
            .execute()
        empty_count = empty_response.count if empty_response.count is not None else 0

        rows_to_delete = null_count + empty_count
        print(f"   Found {null_count} rows with null summaries")
        print(f"   Found {empty_count} rows with empty string summaries")
        print(f"   Total to delete: {rows_to_delete} rows")

        if rows_to_delete == 0:
            print("\n✅ No rows to delete. All summaries are non-null and non-empty.")
            return

    except Exception as e:
        print(f"❌ Error checking count: {e}")
        sys.exit(1)

    # Confirm deletion
    if not args.yes:
        print(f"\n⚠️  About to delete {rows_to_delete} extracted_features rows")
        response = input("   Continue? (yes/no): ")

        if response.lower() != 'yes':
            print("❌ Deletion cancelled")
            sys.exit(0)
    else:
        print(f"\n⚠️  Deleting {rows_to_delete} extracted_features rows (--yes flag provided)...")

    # Delete rows where summary is null
    print("\n2. Deleting rows with null summaries...")
    try:
        delete_null_response = client.table('extracted_features') \
            .delete() \
            .is_('summary', 'null') \
            .execute()

        null_deleted = delete_null_response.count if delete_null_response.count is not None else (len(delete_null_response.data) if delete_null_response.data else 0)
        print(f"   Deleted {null_deleted} rows with null summaries")

    except Exception as e:
        print(f"❌ Error deleting null summaries: {e}")
        sys.exit(1)

    # Delete rows where summary is empty string
    print("\n3. Deleting rows with empty string summaries...")
    try:
        delete_empty_response = client.table('extracted_features') \
            .delete() \
            .eq('summary', '') \
            .execute()

        empty_deleted = delete_empty_response.count if delete_empty_response.count is not None else (len(delete_empty_response.data) if delete_empty_response.data else 0)
        print(f"   Deleted {empty_deleted} rows with empty summaries")

    except Exception as e:
        print(f"❌ Error deleting empty summaries: {e}")
        sys.exit(1)

    total_deleted = null_deleted + empty_deleted
    print(f"\n   Total deleted: {total_deleted} rows")

    # Verify deletion
    print("\n4. Verifying deletion...")
    try:
        # Check null summaries
        verify_null_response = client.table('extracted_features') \
            .select('*', count='exact') \
            .is_('summary', 'null') \
            .execute()
        remaining_null = verify_null_response.count if verify_null_response.count is not None else 0

        # Check empty summaries
        verify_empty_response = client.table('extracted_features') \
            .select('*', count='exact') \
            .eq('summary', '') \
            .execute()
        remaining_empty = verify_empty_response.count if verify_empty_response.count is not None else 0

        remaining_total = remaining_null + remaining_empty

        print(f"   Remaining null summaries: {remaining_null}")
        print(f"   Remaining empty summaries: {remaining_empty}")
        print(f"   Total remaining: {remaining_total}")

        if remaining_total == 0:
            print("\n✅ Success! All null and empty summaries have been deleted.")
        else:
            print(f"\n⚠️  Warning: {remaining_total} invalid summaries still remain")

    except Exception as e:
        print(f"❌ Error during verification: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
