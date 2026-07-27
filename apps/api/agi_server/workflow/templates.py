from __future__ import annotations

from typing import Any

from agi_server.workflow.models import WorkflowDefinition


GROWTH_WORKFLOW_TEMPLATES: list[dict[str, Any]] = [
    {
        "id": "lead-discovery-enrichment",
        "name": "Lead Discovery & Signal Enrichment",
        "description": (
            "Scans public signals, enriches lead attributes, "
            "checks CRM context, and ranks account priorities."
        ),
        "category": "Growth Operations",
        "type": "executable",
        "executable": True,
        "nodes": [
            {"id": "trigger", "kind": "manual_trigger", "label": "Manual Trigger", "position": {"x": 50, "y": 120}, "config": {}},
            {"id": "sync", "kind": "data_source_sync", "label": "CRM & Market Data Sync", "position": {"x": 200, "y": 120}, "config": {"connector_id": "crm_sync"}},
            {"id": "normalize", "kind": "normalize_context", "label": "Normalize Context", "position": {"x": 350, "y": 120}, "config": {}},
            {"id": "compile", "kind": "okf_compile", "label": "OKF Graph Compile", "position": {"x": 500, "y": 120}, "config": {}},
            {"id": "search", "kind": "knowledge_search", "label": "Knowledge Search", "position": {"x": 650, "y": 120}, "config": {"query": "lead enrichment signals"}},
            {"id": "agent1", "kind": "agent_run", "label": "Growth Opportunity Analyst", "position": {"x": 800, "y": 120}, "config": {"agent_id": "growth-opportunity-analyst", "model_profile": "local-balanced"}, "output_type": "hypotheses"},
            {"id": "agent2", "kind": "agent_run", "label": "Evidence Review Agent", "position": {"x": 950, "y": 120}, "config": {"agent_id": "evidence-reviewer", "model_profile": "local-balanced"}, "output_type": "agent_result"},
            {"id": "report", "kind": "report_output", "label": "Persisted Report Output", "position": {"x": 1100, "y": 120}, "config": {"format": "okf+html"}},
            {"id": "approval", "kind": "approval", "label": "Executive Approval Gate", "position": {"x": 1250, "y": 120}, "config": {"role": "approver", "timeout_days": 7}},
        ],
        "edges": [
            {"id": "e1", "source": "trigger", "target": "sync", "data_type": "control"},
            {"id": "e2", "source": "sync", "target": "normalize", "data_type": "raw_records"},
            {"id": "e3", "source": "normalize", "target": "compile", "data_type": "context"},
            {"id": "e4", "source": "compile", "target": "search", "data_type": "knowledge"},
            {"id": "e5", "source": "search", "target": "agent1", "data_type": "evidence"},
            {"id": "e6", "source": "agent1", "target": "agent2", "data_type": "hypotheses"},
            {"id": "e7", "source": "agent2", "target": "report", "data_type": "agent_result"},
            {"id": "e8", "source": "report", "target": "approval", "data_type": "artifact"},
        ],
    },
    {
        "id": "competitive-battlecard",
        "name": "Competitive Battlecard & Sales Plays",
        "description": (
            "Monitors competitor changes, extracts positioning insights, "
            "and generates battlecards with objection handling."
        ),
        "category": "Competitive Intelligence",
        "type": "executable",
        "executable": True,
        "nodes": [
            {"id": "trigger", "kind": "manual_trigger", "label": "Manual Trigger", "position": {"x": 50, "y": 120}, "config": {}},
            {"id": "sync", "kind": "data_source_sync", "label": "Competitor Signal Sync", "position": {"x": 200, "y": 120}, "config": {"connector_id": "competitor_sync"}},
            {"id": "normalize", "kind": "normalize_context", "label": "Normalize Context", "position": {"x": 350, "y": 120}, "config": {}},
            {"id": "compile", "kind": "okf_compile", "label": "OKF Graph Compile", "position": {"x": 500, "y": 120}, "config": {}},
            {"id": "search", "kind": "knowledge_search", "label": "Knowledge Search", "position": {"x": 650, "y": 120}, "config": {"query": "competitor battlecard data"}},
            {"id": "agent1", "kind": "agent_run", "label": "Competitor Intel Agent", "position": {"x": 800, "y": 120}, "config": {"agent_id": "company-analyst", "model_profile": "local-balanced"}, "output_type": "agent_result"},
            {"id": "agent2", "kind": "agent_run", "label": "Battlecard Synthesis Agent", "position": {"x": 950, "y": 120}, "config": {"agent_id": "company-analyst", "model_profile": "local-balanced"}, "output_type": "agent_result"},
            {"id": "report", "kind": "report_output", "label": "Persisted Report Output", "position": {"x": 1100, "y": 120}, "config": {"format": "okf+html"}},
            {"id": "approval", "kind": "approval", "label": "Executive Approval Gate", "position": {"x": 1250, "y": 120}, "config": {"role": "approver", "timeout_days": 7}},
        ],
        "edges": [
            {"id": "e1", "source": "trigger", "target": "sync", "data_type": "control"},
            {"id": "e2", "source": "sync", "target": "normalize", "data_type": "raw_records"},
            {"id": "e3", "source": "normalize", "target": "compile", "data_type": "context"},
            {"id": "e4", "source": "compile", "target": "search", "data_type": "knowledge"},
            {"id": "e5", "source": "search", "target": "agent1", "data_type": "evidence"},
            {"id": "e6", "source": "agent1", "target": "agent2", "data_type": "agent_result"},
            {"id": "e7", "source": "agent2", "target": "report", "data_type": "agent_result"},
            {"id": "e8", "source": "report", "target": "approval", "data_type": "artifact"},
        ],
    },
    {
        "id": "inbound-intent-triage",
        "name": "Inbound Intent Triage & Draft Response",
        "description": (
            "Classifies incoming form submissions and emails, assesses urgency, "
            "and produces human-in-the-loop draft responses."
        ),
        "category": "Inbound Operations",
        "type": "executable",
        "executable": True,
        "nodes": [
            {"id": "trigger", "kind": "manual_trigger", "label": "Manual Trigger", "position": {"x": 50, "y": 120}, "config": {}},
            {"id": "sync", "kind": "data_source_sync", "label": "Inbound Form Sync", "position": {"x": 200, "y": 120}, "config": {"connector_id": "inbound_sync"}},
            {"id": "normalize", "kind": "normalize_context", "label": "Normalize Context", "position": {"x": 350, "y": 120}, "config": {}},
            {"id": "compile", "kind": "okf_compile", "label": "OKF Graph Compile", "position": {"x": 500, "y": 120}, "config": {}},
            {"id": "search", "kind": "knowledge_search", "label": "Knowledge Search", "position": {"x": 650, "y": 120}, "config": {"query": "inbound intent guidelines"}},
            {"id": "agent1", "kind": "agent_run", "label": "Inbound Triage Agent", "position": {"x": 800, "y": 120}, "config": {"agent_id": "company-analyst", "model_profile": "local-balanced"}, "output_type": "agent_result"},
            {"id": "agent2", "kind": "agent_run", "label": "Response Reviewer Agent", "position": {"x": 950, "y": 120}, "config": {"agent_id": "evidence-reviewer", "model_profile": "local-balanced"}, "output_type": "agent_result"},
            {"id": "report", "kind": "report_output", "label": "Persisted Report Output", "position": {"x": 1100, "y": 120}, "config": {"format": "okf+html"}},
            {"id": "approval", "kind": "approval", "label": "Executive Approval Checkpoint", "position": {"x": 1250, "y": 120}, "config": {"role": "approver", "timeout_days": 7}},
        ],
        "edges": [
            {"id": "e1", "source": "trigger", "target": "sync", "data_type": "control"},
            {"id": "e2", "source": "sync", "target": "normalize", "data_type": "raw_records"},
            {"id": "e3", "source": "normalize", "target": "compile", "data_type": "context"},
            {"id": "e4", "source": "compile", "target": "search", "data_type": "knowledge"},
            {"id": "e5", "source": "search", "target": "agent1", "data_type": "evidence"},
            {"id": "e6", "source": "agent1", "target": "agent2", "data_type": "agent_result"},
            {"id": "e7", "source": "agent2", "target": "report", "data_type": "agent_result"},
            {"id": "e8", "source": "report", "target": "approval", "data_type": "artifact"},
        ],
    },
    {
        "id": "crm-erp-data-hygiene",
        "name": "CRM & ERP Data Hygiene & Reactivation",
        "description": (
            "Scans CRM and ERP records for duplicate entities, missing data fields, "
            "and passive customer reactivation signals."
        ),
        "category": "Revenue Operations",
        "type": "executable",
        "executable": True,
        "nodes": [
            {"id": "trigger", "kind": "manual_trigger", "label": "Manual Trigger", "position": {"x": 50, "y": 120}, "config": {}},
            {"id": "sync", "kind": "data_source_sync", "label": "ERP & CRM Scanner Sync", "position": {"x": 200, "y": 120}, "config": {"connector_id": "erp_crm_sync"}},
            {"id": "normalize", "kind": "normalize_context", "label": "Normalize Context", "position": {"x": 350, "y": 120}, "config": {}},
            {"id": "compile", "kind": "okf_compile", "label": "OKF Graph Compile", "position": {"x": 500, "y": 120}, "config": {}},
            {"id": "search", "kind": "knowledge_search", "label": "Knowledge Search", "position": {"x": 650, "y": 120}, "config": {"query": "data hygiene rules"}},
            {"id": "agent1", "kind": "agent_run", "label": "ERP & CRM Scanner Agent", "position": {"x": 800, "y": 120}, "config": {"agent_id": "company-analyst", "model_profile": "local-balanced"}, "output_type": "agent_result"},
            {"id": "agent2", "kind": "agent_run", "label": "OKF Patch Proposal Agent", "position": {"x": 950, "y": 120}, "config": {"agent_id": "wiki-curator", "model_profile": "local-balanced"}, "output_type": "agent_result"},
            {"id": "report", "kind": "report_output", "label": "Persisted Report Output", "position": {"x": 1100, "y": 120}, "config": {"format": "okf+html"}},
            {"id": "approval", "kind": "approval", "label": "Executive Approval Gate", "position": {"x": 1250, "y": 120}, "config": {"role": "approver", "timeout_days": 7}},
        ],
        "edges": [
            {"id": "e1", "source": "trigger", "target": "sync", "data_type": "control"},
            {"id": "e2", "source": "sync", "target": "normalize", "data_type": "raw_records"},
            {"id": "e3", "source": "normalize", "target": "compile", "data_type": "context"},
            {"id": "e4", "source": "compile", "target": "search", "data_type": "knowledge"},
            {"id": "e5", "source": "search", "target": "agent1", "data_type": "evidence"},
            {"id": "e6", "source": "agent1", "target": "agent2", "data_type": "agent_result"},
            {"id": "e7", "source": "agent2", "target": "report", "data_type": "agent_result"},
            {"id": "e8", "source": "report", "target": "approval", "data_type": "artifact"},
        ],
    },
    {
        "id": "enterprise-expansion-blueprint",
        "name": "Enterprise Account Expansion Blueprint (Catalog Reference)",
        "description": (
            "High-level visual diagram for multi-stakeholder enterprise expansion analysis."
        ),
        "category": "Strategic Accounts",
        "type": "catalog-only",
        "executable": False,
        "nodes": [
            {
                "id": "node-catalog-1",
                "kind": "agent_run",
                "label": "Account Mapping Blueprint",
                "position": {"x": 50, "y": 120},
                "config": {
                    "agent_id": "company-analyst",
                    "model_profile": "local-balanced",
                },
            },
        ],
        "edges": [],
    },
]


