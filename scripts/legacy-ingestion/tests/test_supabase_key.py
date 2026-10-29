"""
Tests for Supabase secret-key validation and log redaction (shared/supabase_key.py),
and for Database() refusing a wrong key before it builds a client.

The Database tests stub ``supabase`` and ``dotenv``: the stub ``load_dotenv`` keeps
the repo's real ``.env`` out of the environment under test, and the stub
``create_client`` records the key it was given without any network call.
"""

import importlib
import logging
import sys
import types

import pytest

from shared.supabase_key import (
    SupabaseKeyError,
    install_log_redaction,
    redact_supabase_secrets,
    require_supabase_secret_key,
)

VALID_KEY = "sb_secret_abc123"

INVALID_KEYS = [
    pytest.param("sb_publishable_abc123", id="publishable"),
    pytest.param("eyJhbGciOiJIUzI1NiJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIn0.sig", id="legacy-jwt"),
    pytest.param(" sb_secret_abc123", id="leading-space"),
    pytest.param("sb_secret_abc123\r", id="trailing-cr"),
    pytest.param("sb_secret_abc 123", id="inner-space"),
    pytest.param('"sb_secret_abc123"', id="quoted"),
    pytest.param("sb_secret_", id="bare-prefix"),
]


class TestRequireSupabaseSecretKey:
    def test_accepts_secret_key(self):
        assert require_supabase_secret_key(VALID_KEY) == VALID_KEY

    @pytest.mark.parametrize("raw", [None, ""])
    def test_rejects_missing(self, raw):
        with pytest.raises(SupabaseKeyError, match="Missing SUPABASE_SECRET_KEY"):
            require_supabase_secret_key(raw)

    @pytest.mark.parametrize("raw", INVALID_KEYS)
    def test_rejects_invalid(self, raw):
        with pytest.raises(SupabaseKeyError, match="Invalid SUPABASE_SECRET_KEY"):
            require_supabase_secret_key(raw)


class TestRedaction:
    def test_masks_every_secret_key(self):
        assert redact_supabase_secrets("a sb_secret_x-1_2 b sb_secret_y") == (
            "a sb_secret_[REDACTED] b sb_secret_[REDACTED]"
        )

    def test_leaves_publishable_keys_alone(self):
        assert redact_supabase_secrets("sb_publishable_abc") == "sb_publishable_abc"

    def test_log_records_are_masked(self, caplog):
        install_log_redaction()
        logger = logging.getLogger("test_supabase_key.redaction")
        with caplog.at_level(logging.INFO, logger=logger.name):
            logger.info("connecting with %s", "sb_secret_live123")
            logger.info("no secret %d", 7)

        messages = [record.getMessage() for record in caplog.records]
        assert messages == ["connecting with sb_secret_[REDACTED]", "no secret 7"]
        assert "sb_secret_live123" not in caplog.text


@pytest.fixture
def database_module(monkeypatch):
    """Import shared.database against stub supabase/dotenv modules."""
    created_with = []

    supabase_stub = types.ModuleType("supabase")
    supabase_stub.Client = object
    supabase_stub.create_client = lambda url, key: created_with.append((url, key)) or object()
    dotenv_stub = types.ModuleType("dotenv")
    dotenv_stub.load_dotenv = lambda *args, **kwargs: False

    monkeypatch.setitem(sys.modules, "supabase", supabase_stub)
    monkeypatch.setitem(sys.modules, "dotenv", dotenv_stub)
    monkeypatch.delitem(sys.modules, "shared.database", raising=False)
    for name in ("SUPABASE_URL", "SUPABASE_SECRET_KEY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")

    module = importlib.import_module("shared.database")
    yield module, created_with
    sys.modules.pop("shared.database", None)


class TestDatabaseKeyCheck:
    def test_builds_client_with_secret_key(self, database_module, monkeypatch):
        module, created_with = database_module
        monkeypatch.setenv("SUPABASE_SECRET_KEY", VALID_KEY)

        module.Database()

        assert created_with == [("https://example.supabase.co", VALID_KEY)]

    def test_rejects_missing_key(self, database_module):
        module, created_with = database_module

        with pytest.raises(module.DatabaseConfigurationError, match="SUPABASE_SECRET_KEY"):
            module.Database()
        assert created_with == []

    @pytest.mark.parametrize("raw", INVALID_KEYS)
    def test_rejects_invalid_key_before_creating_client(self, database_module, monkeypatch, raw):
        module, created_with = database_module
        monkeypatch.setenv("SUPABASE_SECRET_KEY", raw)

        with pytest.raises(module.DatabaseConfigurationError, match="Invalid SUPABASE_SECRET_KEY"):
            module.Database()
        assert created_with == []
