from agi_server.agents.capabilities import list_capabilities
from agi_server.agents.registry import ManagedAgentSpec
from agi_server.agents.runtime import ScopedCapabilityTools


def test_capability_registry_listing():
    caps = list_capabilities()
    assert len(caps) >= 6
    ids = [item["id"] for item in caps]
    assert "knowledge.search" in ids
    assert "web.scrape" in ids
    assert "crm.read" in ids
    assert "erp.read" in ids
    assert "metrics.calculate" in ids
    assert "battlecard.generate" in ids


def test_scoped_capability_tools_binding():
    class DummyDB:
        pass

    class DummyMetrics:
        metrics = {}

    tools = ScopedCapabilityTools(
        db=DummyDB(),
        metrics=DummyMetrics(),
        knowledge_root="knowledge",
        bundle_root="knowledge/bundles/company",
        cloud=False,
    )

    spec = ManagedAgentSpec(
        id="test-agent",
        version=1,
        name="Test Agent",
        description="Testing capabilities",
        system_prompt="Comprehensive system prompt for testing dynamic capabilities.",
        model_profile="local-balanced",
        timeout_seconds=30,
        max_output_tokens=1000,
        data_classification="internal",
        approval_risk="low",
        capabilities=[
            "knowledge.search",
            "web.scrape",
            "crm.read",
            "erp.read",
            "metrics.calculate",
            "battlecard.generate",
        ],
        output_type="CompanyAnalysis",
    )

    bound_tools = tools.for_spec(spec)
    assert len(bound_tools) == 6
