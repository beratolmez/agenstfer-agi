from __future__ import annotations

import logging
import re
from typing import Any

from agi_server.agents.model_gateway import resolve_model_profile
from agi_server.config import Settings

logger = logging.getLogger("agi_server")


def redact_sensitive_text(text: str) -> str:
    """Redact secrets and sensitive API key patterns from error strings."""
    if not text:
        return text
    # Redact common API key patterns (Google AI, OpenAI, Bearer tokens, query param keys)
    text = re.sub(r"AIzaSy[A-Za-z0-9_-]{25,50}", "[REDACTED_API_KEY]", text)
    text = re.sub(r"(sk-[A-Za-z0-9_-]{20,})", "[REDACTED_API_KEY]", text)
    text = re.sub(
        r"(bearer\s+)[A-Za-z0-9._~+/-]+=*", r"\1[REDACTED_TOKEN]", text, flags=re.IGNORECASE
    )
    text = re.sub(r"(key=)[A-Za-z0-9_-]{20,}", r"\1[REDACTED_KEY]", text, flags=re.IGNORECASE)
    return text


def build_error_details(
    error: Exception,
    *,
    settings: Settings | None = None,
    profile_id: str | None = None,
    node_id: str | None = None,
) -> dict[str, Any]:
    """Extract content-safe, structured error metadata for error_json fields.

    Populates: provider, model, profile, http_status, node_id, retry_after_seconds.
    """
    provider: str | None = None
    model_name: str | None = None
    http_status: int | None = None

    # Check for HTTP status code on exception or response object
    if hasattr(error, "status_code") and isinstance(error.status_code, int):
        http_status = error.status_code
    elif (
        hasattr(error, "response")
        and hasattr(error.response, "status_code")
        and isinstance(error.response.status_code, int)
    ):
        http_status = error.response.status_code

    # Check for retry-after headers
    retry_after: int | float | str | None = None
    headers = None
    if hasattr(error, "response") and hasattr(error.response, "headers"):
        headers = error.response.headers
    elif hasattr(error, "headers"):
        headers = error.headers

    if headers and hasattr(headers, "__getitem__"):
        for header_name in ("retry-after", "Retry-After", "x-retry-after-seconds"):
            if header_name in headers:
                val = headers[header_name]
                try:
                    retry_after = int(val)
                except (ValueError, TypeError):
                    retry_after = str(val)
                break

    # Resolve profile metadata if settings and profile_id available
    if profile_id and settings:
        try:
            profile = resolve_model_profile(profile_id, settings)
            provider = profile.provider
            model_name = profile.model_name
        except Exception:
            pass

    if not provider:
        provider = getattr(error, "provider", None) or getattr(error, "model_provider", None)
    if not model_name:
        model_name = getattr(error, "model_name", None) or getattr(error, "model", None)

    code = type(error).__name__
    safe_message = redact_sensitive_text(str(error))

    details: dict[str, Any] = {
        "code": code,
        "message": safe_message,
        "error_type": code,
        "provider": provider,
        "model": model_name,
        "profile": profile_id,
        "http_status": http_status,
        "node_id": node_id,
    }
    if retry_after is not None:
        details["retry_after_seconds"] = retry_after

    return details
