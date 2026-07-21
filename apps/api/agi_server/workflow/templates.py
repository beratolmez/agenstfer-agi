from __future__ import annotations

from typing import Any

GROWTH_WORKFLOW_TEMPLATES: list[dict[str, Any]] = [
    {
        "id": "lead-discovery-enrichment",
        "name": "Lead Discovery & Signal Enrichment",
        "description": (
            "Scans public signals, enriches lead attributes, "
            "checks CRM context, and ranks account priorities."
        ),
        "category": "Growth Operations",
        "nodes": [
            {
                "id": "node-1",
                "type": "customNode",
                "position": {"x": 50, "y": 120},
                "data": {
                    "label": "Lead Discovery Agent",
                    "kind": "agent_run",
                    "subtitle": "Lead & Signal Finder",
                    "config": {
                        "agent_id": "lead-opportunity-agent",
                        "model_profile": "local-balanced",
                        "output_type": "OpportunityHypotheses",
                        "capabilities": ["web.scrape", "crm.read"],
                    },
                },
            },
            {
                "id": "node-2",
                "type": "customNode",
                "position": {"x": 380, "y": 120},
                "data": {
                    "label": "Account Score Check",
                    "kind": "condition",
                    "subtitle": "Priority >= 75",
                    "config": {
                        "field": "priority_score",
                        "operator": "gte",
                        "value": 75,
                    },
                },
            },
            {
                "id": "node-3",
                "type": "customNode",
                "position": {"x": 710, "y": 120},
                "data": {
                    "label": "Evidence Review Agent",
                    "kind": "agent_run",
                    "subtitle": "Evidence Verification",
                    "config": {
                        "agent_id": "evidence-reviewer",
                        "model_profile": "cloud-reasoning",
                        "output_type": "EvidenceReview",
                        "capabilities": ["knowledge.search", "metrics.calculate"],
                    },
                },
            },
        ],
        "edges": [
            {"id": "edge-1-2", "source": "node-1", "target": "node-2"},
            {"id": "edge-2-3", "source": "node-2", "target": "node-3", "label": "Pass (true)"},
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
        "nodes": [
            {
                "id": "node-1",
                "type": "customNode",
                "position": {"x": 50, "y": 120},
                "data": {
                    "label": "Competitor Intel Agent",
                    "kind": "agent_run",
                    "subtitle": "Market Monitor",
                    "config": {
                        "agent_id": "competitor-analyst",
                        "model_profile": "local-balanced",
                        "output_type": "CompanyAnalysis",
                        "capabilities": ["web.scrape", "battlecard.generate"],
                    },
                },
            },
            {
                "id": "node-2",
                "type": "customNode",
                "position": {"x": 400, "y": 120},
                "data": {
                    "label": "Battlecard Synthesis Agent",
                    "kind": "agent_run",
                    "subtitle": "Sales Playbook Generator",
                    "config": {
                        "agent_id": "company-analyst",
                        "model_profile": "local-balanced",
                        "output_type": "CompanyAnalysis",
                        "capabilities": ["battlecard.generate", "knowledge.search"],
                    },
                },
            },
        ],
        "edges": [
            {"id": "edge-1-2", "source": "node-1", "target": "node-2"},
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
        "nodes": [
            {
                "id": "node-1",
                "type": "customNode",
                "position": {"x": 50, "y": 120},
                "data": {
                    "label": "Inbound Triage Agent",
                    "kind": "agent_run",
                    "subtitle": "Intent & Urgency Classification",
                    "config": {
                        "agent_id": "company-analyst",
                        "model_profile": "local-balanced",
                        "output_type": "CompanyAnalysis",
                        "capabilities": ["crm.read", "knowledge.search"],
                    },
                },
            },
            {
                "id": "node-2",
                "type": "customNode",
                "position": {"x": 380, "y": 120},
                "data": {
                    "label": "Urgency Check",
                    "kind": "condition",
                    "subtitle": "Urgency >= High",
                    "config": {
                        "field": "urgency_score",
                        "operator": "gte",
                        "value": 80,
                    },
                },
            },
            {
                "id": "node-3",
                "type": "customNode",
                "position": {"x": 710, "y": 120},
                "data": {
                    "label": "Executive Approval Checkpoint",
                    "kind": "agent_run",
                    "subtitle": "Human In The Loop Review",
                    "config": {
                        "agent_id": "evidence-reviewer",
                        "model_profile": "cloud-reasoning",
                        "output_type": "EvidenceReview",
                        "capabilities": ["knowledge.search"],
                    },
                },
            },
        ],
        "edges": [
            {"id": "edge-1-2", "source": "node-1", "target": "node-2"},
            {"id": "edge-2-3", "source": "node-2", "target": "node-3", "label": "Urgent"},
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
        "nodes": [
            {
                "id": "node-1",
                "type": "customNode",
                "position": {"x": 50, "y": 120},
                "data": {
                    "label": "ERP & CRM Scanner Agent",
                    "kind": "agent_run",
                    "subtitle": "Data Quality Inspector",
                    "config": {
                        "agent_id": "company-analyst",
                        "model_profile": "local-balanced",
                        "output_type": "CompanyAnalysis",
                        "capabilities": ["crm.read", "erp.read", "metrics.calculate"],
                    },
                },
            },
            {
                "id": "node-2",
                "type": "customNode",
                "position": {"x": 400, "y": 120},
                "data": {
                    "label": "OKF Patch Proposal Agent",
                    "kind": "agent_run",
                    "subtitle": "Knowledge Graph Repair",
                    "config": {
                        "agent_id": "okf-curator",
                        "model_profile": "local-balanced",
                        "output_type": "OKFChangeSet",
                        "capabilities": ["knowledge.search", "metrics.calculate"],
                    },
                },
            },
        ],
        "edges": [
            {"id": "edge-1-2", "source": "node-1", "target": "node-2"},
        ],
    },
]


def list_workflow_templates() -> list[dict[str, Any]]:
    """Return serializable growth workflow templates."""
    return GROWTH_WORKFLOW_TEMPLATES
