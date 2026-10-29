"""
Service-to-service authentication with INTERNAL_API_KEY, failing closed.

Every Python service's internal endpoints require the `x-internal-api-key` header to
equal the service's INTERNAL_API_KEY, which it loads from Doppler at boot. A service
without a usable key refuses to start (`require_internal_api_key`, called at module
level right after the Doppler load), and a request is allowed only when its header
matches exactly; a missing or wrong header, or any error while checking, is denied.

The API applies the same rule to the key it sends (`parseInternalApiKey` in
`apps/api/src/lib/config.ts`); keep the two in sync.
"""

import hmac
import logging
import os
from typing import Awaitable, Callable, Mapping, Optional

from fastapi import Header, HTTPException

logger = logging.getLogger(__name__)


def parse_internal_api_key(raw: Optional[str]) -> str:
    """
    Return `raw` if it is usable as INTERNAL_API_KEY, else raise RuntimeError.

    A missing or empty key is refused, and so is one containing whitespace (a CR or
    space from a pasted value), which no caller would ever send and so would deny
    every request while looking configured.
    """
    if not raw:
        raise RuntimeError("Missing INTERNAL_API_KEY environment variable; refusing to start")
    if any(character.isspace() for character in raw):
        raise RuntimeError("Invalid INTERNAL_API_KEY: it contains whitespace; refusing to start")
    return raw


def require_internal_api_key(env: Optional[Mapping[str, str]] = None) -> str:
    """Read and validate INTERNAL_API_KEY from `env` (default `os.environ`); raise if unusable."""
    return parse_internal_api_key((os.environ if env is None else env).get("INTERNAL_API_KEY"))


def make_internal_api_key_verifier(expected: str) -> Callable[..., Awaitable[None]]:
    """
    Build the FastAPI dependency that guards internal endpoints.

    `expected` is validated again here, so a verifier can never be built around an
    empty key. The header is compared in constant time.
    """
    expected_bytes = parse_internal_api_key(expected).encode("utf-8")

    async def verify_internal_api_key(x_internal_api_key: Optional[str] = Header(None)) -> None:
        try:
            is_allowed = x_internal_api_key is not None and hmac.compare_digest(
                x_internal_api_key.encode("utf-8"), expected_bytes
            )
        except Exception:  # any failure to check is a denial
            logger.exception("[Auth] Could not check x-internal-api-key; denying")
            is_allowed = False
        if not is_allowed:
            raise HTTPException(status_code=403, detail="Forbidden")

    return verify_internal_api_key
