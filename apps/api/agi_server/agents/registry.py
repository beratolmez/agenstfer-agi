from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class ManagedAgentSpec(BaseModel):
    id: str
    name: str
    version: int = Field(ge=1)
    model_profile: str
    output_type: str
    capabilities: list[str]
    timeout_seconds: int = Field(gt=0, le=600)
    max_output_tokens: int = Field(gt=0, le=32768)
    data_classification: str
    approval_risk: str
    system_prompt: str


class AgentRegistry:
    def __init__(self, directory: Path | str | None = None):
        self.directory = Path(directory or Path(__file__).parent / "specs")

    def list(self) -> list[ManagedAgentSpec]:
        result = []
        for path in sorted(self.directory.glob("*.yaml")):
            result.append(
                ManagedAgentSpec.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
            )
        return result

    def get(self, agent_id: str) -> ManagedAgentSpec:
        for spec in self.list():
            if spec.id == agent_id:
                return spec
        raise KeyError(agent_id)
