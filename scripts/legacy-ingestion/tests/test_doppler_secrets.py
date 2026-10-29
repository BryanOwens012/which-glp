"""Tests for the boot-time Doppler secret loader (shared/doppler_secrets.py). No network."""

import json
import logging
import pathlib
import sys
from urllib.parse import parse_qs, urlparse

import pytest

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
def skip_sleep(_seconds):
    """Skip the retry backoff in tests."""


class TestLoadDopplerSecrets:
    def test_pulls_enumerated_secrets_and_reports_failures(self):
        env = base_env(SUPABASE_URL="railway-copy")
        fetch, requests = make_fetch({"SUPABASE_URL": [ok("https://x.supabase.co")], "INTERNAL_API_KEY": [ok("k")]})

        report = load_doppler_secrets(["SUPABASE_URL", "INTERNAL_API_KEY", "MISSING_ONE"], LOGGER, env, fetch, skip_sleep)

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

        report = load_doppler_secrets(["A"], LOGGER, base_env(), fetch, skip_sleep)

        assert report.pulled == ["A"]
        assert len(requests) == 3

    def test_does_not_retry_a_client_error(self):
        fetch, requests = make_fetch({"A": [(401, None), ok("a")]})

        report = load_doppler_secrets(["A"], LOGGER, base_env(), fetch, skip_sleep)

        assert report.failed == [DopplerFailure("A", "error 401")]
        assert len(requests) == 1

    def test_gives_up_after_repeated_network_errors(self):
        fetch, requests = make_fetch({"A": ["network", "network", "network", ok("a")]})

        report = load_doppler_secrets(["A"], LOGGER, base_env(), fetch, skip_sleep)

        assert report.failed == [DopplerFailure("A", "error network")]
        assert len(requests) == 3

    def test_empty_value_fails_and_keeps_existing_env(self):
        env = base_env(A="railway-copy")
        fetch, _ = make_fetch({"A": [ok("")]})

        report = load_doppler_secrets(["A"], LOGGER, env, fetch, skip_sleep)

        assert report.failed == [DopplerFailure("A", "empty")]
        assert env["A"] == "railway-copy"

    def test_never_requests_an_invalid_name(self):
        fetch, requests = make_fetch({})

        report = load_doppler_secrets(["bad name"], LOGGER, base_env(), fetch, skip_sleep)

        assert report.failed == [DopplerFailure("bad name", "invalid_name")]
        assert requests == []

    def test_skips_without_a_token(self, caplog):
        fetch, requests = make_fetch({})
        with caplog.at_level(logging.INFO, logger=LOGGER.name):
            assert load_doppler_secrets(["A"], LOGGER, {}, fetch, skip_sleep) is None

        assert requests == []
        assert "DOPPLER_TOKEN is not set" in caplog.text

    def test_loads_once_per_environment(self, caplog):
        env = base_env()
        fetch, requests = make_fetch({"A": [ok("a"), ok("again")]})

        load_doppler_secrets(["A"], LOGGER, env, fetch, skip_sleep)
        with caplog.at_level(logging.INFO, logger=LOGGER.name):
            assert load_doppler_secrets(["A"], LOGGER, env, fetch, skip_sleep) is None

        assert env[LOADED_MARKER] == "1"
        assert env["A"] == "a"
        assert len(requests) == 1
        assert "already loaded" in caplog.text

    def test_logs_warning_with_names_and_never_a_value(self, caplog):
        fetch, _ = make_fetch({"A": [ok("secret-value-a")], "B": [(404, None)]})
        with caplog.at_level(logging.INFO, logger=LOGGER.name):
            load_doppler_secrets(["A", "B"], LOGGER, base_env(), fetch, skip_sleep)

        assert [r.levelno for r in caplog.records] == [logging.WARNING]
        assert caplog.records[0].getMessage() == (
            '[doppler] pulled 1 of 2 secrets, 1 failed; pulled=["A"] failed=["B (not_found)"]'
        )
        assert "secret-value-a" not in caplog.text


