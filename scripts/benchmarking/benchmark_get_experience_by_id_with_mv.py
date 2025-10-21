#!/usr/bin/env python3
"""
Benchmark: Get single experience by ID using materialized view

This script benchmarks the experiences.getById query that queries the
mv_experiences_denormalized materialized view by feature_id.

This is the optimized query path used in production.
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
    print("Benchmarking get experience by ID using materialized view...\n")

    # First, get a sample feature_id to use in the test
    conn_temp = get_db_connection()
    with conn_temp.cursor() as cur:
        cur.execute("SELECT feature_id FROM mv_experiences_denormalized LIMIT 1;")
        result = cur.fetchone()
        if not result:
            print("❌ No experiences found in database")
            sys.exit(1)
        sample_id = result[0]
    conn_temp.close()

    print(f"Using sample feature_id: {sample_id}\n")

    # Query that gets a single experience by ID
    # This simulates: GET /api/experiences/[id]
    query = f"""
EXPLAIN ANALYZE
SELECT *
FROM mv_experiences_denormalized
WHERE feature_id = '{sample_id}'
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

        # Run EXPLAIN ANALYZE on get experience by ID query (using MV)
        execute_query(
            conn,
            query,
            "Benchmarking Get Experience by ID with Materialized View"
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
