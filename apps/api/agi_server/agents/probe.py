from __future__ import annotations

import uuid
from typing import Any

from pydantic_ai import Agent

from agi_server.agents.contracts import StructuredOutputProbe
from agi_server.agents.model_gateway import build_pydantic_ai_model, resolve_model_profile
from agi_server.config import Settings


def _new_probe_nonce() -> str:
    return str(uuid.uuid4())


async def probe_model_profile(
    settings: Settings,
    profile_id: str,
    *,
    model_override=None,
) -> dict[str, Any]:
    profile = resolve_model_profile(profile_id, settings)
    nonce = _new_probe_nonce()
    agent = Agent(
        model_override or build_pydantic_ai_model(profile_id, settings),
        output_type=StructuredOutputProbe,
        system_prompt="Return the requested typed probe only. Do not call tools.",
        retries=1,
    )
    result = await agent.run(f"Return status='ok' and nonce='{nonce}'.")
    output = StructuredOutputProbe.model_validate(result.output)
    if output.nonce != nonce:
        raise ValueError("Structured-output probe returned the wrong nonce")
    return {
        "ready": True,
        "profile": profile.id,
        "provider": profile.provider,
        "model": profile.model_name,
        "local": profile.local,
        "structured_output": True,
        "usage": {
            "input_tokens": result.usage.input_tokens,
            "output_tokens": result.usage.output_tokens,
            "requests": result.usage.requests,
        },
    }
