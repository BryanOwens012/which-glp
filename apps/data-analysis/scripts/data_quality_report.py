#!/usr/bin/env python3
"""
Data Quality Assessment for GLP-1 Extracted Features

This script queries the extracted_features table and generates a report on:
- Data completeness for key fields
- Sample sizes per drug
- Field population rates
- Data quality issues

Usage:
    cd /Users/bryan/Github/which-glp
    python3 apps/data-analysis/scripts/data_quality_report.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import json

import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_db_connection():
    """Create direct PostgreSQL connection for complex queries."""
    # Extract project reference from SUPABASE_URL
    supabase_url = os.getenv("SUPABASE_URL")
    if not supabase_url:
        raise ValueError("SUPABASE_URL not found in environment variables")

    # Parse project ref from URL (format: https://<project-ref>.supabase.co)
    project_ref = supabase_url.replace("https://", "").replace(".supabase.co", "")

    # Get password
    password = os.getenv("SUPABASE_DB_PASSWORD")
    if not password:
        raise ValueError("SUPABASE_DB_PASSWORD not found in environment variables")

    # Construct connection parameters (same as Database class in shared/database.py)
    host = f"db.{project_ref}.supabase.co"
    port = 5432
    database = "postgres"
    user = "postgres"

    return psycopg2.connect(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
        sslmode="require"
    )


def assess_data_quality():
    """Generate comprehensive data quality report."""
    print("=" * 80)
    print("GLP-1 EXTRACTED FEATURES - DATA QUALITY ASSESSMENT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. Total record count
        cursor.execute("SELECT COUNT(*) FROM extracted_features")
        total_records = cursor.fetchone()[0]
        print(f"Total extracted features: {total_records:,}")
        print()

        # 2. Records by subreddit
        print("-" * 80)
        print("RECORDS BY SUBREDDIT")
        print("-" * 80)
        cursor.execute("""
            SELECT subreddit, COUNT(*) as count
            FROM extracted_features
            GROUP BY subreddit
            ORDER BY count DESC
        """)
        subreddit_counts = cursor.fetchall()
        for subreddit, count in subreddit_counts:
            print(f"  {subreddit:30s} {count:6,} records")
        print()

        # 3. Field completeness analysis
        print("-" * 80)
        print("FIELD COMPLETENESS (% of records with non-null values)")
        print("-" * 80)

        fields_to_check = [
            ('drug', 'Drug name'),
            ('weight_loss_amount', 'Weight loss amount'),
            ('timeframe', 'Timeframe'),
            ('starting_weight', 'Starting weight'),
            ('current_weight', 'Current weight'),
            ('sex', 'Sex'),
            ('side_effects', 'Side effects'),
            ('cost', 'Cost'),
            ('out_of_pocket_cost', 'Out-of-pocket cost'),
            ('drug_source', 'Drug source (pharmacy/compound)'),
            ('comorbidities', 'Comorbidities'),
        ]

        completeness_data = {}
        for field, label in fields_to_check:
            cursor.execute(f"""
                SELECT
                    COUNT(*) as total,
                    COUNT({field}) as populated,
                    ROUND(100.0 * COUNT({field}) / COUNT(*), 1) as pct
                FROM extracted_features
            """)
            total, populated, pct = cursor.fetchone()
            completeness_data[field] = {'populated': populated, 'pct': pct}
            print(f"  {label:35s} {populated:6,} / {total:6,} ({pct:5.1f}%)")
        print()

        # 4. Weight loss data analysis
        print("-" * 80)
        print("WEIGHT LOSS DATA ANALYSIS")
        print("-" * 80)

        cursor.execute("""
            SELECT COUNT(*)
            FROM extracted_features
            WHERE weight_loss_amount IS NOT NULL AND timeframe IS NOT NULL
        """)
        weight_timeframe_count = cursor.fetchone()[0]
        print(f"  Records with both weight_loss AND timeframe: {weight_timeframe_count:,}")

        # Weight loss + drug
        cursor.execute("""
            SELECT COUNT(*)
            FROM extracted_features
            WHERE weight_loss_amount IS NOT NULL AND drug IS NOT NULL
        """)
        weight_drug_count = cursor.fetchone()[0]
        print(f"  Records with both weight_loss AND drug:      {weight_drug_count:,}")

        # Starting weight distribution
        cursor.execute("""
            SELECT
                CASE
                    WHEN starting_weight < 150 THEN '<150 lbs'
                    WHEN starting_weight BETWEEN 150 AND 200 THEN '150-200 lbs'
                    WHEN starting_weight BETWEEN 200 AND 250 THEN '200-250 lbs'
                    WHEN starting_weight BETWEEN 250 AND 300 THEN '250-300 lbs'
                    ELSE '300+ lbs'
                END as weight_range,
                COUNT(*) as count
            FROM extracted_features
            WHERE starting_weight IS NOT NULL
            GROUP BY weight_range
            ORDER BY weight_range
        """)
        weight_ranges = cursor.fetchall()
        print()
        print("  Starting weight distribution:")
        for weight_range, count in weight_ranges:
            print(f"    {weight_range:15s} {count:6,} records")
        print()

        # 5. Drug distribution
        print("-" * 80)
        print("DRUG DISTRIBUTION")
        print("-" * 80)
        cursor.execute("""
            SELECT drug, COUNT(*) as count
            FROM extracted_features
            WHERE drug IS NOT NULL
            GROUP BY drug
            ORDER BY count DESC
        """)
        drug_dist = cursor.fetchall()
        for drug, count in drug_dist:
            print(f"  {drug:20s} {count:6,} records")
        print()

        # 6. Timeframe distribution
        print("-" * 80)
        print("TIMEFRAME DISTRIBUTION")
        print("-" * 80)
        cursor.execute("""
            SELECT timeframe, COUNT(*) as count
            FROM extracted_features
            WHERE timeframe IS NOT NULL
            GROUP BY timeframe
            ORDER BY count DESC
            LIMIT 15
        """)
        timeframe_dist = cursor.fetchall()
        for timeframe, count in timeframe_dist:
            print(f"  {timeframe:20s} {count:6,} records")
        print()

        # 7. Sex distribution
        print("-" * 80)
        print("SEX DISTRIBUTION")
        print("-" * 80)
        cursor.execute("""
            SELECT sex, COUNT(*) as count
            FROM extracted_features
            WHERE sex IS NOT NULL
            GROUP BY sex
            ORDER BY count DESC
        """)
        sex_dist = cursor.fetchall()
        for sex, count in sex_dist:
            print(f"  {sex:20s} {count:6,} records")
        print()

        # 8. Cost data analysis
        print("-" * 80)
        print("COST DATA ANALYSIS")
        print("-" * 80)
        cursor.execute("""
            SELECT
                COUNT(*) FILTER (WHERE cost IS NOT NULL) as cost_count,
                COUNT(*) FILTER (WHERE out_of_pocket_cost IS NOT NULL) as oop_cost_count,
                COUNT(*) FILTER (WHERE drug_source IS NOT NULL) as drug_source_count
            FROM extracted_features
        """)
        cost_count, oop_count, source_count = cursor.fetchone()
        print(f"  Records with cost data:             {cost_count:6,}")
        print(f"  Records with out-of-pocket cost:    {oop_count:6,}")
        print(f"  Records with drug source:           {source_count:6,}")
        print()

        # 9. Comorbidities analysis
        print("-" * 80)
        print("COMORBIDITIES ANALYSIS")
        print("-" * 80)
        cursor.execute("""
            SELECT COUNT(*)
            FROM extracted_features
            WHERE comorbidities IS NOT NULL AND comorbidities != ''
        """)
        comorbidity_count = cursor.fetchone()[0]
        print(f"  Records with comorbidities:         {comorbidity_count:6,}")

        # Most common comorbidities (this is simplified - comorbidities is a text field)
        cursor.execute("""
            SELECT comorbidities, COUNT(*) as count
            FROM extracted_features
            WHERE comorbidities IS NOT NULL AND comorbidities != ''
            GROUP BY comorbidities
            ORDER BY count DESC
            LIMIT 10
        """)
        common_comorbidities = cursor.fetchall()
        print()
        print("  Most frequently mentioned comorbidity patterns:")
        for comorbidity, count in common_comorbidities:
            # Truncate long text
            comorbidity_text = comorbidity[:50] + "..." if len(comorbidity) > 50 else comorbidity
            print(f"    {comorbidity_text:55s} {count:4,}x")
        print()

        # 10. Data quality summary
        print("=" * 80)
        print("DATA QUALITY SUMMARY")
        print("=" * 80)

        # Calculate usability for different analyses
        cursor.execute("""
            SELECT COUNT(*) FROM extracted_features
            WHERE weight_loss_amount IS NOT NULL
                AND drug IS NOT NULL
                AND timeframe IS NOT NULL
        """)
        usable_for_weight_analysis = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM extracted_features
            WHERE weight_loss_amount IS NOT NULL
                AND drug IS NOT NULL
                AND starting_weight IS NOT NULL
        """)
        usable_for_starting_weight_analysis = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM extracted_features
            WHERE drug IS NOT NULL AND cost IS NOT NULL
        """)
        usable_for_cost_analysis = cursor.fetchone()[0]

        print(f"Records usable for weight loss trajectory analysis:")
        print(f"  (weight_loss + drug + timeframe): {usable_for_weight_analysis:,} " +
              f"({100.0 * usable_for_weight_analysis / total_records:.1f}%)")
        print()
        print(f"Records usable for starting weight impact analysis:")
        print(f"  (weight_loss + drug + starting_weight): {usable_for_starting_weight_analysis:,} " +
              f"({100.0 * usable_for_starting_weight_analysis / total_records:.1f}%)")
        print()
        print(f"Records usable for cost/accessibility analysis:")
        print(f"  (drug + cost): {usable_for_cost_analysis:,} " +
              f"({100.0 * usable_for_cost_analysis / total_records:.1f}%)")
        print()

        # 11. Export summary to JSON
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_records': total_records,
            'subreddits': {sub: count for sub, count in subreddit_counts},
            'field_completeness': completeness_data,
            'usability_metrics': {
                'weight_loss_trajectory': usable_for_weight_analysis,
                'starting_weight_impact': usable_for_starting_weight_analysis,
                'cost_accessibility': usable_for_cost_analysis
            }
        }

        output_path = Path(__file__).resolve().parent.parent / "outputs" / "data_quality_summary.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)

        print("=" * 80)
        print(f"Summary exported to: {output_path}")
        print("=" * 80)

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    assess_data_quality()
