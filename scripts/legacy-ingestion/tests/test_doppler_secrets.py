"""Tests for the boot-time Doppler secret loader (shared/doppler_secrets.py). No network."""

import logging
from urllib.parse import parse_qs, urlparse

from shared.doppler_secrets import (
    LOADED_MARKER,
    DopplerFailure,
    DopplerLoadReport,
    format_doppler_report,
    load_doppler_secrets,
)


def make_fetch(script):
    """A fake fetcher answering each secret name from a script of replies, recording each request."""
    requests = []

    def fetch(url, headers):
        query = parse_qs(urlparse(url).query)
        name = query["name"][0]
        requests.append({"name": name, "query": query, "auth": headers.get("Authorization")})
        reply = (script.get(name) or [(404, None)]).pop(0)
        if reply == "network":
            raise OSError("connection refused")
        return reply

    return fetch, requests


def base_env(**extra):
    env = {"DOPPLER_TOKEN": "dp.st.prd.test-token", "DOPPLER_PROJECT": "whichglp", "DOPPLER_CONFIG": "prd"}
    env.update(extra)
    return env


def ok(value):
    return (200, {"name": "x", "value": {"computed": value}})


LOGGER = logging.getLogger("test_doppler_secrets")
NO_SLEEP = lambda _seconds: None  # noqa: E731


class TestLoadDopplerSecrets:
    def test_pulls_enumerated_secrets_and_reports_failures(self):
        env = base_env(SUPABASE_URL="railway-copy")
        fetch, requests = make_fetch({"SUPABASE_URL": [ok("https://x.supabase.co")], "INTERNAL_API_KEY": [ok("k")]})

        report = load_doppler_secrets(["SUPABASE_URL", "INTERNAL_API_KEY", "MISSING_ONE"], LOGGER, env, fetch, NO_SLEEP)

        assert report.pulled == ["INTERNAL_API_KEY", "SUPABASE_URL"]
        assert report.failed == [DopplerFailure("MISSING_ONE", "not_found")]
        assert env["SUPABASE_URL"] == "https://x.supabase.co"
        assert env["INTERNAL_API_KEY"] == "k"
        assert "MISSING_ONE" not in env
        assert sorted(r["name"] for r in requests) == ["INTERNAL_API_KEY", "MISSING_ONE", "SUPABASE_URL"]
        assert all(r["auth"] == "Bearer dp.st.prd.test-token" for r in requests)
        assert requests[0]["query"]["project"] == ["whichglp"]
        assert requests[0]["query"]["config"] == ["prd"]

    def test_retries_429_and_5xx_then_succeeds(self):
        fetch, requests = make_fetch({"A": [(429, None), (503, None), ok("a")]})

        report = load_doppler_secrets(["A"], LOGGER, base_env(), fetch, NO_SLEEP)

        assert report.pulled == ["A"]
        assert len(requests) == 3

    def test_does_not_retry_a_client_error(self):
        fetch, requests = make_fetch({"A": [(401, None), ok("a")]})

        report = load_doppler_secrets(["A"], LOGGER, base_env(), fetch, NO_SLEEP)

        assert report.failed == [DopplerFailure("A", "error 401")]
        assert len(requests) == 1

    def test_gives_up_after_repeated_network_errors(self):
        fetch, requests = make_fetch({"A": ["network", "network", "network", ok("a")]})

        report = load_doppler_secrets(["A"], LOGGER, base_env(), fetch, NO_SLEEP)

        assert report.failed == [DopplerFailure("A", "error network")]
        assert len(requests) == 3

    def test_empty_value_fails_and_keeps_existing_env(self):
        env = base_env(A="railway-copy")
        fetch, _ = make_fetch({"A": [ok("")]})

        report = load_doppler_secrets(["A"], LOGGER, env, fetch, NO_SLEEP)

        assert report.failed == [DopplerFailure("A", "empty")]
        assert env["A"] == "railway-copy"

    def test_never_requests_an_invalid_name(self):
        fetch, requests = make_fetch({})

        report = load_doppler_secrets(["bad name"], LOGGER, base_env(), fetch, NO_SLEEP)

        assert report.failed == [DopplerFailure("bad name", "invalid_name")]
        assert requests == []

    def test_skips_without_a_token(self, caplog):
        fetch, requests = make_fetch({})
        with caplog.at_level(logging.INFO, logger=LOGGER.name):
            assert load_doppler_secrets(["A"], LOGGER, {}, fetch, NO_SLEEP) is None

        assert requests == []
        assert "DOPPLER_TOKEN is not set" in caplog.text

    def test_loads_once_per_environment(self, caplog):
        env = base_env()
        fetch, requests = make_fetch({"A": [ok("a"), ok("again")]})

        load_doppler_secrets(["A"], LOGGER, env, fetch, NO_SLEEP)
        with caplog.at_level(logging.INFO, logger=LOGGER.name):
            assert load_doppler_secrets(["A"], LOGGER, env, fetch, NO_SLEEP) is None

        assert env[LOADED_MARKER] == "1"
        assert env["A"] == "a"
        assert len(requests) == 1
        assert "already loaded" in caplog.text

    def test_logs_warning_with_names_and_never_a_value(self, caplog):
        fetch, _ = make_fetch({"A": [ok("secret-value-a")], "B": [(404, None)]})
        with caplog.at_level(logging.INFO, logger=LOGGER.name):
            load_doppler_secrets(["A", "B"], LOGGER, base_env(), fetch, NO_SLEEP)

        assert [r.levelno for r in caplog.records] == [logging.WARNING]
        assert caplog.records[0].getMessage() == (
            '[doppler] pulled 1 of 2 secrets, 1 failed; pulled=["A"] failed=["B (not_found)"]'
        )
        assert "secret-value-a" not in caplog.text


class TestFormatDopplerReport:
    def test_matches_the_shared_log_format(self):
        assert format_doppler_report(DopplerLoadReport()) == "[doppler] pulled 0 of 0 secrets, 0 failed; pulled=[] failed=[]"
