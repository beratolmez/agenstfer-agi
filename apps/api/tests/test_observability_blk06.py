from __future__ import annotations

from agi_server.config import Settings
from agi_server.logging_utils import build_error_details, redact_sensitive_text


class MockHTTPError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int,
        model_name: str | None = None,
        headers: dict | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.model_name = model_name
        self.headers = headers or {}


def test_redact_sensitive_text():
    secret_text = (
        "API error with AIzaSy1234567890abcdef12345678901234567 "
        "and Bearer mytoken123 and sk-abc1234567890abcdef12345"
    )
    redacted = redact_sensitive_text(secret_text)
    assert "AIzaSy" not in redacted
    assert "[REDACTED_API_KEY]" in redacted
    assert "[REDACTED_TOKEN]" in redacted


def test_build_error_details_structure():
    settings = Settings(
        cloud_models_enabled=True,
        cloud_provider="gemini",
        cloud_api_key="AIzaSy1234567890abcdef12345678901234567",
        cloud_model="gemini-3.6-flash",
    )
    err = MockHTTPError(
        "Invalid key AIzaSy1234567890abcdef12345678901234567",
        status_code=400,
        model_name="gemini-3.6-flash",
        headers={"retry-after": "30"},
    )
    details = build_error_details(
        err,
        settings=settings,
        profile_id="cloud-balanced",
        node_id="company-analyst",
    )

    assert details["code"] == "MockHTTPError"
    assert details["error_type"] == "MockHTTPError"
    assert details["provider"] == "gemini"
    assert details["model"] == "gemini-3.6-flash"
    assert details["profile"] == "cloud-balanced"
    assert details["http_status"] == 400
    assert details["node_id"] == "company-analyst"
    assert details["retry_after_seconds"] == 30
    assert "AIzaSy" not in details["message"]
    assert "[REDACTED_API_KEY]" in details["message"]
