#!/usr/bin/env python3
"""
Benchmark: Get single experience by ID WITHOUT using materialized view

This script benchmarks the experiences.getById query when executed directly on the base tables
(extracted_features, reddit_posts, reddit_comments) WITHOUT using the materialized view.

This represents the non-optimized query path.
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
    print("Benchmarking get experience by ID WITHOUT materialized view...\n")

    # First, get a sample feature_id to use in the test
    conn_temp = get_db_connection()
    with conn_temp.cursor() as cur:
        cur.execute("SELECT id FROM extracted_features LIMIT 1;")
        result = cur.fetchone()
        if not result:
            print("❌ No experiences found in database")
            sys.exit(1)
        sample_id = result[0]
    conn_temp.close()

    print(f"Using sample feature_id: {sample_id}\n")

    # Query that gets a single experience by ID directly from base tables
    query = f"""
EXPLAIN ANALYZE
SELECT
  -- Primary keys and references
  ef.id AS feature_id,
  ef.post_id,
  ef.comment_id,
  COALESCE(rp.subreddit, rc.subreddit) AS subreddit,
  ef.processed_at,

  -- Reddit content (from posts or comments)
  COALESCE(rp.title, '') AS post_title,
  COALESCE(rp.body, '') AS post_text,
  COALESCE(rc.body, '') AS comment_text,
  COALESCE(rp.author, rc.author) AS author,
  COALESCE(rp.created_at, rc.created_at) AS created_at,
  COALESCE(rp.score, rc.score, 0) AS score,
  CASE WHEN ef.post_id IS NOT NULL THEN 'post' ELSE 'comment' END AS source_type,

  -- Extracted features
  ef.primary_drug,
  ef.summary,
  ef.sentiment_pre,
  ef.sentiment_post,
  ef.recommendation_score,
  ef.age,
  ef.sex,
  ef.location,
  ef.state,
  ef.country,
  ef.beginning_weight,
  ef.end_weight,
  ef.duration_weeks,
  ef.cost_per_month,
  ef.currency,
  ef.has_insurance,
  ef.insurance_provider,
  ef.side_effects,
  ef.comorbidities,
  ef.drug_source,

  -- Pre-calculated fields (computed on-the-fly)
  CASE
    WHEN ef.beginning_weight->>'value' IS NOT NULL
      AND ef.end_weight->>'value' IS NOT NULL
      AND ef.beginning_weight->>'unit' = 'lbs'
      AND ef.end_weight->>'unit' = 'lbs'
    THEN (ef.beginning_weight->>'value')::numeric - (ef.end_weight->>'value')::numeric
    WHEN ef.beginning_weight->>'value' IS NOT NULL
      AND ef.end_weight->>'value' IS NOT NULL
      AND ef.beginning_weight->>'unit' = 'kg'
      AND ef.end_weight->>'unit' = 'kg'
    THEN ((ef.beginning_weight->>'value')::numeric - (ef.end_weight->>'value')::numeric) * 2.20462
    ELSE NULL
  END AS weight_loss_lbs,

  CASE
    WHEN ef.beginning_weight->>'value' IS NOT NULL
      AND ef.end_weight->>'value' IS NOT NULL
      AND (ef.beginning_weight->>'value')::numeric > 0
    THEN ((ef.beginning_weight->>'value')::numeric - (ef.end_weight->>'value')::numeric)
         / (ef.beginning_weight->>'value')::numeric * 100
    ELSE NULL
  END AS weight_loss_percentage

FROM extracted_features ef
LEFT JOIN reddit_posts rp ON ef.post_id = rp.post_id
LEFT JOIN reddit_comments rc ON ef.comment_id = rc.comment_id
WHERE ef.id = '{sample_id}'
  AND ef.primary_drug IS NOT NULL
  AND ef.summary IS NOT NULL
  AND ef.summary != ''
  AND LENGTH(TRIM(ef.summary)) > 0
LIMIT 1;
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

        # Run EXPLAIN ANALYZE on get experience by ID query (WITHOUT MV)
        execute_query(
            conn,
            query,
            "Benchmarking Get Experience by ID WITHOUT Materialized View (Direct Table Queries)"
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
