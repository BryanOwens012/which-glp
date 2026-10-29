"""
Load a service's secrets from Doppler at boot, and report what arrived.

Each backend service fetches only the secret names it enumerates, one request per
name, with the environment's single DOPPLER_TOKEN (plus DOPPLER_PROJECT and
DOPPLER_CONFIG). Pulled values are written into `os.environ` for this process only,
overriding any Railway-provided copy; nothing outside the enumerated list is
requested or accepted. The boot log gives how many were pulled and how many failed,
with both name lists and a reason per failure, never a value. Without DOPPLER_TOKEN
(local development) the load is skipped and `.env` applies as before.

Backend only: the frontend reads public `NEXT_PUBLIC_*` config from ordinary
environment variables and never talks to Doppler.

The TypeScript API keeps the same loader in `apps/api/src/lib/doppler-secrets.ts`,
and the cron functions in `.railway/functions/_doppler-secrets.ts`; keep the three in
sync, log format included.

API reference: https://docs.doppler.com/reference/secrets-get
"""

import json
import logging
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Callable, Iterable, List, MutableMapping, Optional

DOPPLER_SECRET_URL = "https://api.doppler.com/v3/configs/config/secret"

# A secret name as Doppler and the shell accept it; anything else is never requested.
SECRET_NAME_PATTERN = re.compile(r"[A-Z][A-Z0-9_]*")

REQUEST_TIMEOUT_SECONDS = 5
MAX_ATTEMPTS = 3  # 429 and 5xx responses and network errors are retried
RETRY_BASE_DELAY_SECONDS = 0.25

# Set after a load so a re-import in the same process, or a child process that
# inherits this environment (uvicorn's reloader), does not fetch and report again.
LOADED_MARKER = "DOPPLER_SECRETS_LOADED"


@dataclass(frozen=True)
class DopplerFailure:
    """A secret that was not pulled, and why (not_found, empty, invalid_name, error <status>, error network)."""

    name: str
    reason: str


@dataclass
class DopplerLoadReport:
    pulled: List[str] = field(default_factory=list)
    failed: List[DopplerFailure] = field(default_factory=list)


# (name, url, headers) -> (HTTP status, parsed JSON body or None); raises OSError on a network failure.
Fetcher = Callable[[str, dict], "tuple[int, Optional[dict]]"]


def _fetch_json(url: str, headers: dict) -> "tuple[int, Optional[dict]]":
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, None


def _build_secret_url(name: str, env: MutableMapping[str, str]) -> str:
    params = {"name": name}
    if env.get("DOPPLER_PROJECT"):
        params["project"] = env["DOPPLER_PROJECT"]
    if env.get("DOPPLER_CONFIG"):
        params["config"] = env["DOPPLER_CONFIG"]
    return f"{DOPPLER_SECRET_URL}?{urllib.parse.urlencode(params)}"


def _fetch_secret(name: str, token: str, env, fetch: Fetcher, sleep) -> "tuple[str, Optional[str], Optional[str]]":
    """Return (name, value, None) on success or (name, None, reason) on failure."""
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    last_reason = "error network"
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            status, body = fetch(_build_secret_url(name, env), headers)
        except (OSError, ValueError):
            last_reason = "error network"
        else:
            if 200 <= status < 300:
                value = ((body or {}).get("value") or {}).get("computed")
                if not isinstance(value, str) or value == "":
                    return name, None, "empty"
                return name, value, None
            if status == 404:
                return name, None, "not_found"
            last_reason = f"error {status}"
            if not (status == 429 or status >= 500):
                return name, None, last_reason
        if attempt < MAX_ATTEMPTS:
            sleep(RETRY_BASE_DELAY_SECONDS * 4 ** (attempt - 1))
    return name, None, last_reason


def format_doppler_report(report: DopplerLoadReport) -> str:
    """One log line: counts, then the pulled names, then the failed names with reasons (JSON lists)."""
    failed = [f"{failure.name} ({failure.reason})" for failure in report.failed]
    expected = len(report.pulled) + len(report.failed)
    return (
        f"[doppler] pulled {len(report.pulled)} of {expected} secrets, {len(report.failed)} failed; "
        f"pulled={json.dumps(report.pulled, separators=(',', ':'))} "
        f"failed={json.dumps(failed, separators=(',', ':'))}"
    )


def get_report_logger() -> logging.Logger:
    """
    The `doppler` logger, made able to print at INFO.

    The services' own loggers have no handler at module load (only uvicorn configures
    logging), so their INFO lines are dropped. Attach a stdout handler only when no
    handler exists anywhere up this logger's chain, so a configured root (rec-engine's
    basicConfig, pytest's capture) is used as-is and nothing prints twice.
    """
    report_logger = logging.getLogger("doppler")
    report_logger.setLevel(logging.INFO)
    if not report_logger.hasHandlers():
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
        report_logger.addHandler(handler)
    return report_logger


def load_doppler_secrets(
    names: Iterable[str],
    logger: Optional[logging.Logger] = None,
    env: Optional[MutableMapping[str, str]] = None,
    fetch: Fetcher = _fetch_json,
    sleep=time.sleep,
) -> Optional[DopplerLoadReport]:
    """
    Fetch `names` from Doppler, write the pulled values into `env`, and log the report:
    INFO when every secret arrived, WARNING when any failed.

    Returns None, after logging why, when DOPPLER_TOKEN is not set or this environment
    already holds a load (a re-import or an inheriting child process).
    """
    env = os.environ if env is None else env
    logger = get_report_logger() if logger is None else logger
    if env.get(LOADED_MARKER) == "1":
        logger.info("[doppler] secrets already loaded in this environment; skipping")
        return None
    token = env.get("DOPPLER_TOKEN")
    if not token:
        logger.info("[doppler] DOPPLER_TOKEN is not set; skipping the Doppler load (local .env applies)")
        return None

    report = DopplerLoadReport()
    requested = []
    for name in sorted(set(names)):
        if SECRET_NAME_PATTERN.fullmatch(name):
            requested.append(name)
        else:
            report.failed.append(DopplerFailure(name, "invalid_name"))

    with ThreadPoolExecutor(max_workers=max(1, len(requested))) as pool:
        outcomes = list(pool.map(lambda name: _fetch_secret(name, token, env, fetch, sleep), requested))

    for name, value, reason in outcomes:
        if value is not None:
            env[name] = value
            report.pulled.append(name)
        else:
            report.failed.append(DopplerFailure(name, reason))
    report.failed.sort(key=lambda failure: failure.name)
    env[LOADED_MARKER] = "1"

    logger.log(logging.WARNING if report.failed else logging.INFO, format_doppler_report(report))
    return report