class TestLoaderHardening:
    def test_any_exception_is_retried_and_reported_never_raised(self):
        import http.client

        calls = []

        def fetch(url, headers):
            calls.append(url)
            raise http.client.IncompleteRead(b"partial")

        report = load_doppler_secrets(["A"], LOGGER, base_env(), fetch, skip_sleep)

        assert report.failed == [DopplerFailure("A", "error network")]
        assert len(calls) == 3

    def test_non_object_body_counts_as_empty(self):
        fetch, _ = make_fetch({"A": [(200, ["not", "an", "object"])]})

        report = load_doppler_secrets(["A"], LOGGER, base_env(), fetch, skip_sleep)

        assert report.failed == [DopplerFailure("A", "empty")]

    def test_retry_after_is_honored_and_capped(self):
        delays = []
        fetch, _ = make_fetch({"A": [(429, None, "2"), (503, None, "120"), ok("a")]})

        report = load_doppler_secrets(["A"], LOGGER, base_env(), fetch, delays.append)

        assert report.pulled == ["A"]
        assert delays == [2.0, 5]

    def test_non_finite_retry_after_falls_back_to_backoff(self):
        delays = []
        fetch, _ = make_fetch({"A": [(429, None, "nan"), (503, None, "inf"), ok("a")]})

        report = load_doppler_secrets(["A"], LOGGER, base_env(), fetch, delays.append)

        assert report.pulled == ["A"]
        assert 0.25 <= delays[0] <= 0.375 and 1.0 <= delays[1] <= 1.5

    def test_missing_token_on_railway_warns(self, caplog):
        fetch, requests = make_fetch({})
        with caplog.at_level(logging.INFO, logger=LOGGER.name):
            load_doppler_secrets(["A"], LOGGER, {"RAILWAY_ENVIRONMENT_NAME": "production"}, fetch, skip_sleep)

        assert requests == []
        assert [r.levelno for r in caplog.records] == [logging.WARNING]

    def test_redirects_are_refused(self):
        from shared.doppler_secrets import _RefuseRedirects

        assert _RefuseRedirects().redirect_request(None, None, 302, "Found", {}, "https://elsewhere.example/") is None


GOLDEN_CASES = json.loads(
    (pathlib.Path(__file__).parent / "fixtures" / "doppler-log-format.json").read_text(encoding="utf-8")
)


class TestFormatDopplerReport:
    @pytest.mark.parametrize("case", GOLDEN_CASES, ids=lambda case: case["line"][:40])
    def test_matches_the_shared_golden_line(self, case):
        report = DopplerLoadReport(
            pulled=case["pulled"], failed=[DopplerFailure(f["name"], f["reason"]) for f in case["failed"]]
        )
        assert format_doppler_report(report) == case["line"]


class TestOrdering:
    def test_sorts_failures_in_code_point_order_like_the_ts_loader(self):
        report = load_doppler_secrets(["Z", "A_B", "AB"], LOGGER, base_env(), make_fetch({})[0], skip_sleep)
        assert [f.name for f in report.failed] == ["AB", "A_B", "Z"]


class TestTiming:
    def test_backs_off_with_jitter_and_not_after_the_last_attempt(self):
        delays = []
        fetch, _ = make_fetch({"A": [(503, None), (503, None), (503, None)]})

        load_doppler_secrets(["A"], LOGGER, base_env(), fetch, delays.append)

        assert len(delays) == 2
        assert 0.25 <= delays[0] <= 0.375
        assert 1.0 <= delays[1] <= 1.5

    def test_requests_are_bounded_by_the_timeout(self, monkeypatch):
        import shared.doppler_secrets as module

        seen = {}

        class FakeResponse:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def read(self):
                return b'{"value": {"computed": "a"}}'

        def fake_open(request, timeout=None):
            seen["timeout"] = timeout
            return FakeResponse()

        monkeypatch.setattr(module._OPENER, "open", fake_open)
        assert module._fetch_json("https://api.doppler.com/x", {})[0] == 200
        assert seen["timeout"] == module.REQUEST_TIMEOUT_SECONDS


class TestLoadedMarker:
    def test_not_set_when_the_load_is_skipped(self):
        env = {}
        load_doppler_secrets(["A"], LOGGER, env, make_fetch({})[0], skip_sleep)
        assert LOADED_MARKER not in env

    def test_set_even_after_a_total_outage(self):
        # A re-import does not retry a failed load; the next process start does.
        env = base_env()
        load_doppler_secrets(["A"], LOGGER, env, make_fetch({"A": ["network"] * 3})[0], skip_sleep)
        assert env[LOADED_MARKER] == "1"


class TestEnsureReportLogger:
    @pytest.fixture
    def fresh_doppler_logger(self, monkeypatch):
        """Isolate the `doppler` logger and the root handlers for one test."""
        doppler = logging.getLogger("doppler")
        root = logging.getLogger()
        monkeypatch.setattr(doppler, "handlers", [])
        monkeypatch.setattr(doppler, "propagate", True)
        monkeypatch.setattr(root, "handlers", [])
        yield doppler

    def test_prints_once_with_no_logging_configured(self, fresh_doppler_logger, capsys, monkeypatch):
        from shared.doppler_secrets import ensure_report_logger

        # pytest attaches its capture handler to the root at the start of the test body.
        monkeypatch.setattr(logging.getLogger(), "handlers", [])
        ensure_report_logger().info("hello")
        ensure_report_logger().info("again")

        assert capsys.readouterr().out == "INFO doppler: hello\nINFO doppler: again\n"
        assert len(fresh_doppler_logger.handlers) == 1
        assert fresh_doppler_logger.propagate is False

    def test_uses_a_configured_root_without_adding_a_handler(self, fresh_doppler_logger, capsys):
        from shared.doppler_secrets import ensure_report_logger

        root_handler = logging.StreamHandler(sys.stdout)
        logging.getLogger().addHandler(root_handler)
        ensure_report_logger().info("hello")

        assert fresh_doppler_logger.handlers == []
        assert capsys.readouterr().out.count("hello") == 1
