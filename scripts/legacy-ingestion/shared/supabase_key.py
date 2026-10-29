"""
Supabase secret-key validation and log redaction for the Python services.

Every Python service authenticates to Supabase with a secret key
(``sb_secret_...``), which maps to the ``service_role`` Postgres role. A
publishable key maps to ``anon``, which has no grants here, and a legacy
``service_role`` JWT (``eyJ...``) is being retired by Supabase, so both are
rejected at startup instead of failing at the first query.

The TypeScript API keeps the same rule in ``apps/api/src/lib/config.ts``
(``parseSupabaseSecretKey``) and the same redaction in
``apps/api/src/lib/redact.ts``; keep the three in sync.

Reference: https://supabase.com/docs/guides/api/api-keys
"""

import logging
import re
from typing import Optional

SECRET_KEY_PREFIX = "sb_secret_"

# The redaction pattern is deliberately broader than a valid key: anything that
# starts with the prefix is masked, whatever follows it.
_SECRET_KEY_PATTERN = re.compile(r"sb_secret_[A-Za-z0-9_\-]*")
REDACTED = "sb_secret_[REDACTED]"


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
        SupabaseKeyError: When the key is missing, carries whitespace (a CR or
            quote from a pasted ``.env`` line would otherwise reach the request
            header), is the bare prefix, or is not a secret key at all.
    """
    if not raw:
        raise SupabaseKeyError("Missing SUPABASE_SECRET_KEY environment variable")

    if (
        raw != raw.strip()
        or any(ch.isspace() for ch in raw)
        or not raw.startswith(SECRET_KEY_PREFIX)
        or raw == SECRET_KEY_PREFIX
    ):
        raise SupabaseKeyError(
            'Invalid SUPABASE_SECRET_KEY: expected a Supabase secret key starting with "sb_secret_" '
            "(not a publishable key or a legacy service_role JWT)"
        )

    return raw


def redact_supabase_secrets(text: str) -> str:
    """Mask every Supabase secret key in ``text``."""
    return _SECRET_KEY_PATTERN.sub(REDACTED, text)


_previous_factory = None


def install_log_redaction() -> None:
    """
    Mask Supabase secret keys in every log record this process creates.

    Installed as a log-record factory rather than a handler filter, so it covers
    records from every logger (httpx, uvicorn, third-party clients), whichever
    handler later emits them. Idempotent: a second call does nothing.
    """
    global _previous_factory
    if _previous_factory is not None:
        return

    _previous_factory = logging.getLogRecordFactory()
    previous = _previous_factory

    def factory(*args, **kwargs):
        record = previous(*args, **kwargs)
        try:
            message = record.getMessage()
        except Exception:
            # A malformed format string must still log; leave the record as-is.
            return record
        redacted = redact_supabase_secrets(message)
        if redacted != message:
            record.msg = redacted
            record.args = None
        return record

    logging.setLogRecordFactory(factory)
