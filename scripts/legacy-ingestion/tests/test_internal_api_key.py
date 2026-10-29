"""Tests for fail-closed service-to-service auth (shared/internal_api_key.py). No network."""

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from shared.internal_api_key import (
    make_internal_api_key_verifier,
    parse_internal_api_key,
    require_internal_api_key,
)

KEY = "internal-test-key-123"


def make_client(expected: str = KEY) -> TestClient:
    """A one-route app guarded exactly the way the services guard theirs."""
    app = FastAPI()
    verify = make_internal_api_key_verifier(expected)

    @app.get("/guarded")
    async def guarded(_: None = Depends(verify)):
        return {"ok": True}

    return TestClient(app)


class TestParseInternalApiKey:
    def test_accepts_a_key_without_whitespace(self):
        assert parse_internal_api_key(KEY) == KEY

    @pytest.mark.parametrize(
        ("raw", "message"),
        [
            (None, "Missing INTERNAL_API_KEY"),
            ("", "Missing INTERNAL_API_KEY"),
            ("abc\n", "contains whitespace"),
            ("abc\r", "contains whitespace"),
            ("ab c", "contains whitespace"),
        ],
    )
    def test_refuses_an_unusable_key(self, raw, message):
        with pytest.raises(RuntimeError, match=message):
            parse_internal_api_key(raw)

    def test_require_reads_the_environment(self):
        assert require_internal_api_key({"INTERNAL_API_KEY": KEY}) == KEY
        with pytest.raises(RuntimeError, match="Missing INTERNAL_API_KEY"):
            require_internal_api_key({})


class TestVerifier:
    def test_cannot_be_built_around_an_empty_key(self):
        with pytest.raises(RuntimeError, match="Missing INTERNAL_API_KEY"):
            make_internal_api_key_verifier("")

    def test_allows_the_exact_key(self):
        response = make_client().get("/guarded", headers={"x-internal-api-key": KEY})
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "headers",
        [
            {},
            {"x-internal-api-key": ""},
            {"x-internal-api-key": "wrong"},
            {"x-internal-api-key": KEY + "x"},
            {"x-internal-api-key": KEY[:-1]},
            {"x-internal-api-key": KEY.upper()},
        ],
        ids=["missing", "empty", "wrong", "longer", "shorter", "different-case"],
    )
    def test_denies_anything_else(self, headers):
        response = make_client().get("/guarded", headers=headers)
        assert response.status_code == 403
        assert response.json() == {"detail": "Forbidden"}

    def test_denies_when_the_check_itself_fails(self, monkeypatch):
        import shared.internal_api_key as module

        def broken_compare(*_args):
            raise TypeError("comparison failed")

        monkeypatch.setattr(module.hmac, "compare_digest", broken_compare)
        response = make_client().get("/guarded", headers={"x-internal-api-key": KEY})
        assert response.status_code == 403
