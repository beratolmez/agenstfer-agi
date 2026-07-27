from agi_server.workflow.models import NodeKind, WorkflowDefinition, WorkflowEdge, WorkflowNode


def build_default_workflow(model_profile: str | None = None) -> WorkflowDefinition:
    profile = model_profile or "local-balanced"
    rows = [
        ("trigger", NodeKind.MANUAL_TRIGGER, "Manual Trigger", 20, 60, {}, "control"),
        (
            "sync",
            NodeKind.DATA_SOURCE_SYNC,
            "Data Source Sync",
            250,
            60,
            {"connector_id": "demo-company"},
            "raw_records",
        ),
        ("normalize", NodeKind.NORMALIZE_CONTEXT, "Normalize Context", 480, 60, {}, "context"),
        ("compile", NodeKind.OKF_COMPILE, "OKF Compile", 150, 220, {}, "knowledge"),
        (
            "search",
            NodeKind.KNOWLEDGE_SEARCH,
            "Knowledge Search",
            380,
            220,
            {"query": "company context and growth evidence"},
            "evidence",
        ),
        (
            "company_agent",
            NodeKind.AGENT_RUN,
            "Company Analyst",
            610,
            220,
            {
                "agent_id": "company-analyst",
                "agent_version": 3,
                "model_profile": profile,
                "output_type": "CompanyAnalysis",
            },
            "agent_result",
        ),
        (
            "growth_agent",
            NodeKind.AGENT_RUN,
            "Growth Opportunity Analyst",
            150,
            380,
            {
                "agent_id": "growth-opportunity-analyst",
                "agent_version": 3,
                "model_profile": profile,
                "output_type": "OpportunityHypotheses",
            },
            "hypotheses",
        ),
        (
            "score",
            NodeKind.DETERMINISTIC_SCORE,
            "Deterministic Score",
            380,
            390,
            {},
            "scored_opportunities",
        ),
        (
            "review",
            NodeKind.AGENT_RUN,
            "Evidence Reviewer",
            610,
            380,
            {
                "agent_id": "evidence-reviewer",
                "agent_version": 3,
                "model_profile": profile,
                "output_type": "EvidenceReview",
            },
            "agent_result",
        ),
        (
            "curator",
            NodeKind.AGENT_RUN,
            "Wiki Curator",
            150,
            540,
            {
                "agent_id": "wiki-curator",
                "agent_version": 2,
                "model_profile": profile,
                "output_type": "OKFChangeSet",
            },
            "agent_result",
        ),
        (
            "approval",
            NodeKind.APPROVAL,
            "Approval",
            380,
            700,
            {"role": "approver", "timeout_days": 7},
            "approved",
        ),
        (
            "report",
            NodeKind.REPORT_OUTPUT,
            "Report Output",
            380,
            540,
            {"format": "okf+html"},
            "artifact",
        ),
    ]
    nodes = [
        WorkflowNode(
            id=node_id,
            kind=kind,
            label=label,
            position={"x": x, "y": y},
            config=config,
            output_type=output_type,
        )
        for node_id, kind, label, x, y, config, output_type in rows
    ]
    edge_rows = [
        ("trigger", "sync", "control"),
        ("sync", "normalize", "raw_records"),
        ("normalize", "compile", "context"),
        ("compile", "search", "knowledge"),
        ("search", "company_agent", "evidence"),
        ("company_agent", "growth_agent", "agent_result"),
        ("growth_agent", "score", "hypotheses"),
        ("score", "review", "scored_opportunities"),
        ("review", "curator", "agent_result"),
        ("curator", "report", "agent_result"),
        ("report", "approval", "artifact"),
    ]
    edges = [
        WorkflowEdge(id=f"e-{source}-{target}", source=source, target=target, data_type=data_type)
        for source, target, data_type in edge_rows
    ]
    return WorkflowDefinition(
        id="builtin-growth-diagnostic",
        name="Growth Diagnostic",
        version=3,
        nodes=nodes,
        edges=edges,
    )
