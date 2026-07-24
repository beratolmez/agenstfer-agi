import pytest
from agi_server.connectors.crm_erp import ReadOnlyCRMConnector, ReadOnlyERPConnector
from agi_server.db import Base
from agi_server.workflow.models import WorkflowDefinition
from agi_server.workflow.registry_service import (
    ensure_platform_registry,
    validate_workflow_bindings,
)
from agi_server.workflow.templates import (
    get_catalog_templates,
    get_executable_templates,
    list_workflow_templates,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionFactory = sessionmaker(bind=engine)
    session = SessionFactory()
    try:
        ensure_platform_registry(session)
        yield session
    finally:
        session.close()


def test_list_workflow_templates():
    templates = list_workflow_templates()
    assert len(templates) >= 5
    ids = [t["id"] for t in templates]
    assert "lead-discovery-enrichment" in ids
    assert "competitive-battlecard" in ids
    assert "inbound-intent-triage" in ids
    assert "crm-erp-data-hygiene" in ids
    assert "enterprise-expansion-blueprint" in ids


def test_executable_vs_catalog_templates_distinction():
    exec_templates = get_executable_templates()
    catalog_templates = get_catalog_templates()

    assert len(exec_templates) == 4
    assert len(catalog_templates) == 1

    for item in exec_templates:
        assert item["type"] == "executable"
        assert item["executable"] is True

    for item in catalog_templates:
        assert item["type"] == "catalog-only"
        assert item["executable"] is False


def test_template_agent_ids_and_model_profiles_aligned():
    published_agent_ids = {
        "company-analyst",
        "growth-opportunity-analyst",
        "evidence-reviewer",
        "wiki-curator",
    }
    allowlisted_profiles = {"local-balanced", "local-strong", "cloud-balanced"}

    for tpl in get_executable_templates():
        for node in tpl["nodes"]:
            config = node.get("data", {}).get("config", {})
            if "agent_id" in config:
                assert config["agent_id"] in published_agent_ids
            if "model_profile" in config:
                assert config["model_profile"] in allowlisted_profiles


def test_generic_workflow_publication_rules_do_not_force_default_roles(db_session: Session):
    generic_def = WorkflowDefinition.model_validate({
        "id": "generic-test-workflow",
        "version": 1,
        "name": "Generic Workflow",
        "status": "draft",
        "nodes": [
            {
                "id": "trigger-1",
                "label": "Start Trigger",
                "type": "customNode",
                "kind": "manual_trigger",
                "output_type": "CompanyAnalysis",
                "config": {"label": "Start"},
            },
            {
                "id": "agent-1",
                "label": "Company Analyst Node",
                "type": "customNode",
                "kind": "agent_run",
                "output_type": "CompanyAnalysis",
                "config": {
                    "agent_id": "company-analyst",
                    "model_profile": "local-balanced",
                    "output_type": "CompanyAnalysis",
                },
            },
            {
                "id": "report-1",
                "label": "Report Output Node",
                "type": "customNode",
                "kind": "report_output",
                "output_type": "CompanyAnalysis",
                "config": {"label": "Report"},
            },
        ],
        "edges": [
            {
                "id": "e1",
                "source": "trigger-1",
                "target": "agent-1",
                "data_type": "CompanyAnalysis",
            },
            {
                "id": "e2",
                "source": "agent-1",
                "target": "report-1",
                "data_type": "CompanyAnalysis",
            },
        ],
    })

    validated = validate_workflow_bindings(db_session, generic_def)
    assert validated.id == "generic-test-workflow"


def test_builtin_diagnostic_preserves_required_agent_roles(db_session: Session):
    builtin_incomplete = WorkflowDefinition.model_validate({
        "id": "builtin-growth-diagnostic",
        "version": 1,
        "name": "Builtin Growth Diagnostic",
        "status": "draft",
        "nodes": [
            {
                "id": "trigger-1",
                "label": "Start Trigger",
                "type": "customNode",
                "kind": "manual_trigger",
                "output_type": "CompanyAnalysis",
                "config": {"label": "Start"},
            },
            {
                "id": "agent-1",
                "label": "Company Analyst Node",
                "type": "customNode",
                "kind": "agent_run",
                "output_type": "CompanyAnalysis",
                "config": {
                    "agent_id": "company-analyst",
                    "model_profile": "local-balanced",
                    "output_type": "CompanyAnalysis",
                },
            },
        ],
        "edges": [],
    })

    with pytest.raises(ValueError, match="default diagnostic workflow requires built-in agent"):
        validate_workflow_bindings(db_session, builtin_incomplete)


def test_crm_erp_connectors_remain_read_only(tmp_path):
    csv_file = tmp_path / "accounts.csv"
    csv_file.write_text("account_id,name\nacc-1,Acme Corp\n", encoding="utf-8")

    crm = ReadOnlyCRMConnector(path_or_uri=csv_file, source_id="src_crm")
    schema = crm.discover_schema()
    assert schema.read_only is True

    erp = ReadOnlyERPConnector(path_or_uri=csv_file, source_id="src_erp", entity_type="products")
    schema_erp = erp.discover_schema()
    assert schema_erp.read_only is True
