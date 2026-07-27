"""
LLM model resolution for the legacy ai-agent service.

This module is part of the unintegrated legacy microservice
(apps/services/ai-agent). All production LLM inference is handled
exclusively by the Model Gateway in apps/api/agi_server/agents/model_gateway.py.

DO NOT add a fallback TestModel() or direct API-key reads here; doing so
creates a second, ungoverned inference path that bypasses cloud opt-in policy,
data-classification enforcement, and audit logging (see ADR-0006, ADR-0016).
"""

from __future__ import annotations


def get_llm_model(profile_id: str = "local-balanced"):
    """
    Delegates model resolution to the canonical Model Gateway.

    This function exists only for import compatibility with the legacy
    ai-agent graph nodes. It raises RuntimeError if the Model Gateway
    cannot be reached, so that ungoverned inference is never silently
    attempted through a TestModel fallback.

    In production, agent execution must go through
    apps/api/agi_server/agents/runtime.py, not this legacy package.
    """
    try:
        from agi_server.agents.model_gateway import resolve_model_profile
        from agi_server.config import get_settings

        settings = get_settings()
        profile = resolve_model_profile(profile_id, settings)

        try:
            from pydantic_ai.models.gemini import GeminiModel
        except ImportError:
            GeminiModel = None  # type: ignore[assignment,misc]

        try:
            from pydantic_ai.models.openai import OpenAIModel
        except ImportError:
            OpenAIModel = None  # type: ignore[assignment,misc]

        if profile.provider == "gemini" and settings.cloud_api_key and GeminiModel is not None:
            return GeminiModel(
                model_name=profile.model_name,
                api_key=settings.cloud_api_key.get_secret_value(),
            )
        if profile.provider in {"ollama", "openai", "vllm"} and OpenAIModel is not None:
            return OpenAIModel(
                model_name=profile.model_name,
                base_url=(
                    settings.ollama_base_url
                    if profile.provider == "ollama"
                    else "http://localhost:11434/v1"
                ),
                api_key="ollama",
            )
        raise RuntimeError(
            f"Model Gateway resolved profile '{profile_id}' to provider "
            f"'{profile.provider}' but no suitable Pydantic AI model class is available. "
            "Install pydantic-ai[gemini] or pydantic-ai[openai] as appropriate."
        )
    except ImportError as exc:
        raise RuntimeError(
            "Model Gateway (agi_server) is not available in this environment. "
            "The legacy ai-agent service must be run alongside the primary "
            "apps/api/agi_server service. Refusing to fall back to TestModel "
            "to prevent ungoverned LLM inference."
        ) from exc