def template_to_workflow_definition(template: dict[str, Any]) -> WorkflowDefinition:
    """Convert UI template node/edge graph to canonical WorkflowDefinition model."""
    from agi_server.workflow.models import NodeKind, WorkflowDefinition, WorkflowEdge, WorkflowNode

    nodes = []
    for n in template.get("nodes", []):
        if "kind" in n:
            kind_str = n["kind"]
            label_str = n.get("label", n["id"])
            config_dict = n.get("config", {})
            position_dict = n.get("position", {"x": 0, "y": 0})
            output_type_str = n.get("output_type")
        else:
            data = n.get("data", {})
            kind_str = data.get("kind", "agent_run")
            label_str = data.get("label", n["id"])
            config_dict = data.get("config", {})
            position_dict = n.get("position", {"x": 0, "y": 0})
            output_type_str = config_dict.get("output_type")
        nodes.append(
            WorkflowNode(
                id=n["id"],
                kind=NodeKind(kind_str),
                label=label_str,
                position=position_dict,
                config=config_dict,
                output_type=output_type_str,
            )
        )
    edges = []
    for e in template.get("edges", []):
        edges.append(
            WorkflowEdge(
                id=e["id"],
                source=e["source"],
                target=e["target"],
                data_type=e.get("data_type", e.get("label", "control")),
            )
        )
    return WorkflowDefinition(
        id=template["id"],
        name=template["name"],
        version=1,
        nodes=nodes,
        edges=edges,
    )


def list_workflow_templates() -> list[dict[str, Any]]:
    """Return serializable growth workflow templates."""
    return GROWTH_WORKFLOW_TEMPLATES


def get_executable_templates() -> list[dict[str, Any]]:
    """Return only templates flagged as executable as valid WorkflowDefinition dicts."""
    from agi_server.workflow.validator import validate_workflow

    valid_templates = []
    for item in GROWTH_WORKFLOW_TEMPLATES:
        if item.get("executable") is True:
            wf = template_to_workflow_definition(item)
            validation = validate_workflow(wf)
            if validation.valid:
                dumped = wf.model_dump(mode="json")
                dumped["type"] = "executable"
                dumped["executable"] = True
                valid_templates.append(dumped)
            else:
                item["executable"] = False
    return valid_templates


def get_catalog_templates() -> list[dict[str, Any]]:
    """Return catalog-only UI reference templates."""
    return [item for item in GROWTH_WORKFLOW_TEMPLATES if item.get("executable") is False]
