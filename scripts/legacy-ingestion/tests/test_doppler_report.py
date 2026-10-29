"""Tests for the startup Doppler secrets report (shared/doppler_report.py)."""

import logging

from shared.doppler_report import (
    build_doppler_report,
    format_doppler_report,
    log_doppler_report,
)


class TestBuildDopplerReport:
    def test_returns_none_without_expected_names(self):
        assert build_doppler_report({"SUPABASE_URL": "x"}) is None

    def test_splits_pulled_unset_and_empty_sorted_and_deduplicated(self):
        report = build_doppler_report(
            {
                "DOPPLER_VARIABLE_NAMES": " SUPABASE_URL,INTERNAL_API_KEY,,MISSING_ONE, BLANK ,SUPABASE_URL",
                "SUPABASE_URL": "https://x.supabase.co",
                "INTERNAL_API_KEY": "k",
                "BLANK": "",
            }
        )

        assert report.pulled == ["INTERNAL_API_KEY", "SUPABASE_URL"]
        assert report.failed == ["BLANK", "MISSING_ONE"]
        assert report.failure_reasons == {"BLANK": "empty", "MISSING_ONE": "unset"}
        assert report.expected == 4

    def test_empty_expected_list_means_nothing_to_pull(self):
        report = build_doppler_report({"DOPPLER_VARIABLE_NAMES": ""})
        assert (report.pulled, report.failed) == ([], [])


class TestFormatDopplerReport:
    def test_states_counts_and_both_name_lists(self):
        report = build_doppler_report({"DOPPLER_VARIABLE_NAMES": "A,B", "A": "v"})
        assert format_doppler_report(report) == (
            "[doppler] pulled 1 of 2 secrets, 1 failed; pulled=['A'] failed=['B (unset)']"
        )


class TestLogDopplerReport:
    def test_warns_on_failure_and_never_logs_a_value(self, caplog):
        logger = logging.getLogger("test_doppler_report.warn")
        with caplog.at_level(logging.INFO, logger=logger.name):
            log_doppler_report(logger, {"DOPPLER_VARIABLE_NAMES": "A,B", "A": "secret-value-a"})

        assert [r.levelno for r in caplog.records] == [logging.WARNING]
        assert "pulled 1 of 2 secrets, 1 failed" in caplog.text
        assert "secret-value-a" not in caplog.text

    def test_logs_info_when_everything_arrived(self, caplog):
        logger = logging.getLogger("test_doppler_report.info")
        with caplog.at_level(logging.INFO, logger=logger.name):
            log_doppler_report(logger, {"DOPPLER_VARIABLE_NAMES": "A", "A": "v"})

        assert [r.levelno for r in caplog.records] == [logging.INFO]
        assert "pulled 1 of 1 secrets, 0 failed" in caplog.text

    def test_skips_when_no_expected_list(self, caplog):
        logger = logging.getLogger("test_doppler_report.skip")
        with caplog.at_level(logging.INFO, logger=logger.name):
            assert log_doppler_report(logger, {}) is None

        assert "skipping the secrets report" in caplog.text
