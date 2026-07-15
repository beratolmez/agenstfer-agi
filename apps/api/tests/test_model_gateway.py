import pytest
from agi_server.agents.model_gateway import (
    configured_model_profiles,
    model_settings_for_profile,
    resolve_model_profile,
)
from agi_server.config import Settings
from pydantic import SecretStr


def test_explicit_cloud_groq_profile_is_resolved_and_pinned() -> None:
    settings = Settings(
        model_profile="cloud-balanced",
        cloud_models_enabled=True,
        cloud_provider="groq",
        cloud_api_key=SecretStr("test-key"),
    )

    profile = resolve_model_profile("cloud-balanced", settings)

    assert profile.id == "cloud-groq"
    assert profile.base_url == "https://api.groq.com/openai/v1"
    assert profile.model_name == "openai/gpt-oss-20b"
    assert not profile.local


def test_cloud_profile_requires_explicit_opt_in() -> None:
    settings = Settings(
        model_profile="cloud-balanced",
        cloud_provider="mistral",
        cloud_api_key=SecretStr("test-key"),
    )

    with pytest.raises(PermissionError):
        resolve_model_profile("cloud-balanced", settings)


def test_explicit_local_strong_is_not_replaced_by_global_cloud_default() -> None:
    settings = Settings(
        model_profile="cloud-balanced",
        cloud_models_enabled=True,
        cloud_provider="groq",
        cloud_api_key=SecretStr("test-key"),
    )

    assert resolve_model_profile("local-strong", settings).id == "local-strong"


def test_published_agent_default_is_not_silently_replaced_by_installation_default() -> None:
    settings = Settings(
        model_profile="cloud-balanced",
        cloud_models_enabled=True,
        cloud_provider="groq",
        cloud_api_key=SecretStr("test-key"),
    )

    assert resolve_model_profile("local-balanced", settings).id == "local-balanced"


def test_local_structured_output_disables_unpersisted_reasoning() -> None:
    model_settings = model_settings_for_profile(
        "local-balanced", Settings(), max_tokens=4000
    )

    assert model_settings == {
        "max_tokens": 4000,
        "openai_reasoning_effort": "none",
        "temperature": 0,
    }


def test_cloud_profile_does_not_inherit_ollama_reasoning_controls() -> None:
    settings = Settings(
        cloud_models_enabled=True,
        cloud_provider="mistral",
        cloud_api_key=SecretStr("test-key"),
    )

    assert model_settings_for_profile(
        "cloud-balanced", settings, max_tokens=4000
    ) == {"max_tokens": 4000}


def test_profile_catalog_is_allowlisted_and_never_exposes_cloud_secret() -> None:
    settings = Settings(
        model_profile="cloud-balanced",
        cloud_models_enabled=True,
        cloud_provider="groq",
        cloud_api_key=SecretStr("must-not-leak"),
    )

    profiles = configured_model_profiles(settings)

    assert [item["id"] for item in profiles] == [
        "local-balanced",
        "local-strong",
        "cloud-balanced",
    ]
    cloud = profiles[-1]
    assert cloud == {
        "id": "cloud-balanced",
        "provider": "groq",
        "model": "openai/gpt-oss-20b",
        "local": False,
        "enabled": True,
        "configured": True,
        "selected": True,
    }
    assert "must-not-leak" not in repr(profiles)
