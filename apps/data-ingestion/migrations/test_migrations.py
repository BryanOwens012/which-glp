#!/usr/bin/env python3
"""
Unit tests for migration scripts
Run with: pytest test_migrations.py -v
"""

import os
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import psycopg2
from run_migration import load_env, get_db_connection, run_migration


class TestLoadEnv:
    """Test environment loading functionality"""

    @patch('run_migration.Path')
    def test_load_env_file_not_found(self, mock_path):
        """Test that missing .env file raises FileNotFoundError with helpful message"""
        mock_path.return_value.resolve.return_value.parents.__getitem__.return_value.__truediv__.return_value.exists.return_value = False

        with pytest.raises(FileNotFoundError) as exc_info:
            load_env()

        assert ".env file not found" in str(exc_info.value)
        assert "Please create a .env file" in str(exc_info.value)

    @patch('run_migration.load_dotenv')
    @patch('run_migration.Path')
    def test_load_env_success(self, mock_path, mock_load_dotenv):
        """Test successful environment loading"""
        mock_env_path = MagicMock()
        mock_env_path.exists.return_value = True
        mock_path.return_value.resolve.return_value.parents.__getitem__.return_value.__truediv__.return_value = mock_env_path

        load_env()

        mock_load_dotenv.assert_called_once()


class TestGetDbConnection:
    """Test database connection functionality"""

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_supabase_url(self):
        """Test that missing SUPABASE_URL raises EnvironmentError"""
        with pytest.raises(EnvironmentError) as exc_info:
            get_db_connection()

        assert "SUPABASE_URL" in str(exc_info.value)
        assert "Missing or empty environment variable" in str(exc_info.value)

    @patch.dict(os.environ, {"SUPABASE_URL": "https://test.supabase.co"}, clear=True)
    def test_missing_supabase_password(self):
        """Test that missing SUPABASE_DB_PASSWORD raises EnvironmentError"""
        with pytest.raises(EnvironmentError) as exc_info:
            get_db_connection()

        assert "SUPABASE_DB_PASSWORD" in str(exc_info.value)

    @patch.dict(os.environ, {"SUPABASE_URL": "", "SUPABASE_DB_PASSWORD": "pass"}, clear=True)
    def test_empty_supabase_url(self):
        """Test that empty SUPABASE_URL raises EnvironmentError"""
        with pytest.raises(EnvironmentError) as exc_info:
            get_db_connection()

        assert "SUPABASE_URL" in str(exc_info.value)

    @patch.dict(os.environ, {
        "SUPABASE_URL": "invalid-url",
        "SUPABASE_DB_PASSWORD": "password"
    }, clear=True)
    def test_invalid_supabase_url_format(self):
        """Test that invalid URL format raises ValueError"""
        with pytest.raises(ValueError) as exc_info:
            get_db_connection()

        assert "Invalid SUPABASE_URL format" in str(exc_info.value)
        assert "Expected format: https://your-project.supabase.co" in str(exc_info.value)

    @patch.dict(os.environ, {
        "SUPABASE_URL": "http://test.supabase.co",  # http instead of https
        "SUPABASE_DB_PASSWORD": "password"
    }, clear=True)
    def test_http_instead_of_https(self):
        """Test that http:// URL is rejected"""
        with pytest.raises(ValueError) as exc_info:
            get_db_connection()

        assert "Invalid SUPABASE_URL format" in str(exc_info.value)

    @patch('run_migration.psycopg2.connect')
    @patch.dict(os.environ, {
        "SUPABASE_URL": "https://testproject.supabase.co",
        "SUPABASE_DB_PASSWORD": "test_password"
    }, clear=True)
    def test_successful_connection(self, mock_connect):
        """Test successful database connection"""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn

        conn = get_db_connection()

        # Verify connection was called with correct parameters
        mock_connect.assert_called_once_with(
            host="db.testproject.supabase.co",
            port=5432,
            database="postgres",
            user="postgres",
            password="test_password",
            sslmode="require"
        )
        assert conn == mock_conn

    @patch('run_migration.psycopg2.connect')
    @patch.dict(os.environ, {
        "SUPABASE_URL": "https://testproject.supabase.co",
        "SUPABASE_DB_PASSWORD": "test_password"
    }, clear=True)
    def test_connection_failure(self, mock_connect):
        """Test database connection failure handling"""
        mock_connect.side_effect = psycopg2.OperationalError("Connection refused")

        with pytest.raises(psycopg2.OperationalError):
            get_db_connection()


