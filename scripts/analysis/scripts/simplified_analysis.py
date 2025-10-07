#!/usr/bin/env python3
"""
Simplified GLP-1 Data Analysis - Trial Run

Quick exploration of extracted features to identify patterns and plan next steps.
Works with the actual schema (JSONB fields, arrays, etc.)

Usage:
    cd /Users/bryan/Github/which-glp
    python3 scripts/analysis/scripts/simplified_analysis.py
"""

import os
import psycopg2
import json
from dotenv import load_dotenv
from collections import Counter
from datetime import datetime

load_dotenv()


def get_db_connection():
    """Create PostgreSQL connection."""
    supabase_url = os.getenv("SUPABASE_URL")
    project_ref = supabase_url.replace("https://", "").replace(".supabase.co", "")
    password = os.getenv("SUPABASE_DB_PASSWORD")
    host = f"db.{project_ref}.supabase.co"

    return psycopg2.connect(
        host=host,
        port=5432,
        database="postgres",
        user="postgres",
        password=password,
        sslmode="require"
    )


def safe_extract_weight(jsonb_weight):
    """Extract numeric weight from JSONB field.

    Expected format: {"unit": "lbs", "value": 220.0, "confidence": "high"}
    """
    if not jsonb_weight:
        return None
    if isinstance(jsonb_weight, dict):
        # Extract value field directly
        if 'value' in jsonb_weight:
            try:
                val = jsonb_weight['value']
                # Handle null values
                if val is None:
                    return None
                return float(val)
            except (ValueError, TypeError):
                return None
    return None


