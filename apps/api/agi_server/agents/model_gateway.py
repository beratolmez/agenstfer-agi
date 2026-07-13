from __future__ import annotations

from dataclasses import dataclass

from agi_server.config import Settings


@dataclass(frozen=True)
class ModelProfile:
    id: str
    provider: str
    model_name: str
    local: bool
    base_url: str | None = None


PROFILES = {
    "local-balanced": ModelProfile("local-balanced", "ollama", "qwen3.5:9b", True),
    "local-strong": ModelProfile("local-strong", "ollama", "qwen3.5:27b", True),
}

CLOUD_PROVIDERS = {
    "groq": ("https://api.groq.com/openai/v1", "openai/gpt-oss-20b"),
    "mistral": ("https://api.mistral.ai/v1", "mistral-small-latest"),
}


def resolve_model_profile(profile_id: str, settings: Settings) -> ModelProfile:
    # Existing agent specs use local-balanced. The global setting deliberately
    # overrides that default only, so a workflow can still explicitly select a
    # stronger local profile when both options are available.
    effective_profile = (
        settings.model_profile
        if profile_id == "local-balanced" and settings.model_profile != "local-balanced"
        else profile_id
    )
    if effective_profile == "cloud-balanced":
        if not settings.cloud_models_enabled:
            raise PermissionError("Cloud model profilleri yönetici opt-in olmadan kullanılamaz")
        if settings.cloud_provider not in CLOUD_PROVIDERS or settings.cloud_api_key is None:
            raise ValueError(
                "Cloud provider, API key ve cloud profile birlikte yapılandırılmalıdır"
            )
        base_url, default_model = CLOUD_PROVIDERS[settings.cloud_provider]
        return ModelProfile(
            f"cloud-{settings.cloud_provider}",
            settings.cloud_provider,
            settings.cloud_model or default_model,
            False,
            base_url,
        )
    if effective_profile not in PROFILES:
        raise ValueError(f"Bilinmeyen veya izin verilmeyen model profili: {profile_id}")
    profile = PROFILES[effective_profile]
    if not profile.local and not settings.cloud_models_enabled:
        raise PermissionError("Cloud model profilleri yönetici opt-in olmadan kullanılamaz")
    return profile


def build_pydantic_ai_agent(spec, output_type, settings: Settings):
    """Build lazily so deterministic demo/tests do not require a running Ollama."""
    from pydantic_ai import Agent
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.providers.ollama import OllamaProvider
    from pydantic_ai.providers.openai import OpenAIProvider

    profile = resolve_model_profile(spec.model_profile, settings)
    if profile.local:
        provider = OllamaProvider(base_url=settings.ollama_base_url)
    else:
        assert profile.base_url is not None and settings.cloud_api_key is not None
        provider = OpenAIProvider(
            base_url=profile.base_url,
            api_key=settings.cloud_api_key.get_secret_value(),
        )
    model = OpenAIChatModel(profile.model_name, provider=provider)
    return Agent(model, output_type=output_type, system_prompt=spec.system_prompt)
