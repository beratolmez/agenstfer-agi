from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

SignalId = str


class MaterialClaim(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]{2,79}$")
    text: str = Field(min_length=3, max_length=600)
    evidence_ids: list[str] = Field(min_length=1, max_length=50)
    material: bool = True


# 1. Şirketi Tanı (Company Analysis)
class CompanyAnalysis(BaseModel):
    summary: str = Field(min_length=10, max_length=1200)
    segments: list[str] = Field(min_length=1, max_length=8)
    strengths: list[MaterialClaim] = Field(min_length=1, max_length=8)
    weaknesses: list[MaterialClaim] = Field(min_length=1, max_length=8)
    data_gaps: list[str] = Field(max_length=12)


# 2. Potansiyel Müşteriler (Opportunity / Lead Analysis)
class OpportunityHypothesis(BaseModel):
    signal_id: str = Field(min_length=2, max_length=120)
    title: str = Field(min_length=3, max_length=180)
    rationale: str = Field(min_length=10, max_length=800)
    evidence_ids: list[str] = Field(min_length=1, max_length=50)


class OpportunityHypotheses(BaseModel):
    hypotheses: list[OpportunityHypothesis] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def require_unique_signals(self):
        ids = [item.signal_id for item in self.hypotheses]
        if len(set(ids)) != len(ids):
            raise ValueError("Opportunity signal IDs must be unique across hypotheses")
        return self


# 3. Rakipler Kimler (Competitor Intelligence)
class CompetitorItem(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    location: str = Field(min_length=2, max_length=120)
    key_strategy: str = Field(min_length=5, max_length=300)
    weaknesses: list[MaterialClaim] = Field(min_length=1, max_length=5)


class CompetitorIntelligenceAnalysis(BaseModel):
    summary: str = Field(min_length=10, max_length=1000)
    competitors: list[CompetitorItem] = Field(min_length=1, max_length=10)
    market_threats: list[str] = Field(max_length=10)


# 4. Siber Güvenlik (Security Audit)
class SecurityAuditAnalysis(BaseModel):
    overall_risk_level: Literal["low", "medium", "high", "critical"]
    vulnerabilities: list[MaterialClaim] = Field(min_length=1, max_length=10)
    compliance_status: list[str] = Field(max_length=8)
    recommendations: list[str] = Field(min_length=1, max_length=10)


# 5. Finansal Modüller (Financial Diagnostics)
class FinancialDiagnosticsAnalysis(BaseModel):
    revenue_growth_rate: float = Field(ge=-1.0, le=10.0)
    gross_margin_percentage: float = Field(ge=0.0, le=100.0)
    ebitda_margin_percentage: float = Field(ge=-100.0, le=100.0)
    highlights: list[MaterialClaim] = Field(min_length=1, max_length=8)
    risk_factors: list[str] = Field(max_length=10)


# 6. SEO & Sosyal Medya (SEO & Brand Intelligence)
class SEOBrandIntelligenceAnalysis(BaseModel):
    search_visibility_score: int = Field(ge=0, le=100)
    brand_sentiment: Literal["positive", "neutral", "negative"]
    top_keywords: list[str] = Field(min_length=1, max_length=20)
    insights: list[MaterialClaim] = Field(min_length=1, max_length=8)


# 7. Müşteri Memnuniyeti (Customer Satisfaction Analysis)
class CustomerSatisfactionAnalysis(BaseModel):
    nps_score: int = Field(ge=-100, le=100)
    csat_percentage: float = Field(ge=0.0, le=100.0)
    key_pain_points: list[MaterialClaim] = Field(min_length=1, max_length=8)
    retention_recommendations: list[str] = Field(min_length=1, max_length=10)


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
