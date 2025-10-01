#!/usr/bin/env python3
"""
Database migration runner for Supabase Postgres
Usage: python run_migration.py <migration_file.sql>
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql


def load_env():
    """Load environment variables from .env file in project root"""
    env_path = Path(__file__).resolve().parents[3] / ".env"

    # Check if .env file exists
    if not env_path.exists():
        raise FileNotFoundError(
            f".env file not found at: {env_path}\n"
            f"Please create a .env file in the project root with required credentials:\n"
            f"  SUPABASE_URL=https://your-project.supabase.co\n"
            f"  SUPABASE_DB_PASSWORD=your-password"
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

    # Extract database connection details from Supabase URL
    # Supabase URL format: https://<project_ref>.supabase.co
    supabase_url = os.getenv("SUPABASE_URL")

    # Validate URL format
    if not supabase_url.startswith("https://") or ".supabase.co" not in supabase_url:
        raise ValueError(
            f"Invalid SUPABASE_URL format: {supabase_url}\n"
            f"Expected format: https://your-project.supabase.co"
        )

    project_ref = supabase_url.replace("https://", "").replace(".supabase.co", "")

    # Construct Postgres connection string
    # Supabase Postgres: db.<project_ref>.supabase.co:5432
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
        print(f"Error connecting to database: {e}")
        print(f"Attempted connection to: {host}:{port}")
        raise


def run_migration(migration_file: Path):
    """Execute SQL migration file against the database"""
    # Validate migration file exists
    if not migration_file.exists():
        raise FileNotFoundError(
            f"Migration file not found: {migration_file}\n"
            f"Please ensure the file exists in the migrations directory."
        )

    # Validate migration file is not empty
    if migration_file.stat().st_size == 0:
        raise ValueError(
            f"Migration file is empty: {migration_file}\n"
            f"Please ensure the SQL file contains valid migration statements."
        )

    print(f"Loading migration: {migration_file.name}")

    # Read migration SQL
    try:
        with open(migration_file, "r") as f:
            migration_sql = f.read()
    except Exception as e:
        raise IOError(f"Failed to read migration file: {e}")

    # Load environment and establish connection
    load_env()
    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            print(f"Executing migration...")
            cursor.execute(migration_sql)
            conn.commit()
            print(f"✓ Migration completed successfully: {migration_file.name}")
    except psycopg2.Error as e:
        conn.rollback()
        print(f"✗ Migration failed: {e}")
        raise
    finally:
        conn.close()


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_migration.py <migration_file.sql>")
        print("\nExample:")
        print("  python run_migration.py 001_create_reddit_tables.sql")
        sys.exit(1)

    migration_file = Path(__file__).parent / sys.argv[1]

    try:
        run_migration(migration_file)
    except Exception as e:
        print(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
