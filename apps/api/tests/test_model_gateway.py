import pytest
from agi_server.agents.model_gateway import resolve_model_profile
from agi_server.config import Settings
from pydantic import SecretStr


def test_cloud_groq_profile_overrides_default_agent_profile() -> None:
    settings = Settings(
        model_profile="cloud-balanced",
        cloud_models_enabled=True,
        cloud_provider="groq",
        cloud_api_key=SecretStr("test-key"),
    )

    profile = resolve_model_profile("local-balanced", settings)

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
        resolve_model_profile("local-balanced", settings)


def test_explicit_local_strong_is_not_replaced_by_global_cloud_default() -> None:
    settings = Settings(
        model_profile="cloud-balanced",
        cloud_models_enabled=True,
        cloud_provider="groq",
        cloud_api_key=SecretStr("test-key"),
    )

    assert resolve_model_profile("local-strong", settings).id == "local-strong"