class TestRunMigration:
    """Test migration execution functionality"""

    def test_migration_file_not_found(self, tmp_path):
        """Test that missing migration file raises FileNotFoundError"""
        non_existent_file = tmp_path / "does_not_exist.sql"

        with pytest.raises(FileNotFoundError) as exc_info:
            run_migration(non_existent_file)

        assert "Migration file not found" in str(exc_info.value)

    def test_empty_migration_file(self, tmp_path):
        """Test that empty migration file raises ValueError"""
        empty_file = tmp_path / "empty.sql"
        empty_file.touch()

        with pytest.raises(ValueError) as exc_info:
            run_migration(empty_file)

        assert "Migration file is empty" in str(exc_info.value)

    @patch('run_migration.load_env')
    @patch('run_migration.get_db_connection')
    def test_successful_migration(self, mock_get_conn, mock_load_env, tmp_path):
        """Test successful migration execution"""
        # Create a test migration file
        migration_file = tmp_path / "test_migration.sql"
        migration_file.write_text("CREATE TABLE test (id INT);")

        # Mock database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        # Run migration
        run_migration(migration_file)

        # Verify the migration SQL was executed
        mock_cursor.execute.assert_called_once_with("CREATE TABLE test (id INT);")
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('run_migration.load_env')
    @patch('run_migration.get_db_connection')
    def test_migration_sql_error_rollback(self, mock_get_conn, mock_load_env, tmp_path):
        """Test that SQL errors trigger rollback"""
        # Create a test migration file
        migration_file = tmp_path / "test_migration.sql"
        migration_file.write_text("INVALID SQL;")

        # Mock database connection and cursor with SQL error
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = psycopg2.Error("SQL syntax error")
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        # Run migration and expect error
        with pytest.raises(psycopg2.Error):
            run_migration(migration_file)

        # Verify rollback was called
        mock_conn.rollback.assert_called_once()
        mock_conn.close.assert_called_once()

    def test_migration_file_read_error(self, tmp_path):
        """Test handling of file read errors"""
        # Create a file with restricted permissions (this test may behave differently on different systems)
        migration_file = tmp_path / "restricted.sql"
        migration_file.write_text("SELECT 1;")

        # Mock the open function to raise an error
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            with pytest.raises(IOError) as exc_info:
                run_migration(migration_file)

            assert "Failed to read migration file" in str(exc_info.value)


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    @patch.dict(os.environ, {
        "SUPABASE_URL": "https://project-with-dashes.supabase.co",
        "SUPABASE_DB_PASSWORD": "password123"
    }, clear=True)
    @patch('run_migration.psycopg2.connect')
    def test_project_ref_with_dashes(self, mock_connect):
        """Test that project references with dashes are handled correctly"""
        mock_connect.return_value = Mock()

        get_db_connection()

        # Verify the host was constructed correctly
        call_kwargs = mock_connect.call_args[1]
        assert call_kwargs['host'] == "db.project-with-dashes.supabase.co"

    @patch.dict(os.environ, {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_DB_PASSWORD": "p@$$w0rd!#%"
    }, clear=True)
    @patch('run_migration.psycopg2.connect')
    def test_special_characters_in_password(self, mock_connect):
        """Test that special characters in password are handled correctly"""
        mock_connect.return_value = Mock()

        get_db_connection()

        # Verify password was passed correctly
        call_kwargs = mock_connect.call_args[1]
        assert call_kwargs['password'] == "p@$$w0rd!#%"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
