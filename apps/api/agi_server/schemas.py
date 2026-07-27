from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class EvidenceRef(BaseModel):
    id: str
    source_id: str
    label: str
    locator: dict[str, Any]
    snapshot_sha256: str
    coverage: float = Field(ge=0, le=1)


class ScoreFactors(BaseModel):
    goal_alignment: float = Field(ge=0, le=100)
    estimated_impact: float = Field(ge=0, le=100)
    evidence_coverage: float = Field(ge=0, le=100)
    urgency: float = Field(ge=0, le=100)
    feasibility: float = Field(ge=0, le=100)
    risk_penalty: float = Field(ge=0, le=20)

    def total(self) -> int:
        value = (
            0.30 * self.goal_alignment
            + 0.25 * self.estimated_impact
            + 0.20 * self.evidence_coverage
            + 0.15 * self.urgency
            + 0.10 * self.feasibility
            - self.risk_penalty
        )
        return round(max(0, min(100, value)))


class OpportunityRecommendation(BaseModel):
    id: str
    title: str
    subtitle: str
    target_alignment: Literal["Yüksek", "Orta-Yüksek", "Orta"]
    impact: float = Field(ge=0, le=10)
    factors: ScoreFactors
    score: int
    status: Literal["İncelendi", "Taslak", "Onay bekliyor"]
    evidence: list[EvidenceRef]
    rationale: str


class PlanItem(BaseModel):
    week: int
    range: str
    title: str
    actions: list[str]


class DemoCounts(BaseModel):
    accounts: int
    contacts: int
    opportunities: int
    products: int
    orders_invoices: int
    activities: int


class GrowthDiagnostic(BaseModel):
    id: str = "growth-diagnostic-demo-v1"
    company: str
    objective: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    data_readiness: int
    evidence_coverage: int
    open_approvals: int
    summary: str
    counts: DemoCounts
    opportunities: list[OpportunityRecommendation]
    plan: list[PlanItem]
    data_gaps: list[str]
    detected_planted_insights: list[str]
    disclaimer: str = (
        "Skor, deterministic önceliklendirme sonucudur; olasılık veya model confidence değildir."
    )


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    version: str
    mode: str
    components: dict[str, str]


class SourceMappingRequest(BaseModel):
    entity_type: str = Field(min_length=2, max_length=60, pattern=r"^[a-z][a-z0-9_]*$")
    field_mapping: dict[str, str]
    classification: Literal["public", "internal", "confidential", "restricted"] = "internal"


class SetupProgressUpdate(BaseModel):
    current_step: int = Field(ge=1, le=5)
    completed_steps: list[int] = Field(max_length=5)
    configuration: dict[str, str | bool | int] = Field(default_factory=dict)
    status: Literal["in_progress", "completed"] = "in_progress"
