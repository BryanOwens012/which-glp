#!/usr/bin/env python3
"""
Verify database schema after migration
Usage: python verify_schema.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import psycopg2


def load_env():
    """Load environment variables from .env file in project root"""
    env_path = Path(__file__).resolve().parents[3] / ".env"

    # Check if .env file exists
    if not env_path.exists():
        raise FileNotFoundError(
            f".env file not found at: {env_path}\n"
            f"Please create a .env file in the project root with required credentials."
        )

    load_dotenv(env_path)


def get_db_connection():
    """Create and return a database connection to Supabase Postgres"""
    required_vars = ["SUPABASE_URL", "SUPABASE_DB_PASSWORD"]

    # Validate all required environment variables are present
    missing_vars = [var for var in required_vars if var not in os.environ or not os.environ[var]]

    if missing_vars:
        raise EnvironmentError(
            f"Missing or empty environment variable(s): {', '.join(missing_vars)}\n"
            f"Please ensure your .env file contains:\n"
            f"  SUPABASE_URL=https://your-project.supabase.co\n"
            f"  SUPABASE_DB_PASSWORD=your-password"
        )

    supabase_url = os.getenv("SUPABASE_URL")

    # Validate URL format
    if not supabase_url.startswith("https://") or ".supabase.co" not in supabase_url:
        raise ValueError(
            f"Invalid SUPABASE_URL format: {supabase_url}\n"
            f"Expected format: https://your-project.supabase.co"
        )

    project_ref = supabase_url.replace("https://", "").replace(".supabase.co", "")

    host = f"db.{project_ref}.supabase.co"
    port = 5432
    database = "postgres"
    user = "postgres"
    password = os.getenv("SUPABASE_DB_PASSWORD")

    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            sslmode="require"
        )
        return conn
    except psycopg2.OperationalError as e:
        raise ConnectionError(
            f"Failed to connect to database: {e}\n"
            f"Attempted connection to: {host}:{port}\n"
            f"Please verify your credentials and network connection."
        )


def verify_tables():
    """Verify that reddit_posts and reddit_comments tables exist with correct schema"""
    load_env()
    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            # Check if tables exist
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('reddit_posts', 'reddit_comments')
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()

            print("✓ Tables found:")
            for table in tables:
                print(f"  - {table[0]}")

            if len(tables) != 2:
                print(f"✗ Expected 2 tables, found {len(tables)}")
                return False

            # Check reddit_posts columns
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'reddit_posts'
                ORDER BY ordinal_position;
            """)
            posts_columns = cursor.fetchall()

            print(f"\n✓ reddit_posts has {len(posts_columns)} columns:")
            for col in posts_columns:
                nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                print(f"  - {col[0]}: {col[1]} ({nullable})")

            # Check reddit_comments columns
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'reddit_comments'
                ORDER BY ordinal_position;
            """)
            comments_columns = cursor.fetchall()

            print(f"\n✓ reddit_comments has {len(comments_columns)} columns:")
            for col in comments_columns:
                nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                print(f"  - {col[0]}: {col[1]} ({nullable})")

            # Check indexes
            cursor.execute("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename IN ('reddit_posts', 'reddit_comments')
                ORDER BY indexname;
            """)
            indexes = cursor.fetchall()

            print(f"\n✓ Found {len(indexes)} indexes:")
            for idx in indexes:
                print(f"  - {idx[0]}")

            # Check foreign key constraint
            cursor.execute("""
                SELECT conname, contype
                FROM pg_constraint
                WHERE conrelid = 'reddit_comments'::regclass
                AND contype = 'f';
            """)
            foreign_keys = cursor.fetchall()

            print(f"\n✓ Found {len(foreign_keys)} foreign key(s) on reddit_comments:")
            for fk in foreign_keys:
                print(f"  - {fk[0]}")

            print("\n✓ Schema verification complete!")
            return True

    except Exception as e:
        print(f"✗ Verification failed: {e}")
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    verify_tables()
