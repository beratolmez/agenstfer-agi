from __future__ import annotations

from collections import defaultdict, deque

from agi_server.workflow.catalog import NODE_CATALOG
from agi_server.workflow.models import (
    NodeKind,
    WorkflowDefinition,
    WorkflowIssue,
    WorkflowValidation,
)

TRIGGERS = {NodeKind.MANUAL_TRIGGER, NodeKind.ONBOARDING_TRIGGER, NodeKind.SCHEDULE_TRIGGER}
CONDITION_OPERATORS = {"eq", "ne", "gt", "gte", "lt", "lte", "contains"}


def validate_workflow(workflow: WorkflowDefinition) -> WorkflowValidation:
    issues: list[WorkflowIssue] = []
    nodes = {node.id: node for node in workflow.nodes}
    incoming: dict[str, list[str]] = defaultdict(list)
    outgoing: dict[str, list[str]] = defaultdict(list)
    indegree = {node.id: 0 for node in workflow.nodes}

    triggers = [node for node in workflow.nodes if node.kind in TRIGGERS]
    if len(triggers) != 1:
        issues.append(
            WorkflowIssue(code="trigger.count", message="Workflow tam bir trigger içermelidir.")
        )

    for node in workflow.nodes:
        spec = NODE_CATALOG[node.kind]
        missing = sorted(key for key in spec.required_config if node.config.get(key) in (None, ""))
        if missing:
            issues.append(
                WorkflowIssue(
                    code="node.missing_config",
                    node_id=node.id,
                    message=f"Zorunlu config eksik: {', '.join(missing)}",
                )
            )
        if node.kind == NodeKind.CONDITION:
            field = node.config.get("field")
            operator = node.config.get("operator")
            safe_field = (
                isinstance(field, str) and field.replace("_", "").replace(".", "").isalnum()
            )
            if not safe_field:
                issues.append(
                    WorkflowIssue(
                        code="condition.field",
                        node_id=node.id,
                        message=(
                            "Condition field yalnız güvenli dotted-field biçimini kullanabilir."
                        ),
                    )
                )
            if operator not in CONDITION_OPERATORS:
                issues.append(
                    WorkflowIssue(
                        code="condition.operator",
                        node_id=node.id,
                        message="Condition operator allowlist içinde değil.",
                    )
                )

    for edge in workflow.edges:
        source = nodes.get(edge.source)
        target = nodes.get(edge.target)
        if not source or not target:
            issues.append(
                WorkflowIssue(
                    code="edge.unknown_node",
                    edge_id=edge.id,
                    message="Edge bilinmeyen source veya target kullanıyor.",
                )
            )
            continue
        expected_output = source.output_type or NODE_CATALOG[source.kind].default_output
        if edge.data_type != expected_output:
            issues.append(
                WorkflowIssue(
                    code="edge.source_type",
                    edge_id=edge.id,
                    message=f"Edge tipi {edge.data_type}; source çıktısı {expected_output}.",
                )
            )
        if edge.data_type not in NODE_CATALOG[target.kind].accepted_inputs:
            issues.append(
                WorkflowIssue(
                    code="edge.target_type",
                    edge_id=edge.id,
                    message=f"{target.kind.value} '{edge.data_type}' girdisini kabul etmiyor.",
                )
            )
        outgoing[source.id].append(target.id)
        incoming[target.id].append(source.id)
        indegree[target.id] += 1

    for node in workflow.nodes:
        node_edges = [edge for edge in workflow.edges if edge.source == node.id]
        if node.kind == NodeKind.CONDITION:
            branches = [edge.branch for edge in node_edges]
            if sorted(branch for branch in branches if branch is not None) != ["false", "true"]:
                issues.append(
                    WorkflowIssue(
                        code="condition.branches",
                        node_id=node.id,
                        message="Condition tam bir true ve bir false branch içermelidir.",
                    )
                )
        elif any(edge.branch is not None for edge in node_edges):
            issues.append(
                WorkflowIssue(
                    code="edge.unexpected_branch",
                    node_id=node.id,
                    message="Yalnız Condition node branch etiketi kullanabilir.",
                )
            )

    queue = deque(sorted(node_id for node_id, degree in indegree.items() if degree == 0))
    order: list[str] = []
    while queue:
        node_id = queue.popleft()
        order.append(node_id)
        for target in outgoing[node_id]:
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    if len(order) != len(nodes):
        issues.append(WorkflowIssue(code="graph.cycle", message="Workflow çevrim içeremez."))

    if triggers:
        reachable: set[str] = set()
        queue = deque([triggers[0].id])
        while queue:
            node_id = queue.popleft()
            if node_id in reachable:
                continue
            reachable.add(node_id)
            queue.extend(outgoing[node_id])
        for orphan in sorted(set(nodes) - reachable):
            issues.append(
                WorkflowIssue(
                    code="graph.unreachable",
                    node_id=orphan,
                    message="Node trigger'dan erişilebilir değil.",
                )
            )

    outputs = [node for node in workflow.nodes if node.kind == NodeKind.REPORT_OUTPUT]
    if not outputs:
        issues.append(
            WorkflowIssue(code="output.missing", message="En az bir Report Output gerekir.")
        )
    approvals = [node for node in workflow.nodes if node.kind == NodeKind.APPROVAL]
    if len(approvals) != 1:
        issues.append(
            WorkflowIssue(
                code="approval.count",
                message="Published MVP workflow tam bir Approval node içermelidir.",
            )
        )
    elif outputs and order:
        positions = {node_id: index for index, node_id in enumerate(order)}
        if any(positions[approvals[0].id] <= positions[output.id] for output in outputs):
            issues.append(
                WorkflowIssue(
                    code="approval.order",
                    node_id=approvals[0].id,
                    message="Approval node report candidate üretildikten sonra çalışmalıdır.",
                )
            )
    return WorkflowValidation(valid=not issues, issues=issues, topological_order=order)
