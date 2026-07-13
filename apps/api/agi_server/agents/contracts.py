from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

SignalId = Literal[
    "energy-retrofit",
    "predictive-maintenance",
    "oem-export",
    "spare-parts-subscription",
    "digital-twin-commissioning",
]


class MaterialClaim(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{2,79}$")
    text: str = Field(min_length=3, max_length=600)
    evidence_ids: list[str] = Field(min_length=1, max_length=50)
    material: bool = True


class CompanyAnalysis(BaseModel):
    summary: str = Field(min_length=10, max_length=1200)
    segments: list[str] = Field(min_length=1, max_length=8)
    strengths: list[MaterialClaim] = Field(min_length=1, max_length=8)
    weaknesses: list[MaterialClaim] = Field(min_length=1, max_length=8)
    data_gaps: list[str] = Field(max_length=12)


class OpportunityHypothesis(BaseModel):
    signal_id: SignalId
    title: str = Field(min_length=3, max_length=180)
    rationale: str = Field(min_length=10, max_length=800)
    evidence_ids: list[str] = Field(min_length=1, max_length=50)


class OpportunityHypotheses(BaseModel):
    hypotheses: list[OpportunityHypothesis] = Field(min_length=5, max_length=5)

    @model_validator(mode="after")
    def require_all_signals_once(self):
        ids = [item.signal_id for item in self.hypotheses]
        if len(set(ids)) != 5:
            raise ValueError("Each deterministic opportunity signal must appear exactly once")
        return self


class EvidenceDecision(BaseModel):
    claim_id: str
    supported: bool
    evidence_ids: list[str] = Field(max_length=50)
    reason: str = Field(min_length=3, max_length=500)


class EvidenceReview(BaseModel):
    approved: bool
    decisions: list[EvidenceDecision] = Field(min_length=1, max_length=30)
    contradictions: list[str] = Field(max_length=20)


class OKFChangeSet(BaseModel):
    summary: str = Field(min_length=5, max_length=500)
    concept_paths: list[str] = Field(min_length=1, max_length=20)
    source_ids: list[str] = Field(min_length=1, max_length=20)


class StructuredOutputProbe(BaseModel):
    status: Literal["ok"]
    nonce: str
