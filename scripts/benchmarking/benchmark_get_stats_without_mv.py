#!/usr/bin/env python3
"""
Benchmark: getStats WITHOUT using materialized view (direct table queries)

This script benchmarks the getStats query when executed directly on the base tables
(extracted_features, reddit_posts, reddit_comments) WITHOUT using the materialized view.

This represents the non-optimized query path and should be significantly slower.
"""

import os
import sys
from pathlib import Path

# Add the repository root to Python path for imports
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))

import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_connection():
    """Create database connection using environment variables."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_db_password = os.getenv("SUPABASE_DB_PASSWORD")

    if not supabase_url or not supabase_db_password:
        raise ValueError("SUPABASE_URL and SUPABASE_DB_PASSWORD must be set in .env")

    # Extract project reference from Supabase URL
    project_ref = supabase_url.replace("https://", "").replace(".supabase.co", "")

    # Construct PostgreSQL connection string
    conn_string = (
        f"postgresql://postgres:{supabase_db_password}"
        f"@db.{project_ref}.supabase.co:5432/postgres"
    )

    return psycopg2.connect(conn_string)


def execute_query(conn, query, description):
    """Execute a query and print results."""
    print(f"\n{'='*80}")
    print(f"{description}")
    print(f"{'='*80}\n")

    with conn.cursor() as cur:
        cur.execute(query)

        # For EXPLAIN queries, fetch and print all rows
        if "EXPLAIN" in query.upper():
            results = cur.fetchall()
            for row in results:
                print(row[0])
        else:
            # For other queries, just commit
            conn.commit()
            print("✓ Query executed successfully")


def main():
    """Main script execution."""
    print("Benchmarking getStats WITHOUT materialized view (direct table queries)...\n")

    # Query that computes platform stats directly from base tables
    # This is the equivalent of get_platform_stats() but without the MV
    query = """
EXPLAIN ANALYZE
WITH deduplicated_experiences AS (
  SELECT DISTINCT ON (post_id)
    ef.id AS feature_id,
    ef.post_id,
    ef.comment_id,
    COALESCE(rp.subreddit, rc.subreddit) AS subreddit,
    ef.processed_at,
    ef.primary_drug,
    ef.summary,
    ef.location,
    ef.state,
    ef.country
  FROM extracted_features ef
  LEFT JOIN reddit_posts rp ON ef.post_id = rp.post_id
  LEFT JOIN reddit_comments rc ON ef.comment_id = rc.comment_id
  WHERE ef.primary_drug IS NOT NULL
    AND ef.summary IS NOT NULL
    AND ef.summary != ''
    AND LENGTH(TRIM(ef.summary)) > 0
  ORDER BY
    post_id,
    CASE WHEN ef.comment_id IS NULL THEN 0 ELSE 1 END,
    ef.sentiment_post DESC NULLS LAST,
    ef.processed_at DESC
)
SELECT
  COUNT(*) AS total_experiences,
  COUNT(DISTINCT primary_drug) FILTER (WHERE primary_drug IS NOT NULL) AS unique_drugs,
  COUNT(DISTINCT location) FILTER (WHERE location IS NOT NULL) AS locations_tracked
FROM deduplicated_experiences;
"""

    conn = None

    try:
        # Connect to database
        print("Connecting to Supabase database...")
        conn = get_db_connection()
        print("✓ Connected successfully\n")

        # Enable EXPLAIN for PostgREST
        execute_query(
            conn,
            "ALTER ROLE authenticator SET pgrst.db_plan_enabled TO 'true';",
            "Enabling EXPLAIN for PostgREST"
        )

        # Reload PostgREST config
        execute_query(
            conn,
            "NOTIFY pgrst, 'reload config';",
            "Reloading PostgREST configuration"
        )

        # Run EXPLAIN ANALYZE on getStats query (WITHOUT MV)
        execute_query(
            conn,
            query,
            "Benchmarking getStats WITHOUT Materialized View (Direct Table Queries)"
        )

        # Disable EXPLAIN for PostgREST
        execute_query(
            conn,
            "ALTER ROLE authenticator SET pgrst.db_plan_enabled TO 'false';",
            "Disabling EXPLAIN for PostgREST"
        )

        # Reload PostgREST config again
        execute_query(
            conn,
            "NOTIFY pgrst, 'reload config';",
            "Reloading PostgREST configuration"
        )

        print(f"\n{'='*80}")
        print("✓ Benchmark completed successfully!")
        print(f"{'='*80}\n")

    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

    finally:
        if conn:
            conn.close()
            print("Database connection closed.\n")


if __name__ == "__main__":
    main()
