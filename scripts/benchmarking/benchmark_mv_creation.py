#!/usr/bin/env python3
"""
One-time script to benchmark the materialized view query performance.

This script:
1. Enables EXPLAIN for PostgREST
2. Reloads the PostgREST config
3. Runs EXPLAIN ANALYZE on the materialized view query
4. Disables EXPLAIN
5. Reloads the PostgREST config again

The query tested is identical to mv_experiences_denormalized from migration 020.
"""

import os
import sys
from pathlib import Path

# Add the repository root to Python path for imports
repo_root = Path(__file__).parent.parent
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
    # Format: https://project-ref.supabase.co
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
    print("Starting materialized view query benchmark...\n")

    # The actual query from the materialized view (migration 020)
    mv_query = """
EXPLAIN ANALYZE
SELECT DISTINCT ON (post_id)
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
  ef.side_effects, -- Full JSONB with severity info
  ef.comorbidities,
  ef.drug_source,
  ef.pharmacy_access_issues,
  ef.plateau_mentioned,
  ef.rebound_weight_gain,
  ef.side_effect_timing,
  ef.side_effect_resolution,
  ef.food_intolerances,
  ef.dosage_progression,
  ef.exercise_frequency,
  ef.dietary_changes,
  ef.labs_improvement,
  ef.medication_reduction,
  ef.nsv_mentioned,
  ef.support_system,
  ef.mental_health_impact,

  -- Pre-calculated fields for performance
  -- Weight loss in lbs (extract from JSONB)
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

  -- Weight loss percentage
  CASE
    WHEN ef.beginning_weight->>'value' IS NOT NULL
      AND ef.end_weight->>'value' IS NOT NULL
      AND (ef.beginning_weight->>'value')::numeric > 0
    THEN ((ef.beginning_weight->>'value')::numeric - (ef.end_weight->>'value')::numeric)
         / (ef.beginning_weight->>'value')::numeric * 100
    ELSE NULL
  END AS weight_loss_percentage,

  -- Weight loss speed in lbs per month
  CASE
    WHEN ef.beginning_weight->>'value' IS NOT NULL
      AND ef.end_weight->>'value' IS NOT NULL
      AND ef.duration_weeks IS NOT NULL
      AND ef.duration_weeks > 0
      AND ef.beginning_weight->>'unit' = 'lbs'
      AND ef.end_weight->>'unit' = 'lbs'
    THEN ((ef.beginning_weight->>'value')::numeric - (ef.end_weight->>'value')::numeric)
         / (ef.duration_weeks / 4.33)
    WHEN ef.beginning_weight->>'value' IS NOT NULL
      AND ef.end_weight->>'value' IS NOT NULL
      AND ef.duration_weeks IS NOT NULL
      AND ef.duration_weeks > 0
      AND ef.beginning_weight->>'unit' = 'kg'
      AND ef.end_weight->>'unit' = 'kg'
    THEN (((ef.beginning_weight->>'value')::numeric - (ef.end_weight->>'value')::numeric) * 2.20462)
         / (ef.duration_weeks / 4.33)
    ELSE NULL
  END AS weight_loss_speed_lbs_per_month,

  -- Weight loss speed in percentage per month
  CASE
    WHEN ef.beginning_weight->>'value' IS NOT NULL
      AND ef.end_weight->>'value' IS NOT NULL
      AND ef.duration_weeks IS NOT NULL
      AND ef.duration_weeks > 0
      AND (ef.beginning_weight->>'value')::numeric > 0
    THEN (((ef.beginning_weight->>'value')::numeric - (ef.end_weight->>'value')::numeric)
          / (ef.beginning_weight->>'value')::numeric * 100)
         / (ef.duration_weeks / 4.33)
    ELSE NULL
  END AS weight_loss_speed_percent_per_month,

  -- Beginning weight in lbs
  CASE
    WHEN ef.beginning_weight->>'unit' = 'lbs'
    THEN (ef.beginning_weight->>'value')::numeric
    WHEN ef.beginning_weight->>'unit' = 'kg'
    THEN (ef.beginning_weight->>'value')::numeric * 2.20462
    ELSE NULL
  END AS beginning_weight_lbs,

  -- End weight in lbs
  CASE
    WHEN ef.end_weight->>'unit' = 'lbs'
    THEN (ef.end_weight->>'value')::numeric
    WHEN ef.end_weight->>'unit' = 'kg'
    THEN (ef.end_weight->>'value')::numeric * 2.20462
    ELSE NULL
  END AS end_weight_lbs,

  -- Sentiment change
  CASE
    WHEN ef.sentiment_pre IS NOT NULL AND ef.sentiment_post IS NOT NULL
    THEN ef.sentiment_post - ef.sentiment_pre
    ELSE NULL
  END AS sentiment_change,

  -- Age bucket for demographic analysis
  CASE
    WHEN ef.age < 25 THEN '18-24'
    WHEN ef.age < 35 THEN '25-34'
    WHEN ef.age < 45 THEN '35-44'
    WHEN ef.age < 55 THEN '45-54'
    WHEN ef.age < 65 THEN '55-64'
    ELSE '65+'
  END AS age_bucket,

  -- Top side effects (extract from JSONB array for convenience)
  CASE
    WHEN ef.side_effects IS NOT NULL
    THEN (
      SELECT array_agg(value::text)
      FROM jsonb_array_elements_text(ef.side_effects)
      LIMIT 5
    )
    ELSE ARRAY[]::text[]
  END AS top_side_effects

FROM extracted_features ef
LEFT JOIN reddit_posts rp ON ef.post_id = rp.post_id
LEFT JOIN reddit_comments rc ON ef.comment_id = rc.comment_id
WHERE ef.primary_drug IS NOT NULL -- Only include records with identified drug
  -- Only include records with non-empty summaries (successfully extracted)
  AND ef.summary IS NOT NULL
  AND ef.summary != ''
  AND LENGTH(TRIM(ef.summary)) > 0
ORDER BY
  post_id,
  -- Prioritize post-level extractions (comment_id IS NULL) over comment-level
  CASE WHEN ef.comment_id IS NULL THEN 0 ELSE 1 END,
  -- Then by sentiment_post (prefer records with better data)
  ef.sentiment_post DESC NULLS LAST,
  -- Finally by processed_at (most recent extraction)
  ef.processed_at DESC;
"""

    conn = None

    try:
        # Connect to database
        print("Connecting to Supabase database...")
        conn = get_db_connection()
        print("✓ Connected successfully\n")

        # Step 1: Enable EXPLAIN for PostgREST
        execute_query(
            conn,
            "ALTER ROLE authenticator SET pgrst.db_plan_enabled TO 'true';",
            "Step 1: Enabling EXPLAIN for PostgREST"
        )

        # Step 2: Reload PostgREST config
        execute_query(
            conn,
            "NOTIFY pgrst, 'reload config';",
            "Step 2: Reloading PostgREST configuration"
        )

        # Step 3: Run EXPLAIN ANALYZE on the materialized view query
        execute_query(
            conn,
            mv_query,
            "Step 3: Running EXPLAIN ANALYZE on materialized view query"
        )

        # Step 4: Disable EXPLAIN for PostgREST
        execute_query(
            conn,
            "ALTER ROLE authenticator SET pgrst.db_plan_enabled TO 'false';",
            "Step 4: Disabling EXPLAIN for PostgREST"
        )

        # Step 5: Reload PostgREST config again
        execute_query(
            conn,
            "NOTIFY pgrst, 'reload config';",
            "Step 5: Reloading PostgREST configuration"
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
