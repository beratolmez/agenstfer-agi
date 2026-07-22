from agi_server.agents.model_gateway import (
    CLOUD_PROVIDERS,
    resolve_model_profile,
)
from agi_server.config import Settings


def test_cloud_providers_registry():
    assert "gemini" in CLOUD_PROVIDERS
    assert "groq" in CLOUD_PROVIDERS
    assert "mistral" in CLOUD_PROVIDERS
    assert "openrouter" in CLOUD_PROVIDERS

    gemini_base_url, gemini_model = CLOUD_PROVIDERS["gemini"]
    assert "googleapis" in gemini_base_url
    assert gemini_model == "gemini-2.0-flash"


def test_resolve_cloud_model_profile():
    settings = Settings(
        cloud_models_enabled=True,
        cloud_provider="gemini",
        cloud_api_key="AIzaSyTestFakeKey",
        cloud_model="gemini-2.0-flash",
    )
    profile = resolve_model_profile("cloud-balanced", settings)
    assert profile.provider == "gemini"
    assert profile.model_name == "gemini-2.0-flash"
    assert profile.local is False
