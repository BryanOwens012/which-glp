"""
Startup report of the secrets a service receives from Doppler.

Doppler syncs secrets into Railway's production shared variables, and each service
references the ones it reads. `.railway/railway.ts` sets DOPPLER_VARIABLE_NAMES on
every service to the comma-separated names of those references, so the expected
list has one source. At boot a service logs how many arrived and how many did not,
with both name lists. Values are never logged.

A service cannot tell why a secret is missing (absent from Doppler, a failed sync,
a reference to a shared variable that does not exist): it sees only `unset` or
`empty`, and the report says which.

The TypeScript API and the cron functions keep the same report in
`apps/api/src/lib/doppler-report.ts` and inline in `.railway/functions/`; keep
them in sync.
"""

import logging
import os
from dataclasses import dataclass, field
from typing import List, Mapping, Optional

EXPECTED_NAMES_VARIABLE = "DOPPLER_VARIABLE_NAMES"


@dataclass
class DopplerReport:
    """Which expected secrets arrived. `failed` pairs each name with `unset` or `empty`."""

    pulled: List[str] = field(default_factory=list)
    failed: List[str] = field(default_factory=list)
    failure_reasons: dict = field(default_factory=dict)

    @property
    def expected(self) -> int:
        return len(self.pulled) + len(self.failed)


def build_doppler_report(env: Mapping[str, str]) -> Optional[DopplerReport]:
    """
    Compare the expected Doppler secrets against `env`.

    Args:
        env: The process environment (or a stand-in for tests).

    Returns:
        The report, or None when DOPPLER_VARIABLE_NAMES is unset (a local run with
        no Railway config), so there is nothing to check against.
    """
    raw = env.get(EXPECTED_NAMES_VARIABLE)
    if raw is None:
        return None

    names = sorted({name.strip() for name in raw.split(",") if name.strip()})
    report = DopplerReport()
    for name in names:
        value = env.get(name)
        if value is None:
            report.failed.append(name)
            report.failure_reasons[name] = "unset"
        elif value == "":
            report.failed.append(name)
            report.failure_reasons[name] = "empty"
        else:
            report.pulled.append(name)
    return report


def format_doppler_report(report: DopplerReport) -> str:
    """One log line: counts, then the pulled names, then the failed names with reasons."""
    failed = [f"{name} ({report.failure_reasons[name]})" for name in report.failed]
    return (
        f"[doppler] pulled {len(report.pulled)} of {report.expected} secrets, "
        f"{len(report.failed)} failed; pulled={report.pulled} failed={failed}"
    )


def log_doppler_report(logger: logging.Logger, env: Optional[Mapping[str, str]] = None) -> Optional[DopplerReport]:
    """
    Log the startup report: INFO when every secret arrived, WARNING when any failed.

    Returns the report, or None when there is nothing to check (logged at INFO).
    """
    report = build_doppler_report(os.environ if env is None else env)
    if report is None:
        logger.info("[doppler] %s is not set; skipping the secrets report", EXPECTED_NAMES_VARIABLE)
        return None

    level = logging.WARNING if report.failed else logging.INFO
    logger.log(level, format_doppler_report(report))
    return report
