"""Typed contract tests for the diagnostic output schemas.

These five business-domain contracts (competitor, security, financial, SEO, CSAT) are
PRD targets that no agent spec can select yet: ManagedAgentSpec.output_type only admits
the four wired contracts. The schemas are kept under test so they stay valid until the
corresponding agents are built.
"""

from agi_server.agents.contracts import (
    CompanyAnalysis,
    CompetitorIntelligenceAnalysis,
    CustomerSatisfactionAnalysis,
    FinancialDiagnosticsAnalysis,
    MaterialClaim,
    SecurityAuditAnalysis,
    SEOBrandIntelligenceAnalysis,
)


def test_company_analysis_contract():
    claim = MaterialClaim(id="claim-1", text="High operational stability", evidence_ids=["ev-1"])
    analysis = CompanyAnalysis(
        summary="Company profile analysis text",
        segments=["Automotive", "Industrial"],
        strengths=[claim],
        weaknesses=[claim],
        data_gaps=["Missing CRM sync"],
    )
    assert len(analysis.strengths) == 1
    assert analysis.segments == ["Automotive", "Industrial"]


def test_competitor_intelligence_contract():
    claim = MaterialClaim(
        id="claim-2",
        text="Competitor pricing disadvantage",
        evidence_ids=["ev-2"],
    )
    intel = CompetitorIntelligenceAnalysis(
        summary="Competitor market breakdown",
        competitors=[
            {
                "name": "Acme Corp",
                "location": "Istanbul, TR",
                "key_strategy": "Aggressive pricing",
                "weaknesses": [claim],
            }
        ],
        market_threats=["New market entrant"],
    )
    assert intel.competitors[0].name == "Acme Corp"


def test_security_audit_contract():
    claim = MaterialClaim(
        id="claim-3",
        text="Publicly exposed staging endpoint",
        evidence_ids=["ev-3"],
    )
    audit = SecurityAuditAnalysis(
        overall_risk_level="medium",
        vulnerabilities=[claim],
        compliance_status=["ISO27001"],
        recommendations=["Enforce HTTPS and VPC private subnets"],
    )
    assert audit.overall_risk_level == "medium"


def test_financial_diagnostics_contract():
    claim = MaterialClaim(id="claim-4", text="EBITDA margin growth", evidence_ids=["ev-4"])
    fin = FinancialDiagnosticsAnalysis(
        revenue_growth_rate=0.15,
        gross_margin_percentage=42.5,
        ebitda_margin_percentage=18.0,
        highlights=[claim],
        risk_factors=["Supply chain volatility"],
    )
    assert fin.revenue_growth_rate == 0.15
    assert fin.gross_margin_percentage == 42.5


def test_seo_brand_intelligence_contract():
    claim = MaterialClaim(
        id="claim-5",
        text="High organic search ranking for industrial automation",
        evidence_ids=["ev-5"],
    )
    seo = SEOBrandIntelligenceAnalysis(
        search_visibility_score=85,
        brand_sentiment="positive",
        top_keywords=["industrial automation", "growth intelligence"],
        insights=[claim],
    )
    assert seo.search_visibility_score == 85
    assert seo.brand_sentiment == "positive"


def test_customer_satisfaction_contract():
    claim = MaterialClaim(id="claim-6", text="Fast support response time", evidence_ids=["ev-6"])
    csat = CustomerSatisfactionAnalysis(
        nps_score=68,
        csat_percentage=92.0,
        key_pain_points=[claim],
        retention_recommendations=["Introduce proactive account management"],
    )
    assert csat.nps_score == 68
    assert csat.csat_percentage == 92.0