def analyze_data():
    """Run simplified analysis on extracted features."""
    print("=" * 80)
    print("GLP-1 SIMPLIFIED DATA ANALYSIS - TRIAL RUN")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. Basic counts
        cursor.execute("SELECT COUNT(*) FROM extracted_features")
        total = cursor.fetchone()[0]
        print(f"Total records: {total:,}")
        print()

        # 2. Primary drug distribution
        print("-" * 80)
        print("PRIMARY DRUG DISTRIBUTION")
        print("-" * 80)
        cursor.execute("""
            SELECT primary_drug, COUNT(*) as count
            FROM extracted_features
            WHERE primary_drug IS NOT NULL
            GROUP BY primary_drug
            ORDER BY count DESC
        """)
        for drug, count in cursor.fetchall():
            pct = 100.0 * count / total
            print(f"  {drug:20s} {count:5,} ({pct:5.1f}%)")
        print()

        # 3. Weight loss analysis (extract from JSONB)
        print("-" * 80)
        print("WEIGHT LOSS DATA AVAILABILITY")
        print("-" * 80)
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(beginning_weight) as has_start,
                COUNT(end_weight) as has_end,
                COUNT(CASE WHEN beginning_weight IS NOT NULL AND end_weight IS NOT NULL THEN 1 END) as has_both
            FROM extracted_features
        """)
        row = cursor.fetchone()
        print(f"  Has beginning weight: {row[1]:5,} ({100.0*row[1]/row[0]:5.1f}%)")
        print(f"  Has end weight:       {row[2]:5,} ({100.0*row[2]/row[0]:5.1f}%)")
        print(f"  Has both weights:     {row[3]:5,} ({100.0*row[3]/row[0]:5.1f}%)")
        print()

        # 4. Duration analysis
        print("-" * 80)
        print("DURATION DATA")
        print("-" * 80)
        cursor.execute("""
            SELECT
                COUNT(duration_weeks) as has_duration,
                MIN(duration_weeks) as min_weeks,
                MAX(duration_weeks) as max_weeks,
                AVG(duration_weeks) as avg_weeks,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_weeks) as median_weeks
            FROM extracted_features
            WHERE duration_weeks IS NOT NULL AND duration_weeks > 0
        """)
        row = cursor.fetchone()
        if row[0]:
            print(f"  Records with duration: {row[0]:,}")
            print(f"  Range: {row[1]:.0f} - {row[2]:.0f} weeks")
            print(f"  Mean: {float(row[3]):.1f} weeks ({float(row[3])/4.33:.1f} months)")
            print(f"  Median: {float(row[4]):.1f} weeks ({float(row[4])/4.33:.1f} months)")
        print()

        # 5. Cost analysis
        print("-" * 80)
        print("COST DATA")
        print("-" * 80)
        cursor.execute("""
            SELECT
                COUNT(cost_per_month) as has_cost,
                MIN(cost_per_month) as min_cost,
                MAX(cost_per_month) as max_cost,
                AVG(cost_per_month) as avg_cost,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY cost_per_month) as median_cost
            FROM extracted_features
            WHERE cost_per_month IS NOT NULL AND cost_per_month > 0
        """)
        row = cursor.fetchone()
        if row[0]:
            print(f"  Records with cost: {row[0]:,}")
            print(f"  Range: ${float(row[1]):.0f} - ${float(row[2]):.0f} per month")
            print(f"  Mean: ${float(row[3]):.0f} per month")
            print(f"  Median: ${float(row[4]):.0f} per month")
        print()

        # 6. Insurance coverage
        print("-" * 80)
        print("INSURANCE COVERAGE")
        print("-" * 80)
        cursor.execute("""
            SELECT
                has_insurance,
                COUNT(*) as count
            FROM extracted_features
            WHERE has_insurance IS NOT NULL
            GROUP BY has_insurance
        """)
        for has_ins, count in cursor.fetchall():
            status = "Covered" if has_ins else "Not covered"
            print(f"  {status:15s} {count:5,}")
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
        for sex, count in cursor.fetchall():
            pct = 100.0 * count / total
            print(f"  {sex:10s} {count:5,} ({pct:5.1f}%)")
        print()

        # 8. Age distribution
        print("-" * 80)
        print("AGE DISTRIBUTION")
        print("-" * 80)
        cursor.execute("""
            SELECT
                COUNT(age) as has_age,
                MIN(age) as min_age,
                MAX(age) as max_age,
                AVG(age) as avg_age
            FROM extracted_features
            WHERE age IS NOT NULL AND age > 0 AND age < 120
        """)
        row = cursor.fetchone()
        if row[0]:
            print(f"  Records with age: {row[0]:,}")
            print(f"  Range: {row[1]} - {row[2]} years")
            print(f"  Mean: {float(row[3]):.1f} years")
        print()

        # 9. Comorbidities (array field)
        print("-" * 80)
        print("COMORBIDITIES")
        print("-" * 80)
        cursor.execute("""
            SELECT COUNT(*)
            FROM extracted_features
            WHERE comorbidities IS NOT NULL AND array_length(comorbidities, 1) > 0
        """)
        comorbid_count = cursor.fetchone()[0]
        print(f"  Records with comorbidities: {comorbid_count:,} ({100.0*comorbid_count/total:.1f}%)")
        print()

        # 10. Side effects (JSONB field)
        print("-" * 80)
        print("SIDE EFFECTS")
        print("-" * 80)
        cursor.execute("""
            SELECT COUNT(*)
            FROM extracted_features
            WHERE side_effects IS NOT NULL
        """)
        se_count = cursor.fetchone()[0]
        print(f"  Records with side effects data: {se_count:,} ({100.0*se_count/total:.1f}%)")
        print()

        # 11. Weight loss calculation (for all records with both weights)
        print("-" * 80)
        print("WEIGHT LOSS ANALYSIS")
        print("-" * 80)
        print("  Extracting weight values from JSONB fields...")
        cursor.execute("""
            SELECT beginning_weight, end_weight, duration_weeks, primary_drug
            FROM extracted_features
            WHERE beginning_weight IS NOT NULL
                AND end_weight IS NOT NULL
        """)

        weight_losses = []
        for row in cursor.fetchall():
            start_weight = safe_extract_weight(row[0])
            end_weight = safe_extract_weight(row[1])
            if start_weight and end_weight and start_weight > end_weight:
                loss = start_weight - end_weight
                weeks = row[2]
                drug = row[3]
                weight_losses.append({
                    'loss': loss,
                    'weeks': weeks,
                    'drug': drug,
                    'pct_loss': 100.0 * loss / start_weight
                })

        if weight_losses:
            avg_loss = sum(w['loss'] for w in weight_losses) / len(weight_losses)
            avg_pct = sum(w['pct_loss'] for w in weight_losses) / len(weight_losses)
            print(f"  Successfully parsed: {len(weight_losses)} records")
            print(f"  Average weight loss: {avg_loss:.1f} lbs ({avg_pct:.1f}% of starting weight)")
            print()

            # Group by drug
            by_drug = {}
            for w in weight_losses:
                drug = w['drug'] or 'Unknown'
                if drug not in by_drug:
                    by_drug[drug] = []
                by_drug[drug].append(w['loss'])

            print("  Average loss by drug:")
            for drug, losses in sorted(by_drug.items(), key=lambda x: len(x[1]), reverse=True):
                avg = sum(losses) / len(losses)
                print(f"    {drug:20s} {avg:6.1f} lbs (n={len(losses)})")
        else:
            print("  ⚠ Could not parse weight data from JSONB format")
            print("  This requires understanding the JSONB structure")
        print()

        # 12. Data quality summary for research questions
        print("=" * 80)
        print("DATA READINESS FOR RESEARCH QUESTIONS")
        print("=" * 80)

        cursor.execute("""
            SELECT COUNT(*) FROM extracted_features
            WHERE beginning_weight IS NOT NULL
                AND end_weight IS NOT NULL
                AND duration_weeks IS NOT NULL
                AND primary_drug IS NOT NULL
        """)
        q1_ready = cursor.fetchone()[0]
        print(f"Q1: Weight loss over time by drug")
        print(f"    Ready: {q1_ready:,} records ({100.0*q1_ready/total:.1f}%)")
        print()

        cursor.execute("""
            SELECT COUNT(*) FROM extracted_features
            WHERE cost_per_month IS NOT NULL
                AND primary_drug IS NOT NULL
        """)
        q2_ready = cursor.fetchone()[0]
        print(f"Q2: Drug accessibility & costs")
        print(f"    Ready: {q2_ready:,} records ({100.0*q2_ready/total:.1f}%)")
        print()

        cursor.execute("""
            SELECT COUNT(*) FROM extracted_features
            WHERE sex IS NOT NULL
                AND beginning_weight IS NOT NULL
                AND end_weight IS NOT NULL
        """)
        q3_ready = cursor.fetchone()[0]
        print(f"Q3: Sex-based differences in outcomes")
        print(f"    Ready: {q3_ready:,} records ({100.0*q3_ready/total:.1f}%)")
        print()

        print("=" * 80)
        print("NEXT STEPS")
        print("=" * 80)
        print()
        print("1. Understand JSONB structure for beginning_weight/end_weight")
        print("   - Query sample records to see the JSON format")
        print("   - Extract numeric values properly")
        print()
        print("2. JOIN with reddit_posts to get subreddit information")
        print("   - Add subreddit context to analysis")
        print("   - Compare patterns across different communities")
        print()
        print("3. Parse side_effects JSONB for specific symptoms")
        print("   - Nausea, fatigue, GI issues by drug")
        print("   - Timing and severity patterns")
        print()
        print("4. Explore advanced fields:")
        print("   - drug_sentiments (before/after sentiment)")
        print("   - labs_improvement array")
        print("   - NSV (non-scale victories) array")
        print("   - plateau_mentioned, rebound_weight_gain booleans")
        print()

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    analyze_data()
