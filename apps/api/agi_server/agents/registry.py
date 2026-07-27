from __future__ import annotations

import importlib.resources
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator

from agi_server.agents.capabilities import BUILTIN_CAPABILITIES


class ManagedAgentSpec(BaseModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]{2,79}$")
    name: str = Field(min_length=2, max_length=160)
    version: int = Field(ge=1)
    model_profile: Literal["local-balanced", "local-strong", "cloud-balanced"]
    output_type: Literal[
        "CompanyAnalysis",
        "OpportunityHypotheses",
        "EvidenceReview",
        "OKFChangeSet",
    ]
    capabilities: list[str] = Field(min_length=1, max_length=16)
    timeout_seconds: int = Field(gt=0, le=600)
    max_output_tokens: int = Field(gt=0, le=32768)
    data_classification: Literal["public", "internal", "confidential", "restricted"]
    approval_risk: Literal["low", "medium", "high"]
    system_prompt: str = Field(min_length=20, max_length=8000)

    @field_validator("capabilities")
    @classmethod
    def capabilities_are_unique_and_known(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("Agent capabilities must be unique")
        unknown = set(value) - set(BUILTIN_CAPABILITIES)
        if unknown:
            raise ValueError(f"Unknown capability IDs in spec: {sorted(unknown)}")
        return value


class AgentRegistry:
    def __init__(self, directory: Path | str | None = None):
        if directory:
            self.directory = Path(directory)
        else:
            try:
                res_path = Path(str(importlib.resources.files("agi_server.agents") / "specs"))
                if res_path.exists() and list(res_path.glob("*.yaml")):
                    self.directory = res_path
                else:
                    self.directory = Path(__file__).parent / "specs"
            except Exception:
                self.directory = Path(__file__).parent / "specs"

    def list(self) -> list[ManagedAgentSpec]:
        if not self.directory.exists():
            raise RuntimeError(f"Agent specs directory does not exist: {self.directory}")
        paths = sorted(self.directory.glob("*.yaml"))
        if not paths:
            raise RuntimeError(f"No agent specs found in directory: {self.directory}")
        result = []
        for path in paths:
            result.append(
                ManagedAgentSpec.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
            )
        return result

    def get(self, agent_id: str) -> ManagedAgentSpec:
        for spec in self.list():
            if spec.id == agent_id:
                return spec
        raise KeyError(agent_id)

