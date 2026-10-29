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
import math
import os
import random
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
MAX_RETRY_AFTER_SECONDS = 5  # a Retry-After header is honored up to this cap

# Set after a load so a second import of the same module does not fetch and report
# again. Python-only: rec-engine starts with `python3 api.py`, whose
# `uvicorn.run("api:app")` imports the module a second time in the same process; the
# TypeScript entry points never load twice.
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


# (url, headers) -> (HTTP status, parsed JSON body or None[, Retry-After header]); any
# exception counts as a network failure.
Fetcher = Callable[[str, dict], tuple]


class _RefuseRedirects(urllib.request.HTTPRedirectHandler):
    """Never follow a redirect: urllib would resend the bearer token to the new host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_RefuseRedirects)


def _fetch_json(url: str, headers: dict) -> tuple:
    request = urllib.request.Request(url, headers=headers)
    try:
        with _OPENER.open(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        retry_after = error.headers.get("Retry-After")
        error.close()
        return error.code, None, retry_after


def _retry_delay(attempt: int, retry_after: Optional[str]) -> float:
    """Exponential backoff with jitter, or the server's Retry-After (seconds) up to a cap."""
    if retry_after is not None:
        try:
            seconds = float(retry_after)
        except ValueError:
            seconds = math.nan
        if math.isfinite(seconds):  # "nan"/"inf" would reach time.sleep and crash the boot
            return min(max(seconds, 0.0), MAX_RETRY_AFTER_SECONDS)
    return RETRY_BASE_DELAY_SECONDS * 4 ** (attempt - 1) * random.uniform(1.0, 1.5)


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
        retry_after = None
        try:
            result = fetch(_build_secret_url(name, env), headers)
            status, body = result[0], result[1]
            retry_after = result[2] if len(result) > 2 else None
        except Exception:  # any transport or parse failure: retry, then report, never crash the boot
            last_reason = "error network"
        else:
            if 200 <= status < 300:
                secret = body.get("value") if isinstance(body, dict) else None
                value = secret.get("computed") if isinstance(secret, dict) else None
                if not isinstance(value, str) or value == "":
                    return name, None, "empty"
                return name, value, None
            if status == 404:
                return name, None, "not_found"
            last_reason = f"error {status}"
            if not (status == 429 or status >= 500):
                return name, None, last_reason
        if attempt < MAX_ATTEMPTS:
            sleep(_retry_delay(attempt, retry_after))
    return name, None, last_reason


def format_doppler_report(report: DopplerLoadReport) -> str:
    """One log line: counts, then the pulled names, then the failed names with reasons (JSON lists)."""
    failed = [f"{failure.name} ({failure.reason})" for failure in report.failed]
    expected = len(report.pulled) + len(report.failed)
    return (
        f"[doppler] pulled {len(report.pulled)} of {expected} secrets, {len(report.failed)} failed; "
        f"pulled={json.dumps(report.pulled, separators=(',', ':'), ensure_ascii=False)} "
        f"failed={json.dumps(failed, separators=(',', ':'), ensure_ascii=False)}"
    )


def ensure_report_logger() -> logging.Logger:
    """
    The `doppler` logger, made able to print at INFO.

    The services' own loggers have no handler at module load (only uvicorn configures
    logging), so their INFO lines are dropped. Attach a stdout handler only when no
    handler exists anywhere up this logger's chain, so a configured root (rec-engine's
    basicConfig, pytest's capture) is used as-is. When it attaches its own handler it
    stops propagating, so a root configured later cannot print the line twice. Kept
    free of `shared.config` because rec-engine imports this module without `shared`.
    """
    report_logger = logging.getLogger("doppler")
    report_logger.setLevel(logging.INFO)
    if not report_logger.hasHandlers():
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
        report_logger.addHandler(handler)
        report_logger.propagate = False
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
    logger = ensure_report_logger() if logger is None else logger
    if env.get(LOADED_MARKER) == "1":
        logger.info("[doppler] secrets already loaded in this environment; skipping")
        return None
    token = env.get("DOPPLER_TOKEN")
    if not token:
        # On Railway every service is given DOPPLER_TOKEN, so its absence is a misconfiguration.
        on_railway = bool(env.get("RAILWAY_ENVIRONMENT_NAME"))
        logger.log(
            logging.WARNING if on_railway else logging.INFO,
            "[doppler] DOPPLER_TOKEN is not set; skipping the Doppler load (%s)",
            "running on existing environment values" if on_railway else "local .env applies",
        )
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
