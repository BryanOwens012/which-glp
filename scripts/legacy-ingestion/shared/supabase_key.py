"""
Supabase secret-key validation and log redaction (Supabase secret keys and Doppler
tokens) for the Python services.

Every Python service authenticates to Supabase with a secret key
(``sb_secret_...``), which maps to the ``service_role`` Postgres role. A
publishable key maps to ``anon``, which has no grants here, and a legacy
``service_role`` JWT (``eyJ...``) is being retired by Supabase, so both are
rejected at startup instead of failing at the first query.

The TypeScript API keeps the same two rules in ``apps/api/src/lib/config.ts``
(``parseSupabaseSecretKey``) and ``apps/api/src/lib/redact.ts``; keep all three
in sync.

Reference: https://supabase.com/docs/guides/api/api-keys
"""

import logging
import re
import traceback
from typing import Optional

# A valid key is the prefix followed by at least one non-whitespace character.
# The redaction pattern is a superset of it, so whatever passes validation is
# masked in full.
_VALID_SECRET_KEY = re.compile(r"sb_secret_\S+")
_SECRET_KEY_PATTERN = re.compile(r"sb_secret_\S*")
REDACTED = "sb_secret_[REDACTED]"

# Doppler tokens: service (st), CLI (ct), personal (pt), service account (sa), SCIM and audit.
_DOPPLER_TOKEN_PATTERN = re.compile(r"dp\.(?:st|ct|pt|sa|scim|audit)\.\S+")
DOPPLER_REDACTED = "dp.[REDACTED]"


class SupabaseKeyError(ValueError):
    """Raised when SUPABASE_SECRET_KEY is missing or is not a secret key."""


def require_supabase_secret_key(raw: Optional[str]) -> str:
    """
    Validate a ``SUPABASE_SECRET_KEY`` value and return it unchanged.

    Args:
        raw: The environment value, or None when unset.

    Returns:
        The key, when it is a Supabase secret key.

    Raises:
        SupabaseKeyError: When the key is missing, is not a secret key, is the
            bare prefix, or carries whitespace anywhere (a CR or space from a
            pasted ``.env`` line would otherwise reach the request header).
    """
    if not raw:
        raise SupabaseKeyError("Missing SUPABASE_SECRET_KEY environment variable")

    if not _VALID_SECRET_KEY.fullmatch(raw):
        raise SupabaseKeyError(
            'Invalid SUPABASE_SECRET_KEY: expected a Supabase secret key starting with "sb_secret_" '
            "(not a publishable key or a legacy service_role JWT)"
        )

    return raw


def redact_secrets(text: str) -> str:
    """Mask every Supabase secret key and Doppler token in ``text``."""
    return _DOPPLER_TOKEN_PATTERN.sub(DOPPLER_REDACTED, _SECRET_KEY_PATTERN.sub(REDACTED, text))


def _redact_record(record: logging.LogRecord) -> logging.LogRecord:
    """Mask secrets (Supabase keys, Doppler tokens) in a record's message, traceback, and stack text."""
    try:
        message = record.getMessage()
    except Exception:
        # A malformed format string must still reach the handler, which reports
        # it the way stock logging does.
        message = None

    if message is not None:
        redacted = redact_secrets(message)
        if redacted != message:
            record.msg = redacted
            record.args = None

    # Formatters render exc_info only when exc_text is unset, so filling
    # exc_text with the masked traceback is what keeps the key out of it.
    if record.exc_info and not record.exc_text:
        exc_text = "".join(traceback.format_exception(*record.exc_info)).rstrip("\n")
        record.exc_text = redact_secrets(exc_text)

    if record.stack_info:
        record.stack_info = redact_secrets(record.stack_info)

    return record


_is_installed = False


def install_log_redaction() -> None:
    """
    Mask secrets (Supabase secret keys, Doppler tokens) in every log record this process creates.

    Installed as a log-record factory rather than a handler filter, so it covers
    records from every logger (httpx, uvicorn, third-party clients), whichever
    handler later emits them. It covers the logging module only: text written
    with ``print`` or straight to stdout is not masked. Idempotent.
    """
    global _is_installed
    if _is_installed:
        return

    previous = logging.getLogRecordFactory()

    def factory(*args, **kwargs):
        return _redact_record(previous(*args, **kwargs))

    logging.setLogRecordFactory(factory)
    _is_installed = True
