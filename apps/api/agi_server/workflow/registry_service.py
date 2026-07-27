from __future__ import annotations

import re
from copy import deepcopy
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from agi_server.agents.model_gateway import resolve_model_profile
from agi_server.agents.registry import AgentRegistry, ManagedAgentSpec
from agi_server.config import Settings
from agi_server.db import (
    AgentDefinitionRow,
    CapabilityDefinitionRow,
    WorkflowDefinitionRow,
    WorkflowSchedule,
)
from agi_server.workflow.default import build_default_workflow
from agi_server.workflow.models import NodeKind, WorkflowDefinition
from agi_server.workflow.validator import validate_workflow

SAFE_ID = re.compile(r"^[a-z][a-z0-9_-]{2,79}$")
CRON_PART = re.compile(r"^[0-9*/,\-]+$")


def ensure_platform_registry(db: Session, settings: Settings | None = None) -> None:
    specs = AgentRegistry().list()
    if not specs:
        raise RuntimeError("Platform registry seeding failed: zero agent specs found")
    for spec in specs:
        row = db.get(AgentDefinitionRow, (spec.id, spec.version))
        if row is None:
            db.add(
                AgentDefinitionRow(
                    id=spec.id,
                    version=spec.version,
                    name=spec.name,
                    status="published",
                    definition=spec.model_dump(mode="json"),
                )
            )
        else:
            row.status = "published"
            row.name = spec.name
            row.definition = spec.model_dump(mode="json")
    db.flush()

    capabilities = sorted({item for spec in specs for item in spec.capabilities})
    for capability_id in capabilities:
        row = db.get(CapabilityDefinitionRow, (capability_id, 1))
        if row is None:
            db.add(
                CapabilityDefinitionRow(
                    id=capability_id,
                    version=1,
                    name=capability_id.replace(".", " ").title(),
                    status="published",
                    definition={
                        "implementation": "code-defined",
                        "allowlisted": True,
                        "external_write": False,
                    },
                )
            )
        elif row.status != "published":
            row.status = "published"

    if settings is None:
        from agi_server.config import get_settings
        settings = get_settings()

    profile = settings.model_profile if settings else "local-balanced"
    workflow = build_default_workflow(model_profile=profile).model_copy(update={"status": "published"})
    workflow_row = db.get(WorkflowDefinitionRow, (workflow.id, workflow.version))
    if workflow_row is None:
        db.add(
            WorkflowDefinitionRow(
                id=workflow.id,
                version=workflow.version,
                name=workflow.name,
                status="published",
                definition=workflow.model_dump(mode="json"),
            )
        )
    else:
        workflow_row.status = "published"
        workflow_row.definition = workflow.model_dump(mode="json")
    db.commit()


def workflow_from_row(row: WorkflowDefinitionRow) -> WorkflowDefinition:
    return WorkflowDefinition.model_validate(
        {**row.definition, "id": row.id, "version": row.version, "status": row.status}
    )


def latest_workflow(db: Session, workflow_id: str, *, draft_first: bool = True):
    rows = list(
        db.scalars(
            select(WorkflowDefinitionRow)
            .where(WorkflowDefinitionRow.id == workflow_id)
            .order_by(WorkflowDefinitionRow.version.desc())
        )
    )
    if draft_first:
        draft = next((row for row in rows if row.status == "draft"), None)
        if draft is not None:
            return draft
    return rows[0] if rows else None


def save_workflow_draft(
    db: Session,
    definition: WorkflowDefinition,
    actor_id: str | None,
) -> WorkflowDefinitionRow:
    if not SAFE_ID.fullmatch(definition.id):
        raise ValueError("Workflow ID is invalid")
    ensure_platform_registry(db)
    row = db.get(WorkflowDefinitionRow, (definition.id, definition.version))
    if row is not None and row.status != "draft":
        raise ValueError("Published workflow versions are immutable")
    payload = definition.model_copy(update={"status": "draft"}).model_dump(mode="json")
    if row is None:
        max_version = db.scalar(
            select(func.max(WorkflowDefinitionRow.version)).where(
                WorkflowDefinitionRow.id == definition.id
            )
        )
        if max_version is not None:
            raise ValueError("New workflow versions must be created by cloning")
        if definition.version != 1:
            raise ValueError("A new workflow must start at version 1")
        row = WorkflowDefinitionRow(
            id=definition.id,
            version=definition.version,
            name=definition.name,
            status="draft",
            definition=payload,
            created_by=actor_id,
        )
        db.add(row)
    else:
        row.name = definition.name
        row.definition = payload
    db.commit()
    return row


def clone_workflow_version(
    db: Session,
    source: WorkflowDefinitionRow,
    actor_id: str | None,
    *,
    target_id: str | None = None,
) -> WorkflowDefinitionRow:
    workflow_id = target_id or source.id
    if not SAFE_ID.fullmatch(workflow_id):
        raise ValueError("Workflow ID is invalid")
    max_version = db.scalar(
        select(func.max(WorkflowDefinitionRow.version)).where(
            WorkflowDefinitionRow.id == workflow_id
        )
    )
    version = int(max_version or 0) + 1
    payload = deepcopy(source.definition)
    payload.update({"id": workflow_id, "version": version, "status": "draft"})
    row = WorkflowDefinitionRow(
        id=workflow_id,
        version=version,
        name=f"{source.name} (copy)" if target_id else source.name,
        status="draft",
        definition=payload,
        created_by=actor_id,
    )
    db.add(row)
    db.commit()
    return row


def validate_workflow_bindings(
    db: Session, workflow: WorkflowDefinition, settings: Settings | None = None
) -> WorkflowDefinition:
    """Validate and pin registry references the pure graph validator cannot inspect."""
    ensure_platform_registry(db)
    issues: list[str] = []
    agent_ids: set[str] = set()
    pinned_nodes = []
    for node in workflow.nodes:
        if node.kind != NodeKind.AGENT_RUN:
            pinned_nodes.append(node)
            continue
        agent_id = str(node.config.get("agent_id", ""))
        agent_ids.add(agent_id)
        requested_version = node.config.get("agent_version")
        if requested_version is not None and (
            isinstance(requested_version, bool)
            or not isinstance(requested_version, int)
            or requested_version < 1
        ):
            issues.append(f"{node.id}: agent_version must be a positive integer")
            pinned_nodes.append(node)
            continue
        if requested_version is None:
            row = db.scalar(
                select(AgentDefinitionRow)
                .where(
                    AgentDefinitionRow.id == agent_id,
                    AgentDefinitionRow.status == "published",
                )
                .order_by(AgentDefinitionRow.version.desc())
            )
            if row is None:
                issues.append(f"{node.id}: agent '{agent_id}' has no published version")
                pinned_nodes.append(node)
                continue
        else:
            row = db.get(AgentDefinitionRow, (agent_id, requested_version))
            if row is None or row.status != "published":
                issues.append(
                    f"{node.id}: pinned agent '{agent_id}' version {requested_version} is not published"
                )
                pinned_nodes.append(node)
                continue
        spec = agent_from_row(row)
        output_type = node.config.get("output_type")
        if output_type is not None and output_type != spec.output_type:
            issues.append(
                f"{node.id}: output_type '{output_type}' does not match agent '{spec.output_type}'"
            )
        node_caps = node.config.get("capabilities")
        if node_caps is not None:
            if not isinstance(node_caps, (list, set, tuple, frozenset)):
                issues.append(f"{node.id}: capabilities must be a list of capability IDs")
            else:
                invalid_caps = sorted(set(node_caps) - set(spec.capabilities))
                if invalid_caps:
                    issues.append(
                        f"{node.id}: capabilities {invalid_caps} expand beyond published agent spec capabilities {sorted(spec.capabilities)}"
                    )
        profile = node.config.get("model_profile")
        if profile not in {"local-balanced", "local-strong", "cloud-balanced"}:
            issues.append(f"{node.id}: model profile is not allowlisted")
        elif settings is not None:
            try:
                resolve_model_profile(str(profile), settings)
            except Exception as profile_err:
                issues.append(f"{node.id}: model profile '{profile}' is unavailable: {profile_err}")
        pinned_nodes.append(
            node.model_copy(update={"config": {**node.config, "agent_version": row.version}})
        )

    if workflow.id == "builtin-growth-diagnostic":
        required_report_agents = {
            "company-analyst",
            "growth-opportunity-analyst",
            "evidence-reviewer",
            "wiki-curator",
        }
        missing = sorted(required_report_agents - agent_ids)
        if missing:
            issues.append(f"default diagnostic workflow requires built-in agent roles: {missing}")
    if issues:
        raise ValueError(f"Workflow registry binding validation failed: {issues}")
    return workflow.model_copy(update={"nodes": pinned_nodes})


def publish_workflow(db: Session, row: WorkflowDefinitionRow) -> WorkflowDefinitionRow:
    if row.status != "draft":
        raise ValueError("Only a draft can be published")
    workflow = workflow_from_row(row)
    validation = validate_workflow(workflow)
    if not validation.valid:
        raise ValueError(f"Workflow validation failed: {[item.code for item in validation.issues]}")
    workflow = validate_workflow_bindings(db, workflow)
    row.status = "published"
    row.definition = workflow.model_copy(update={"status": "published"}).model_dump(mode="json")
    db.commit()
    return row


def agent_from_row(row: AgentDefinitionRow) -> ManagedAgentSpec:
    return ManagedAgentSpec.model_validate(row.definition)


def clone_agent_version(
    db: Session,
    source: AgentDefinitionRow,
    actor_id: str | None,
) -> AgentDefinitionRow:
    max_version = db.scalar(
        select(func.max(AgentDefinitionRow.version)).where(AgentDefinitionRow.id == source.id)
    )
    version = int(max_version or 0) + 1
    payload = deepcopy(source.definition)
    payload["version"] = version
    row = AgentDefinitionRow(
        id=source.id,
        version=version,
        name=source.name,
        status="draft",
        definition=payload,
        created_by=actor_id,
    )
    db.add(row)
    db.commit()
    return row


def save_agent_draft(
    db: Session,
    spec: ManagedAgentSpec,
    actor_id: str | None,
) -> AgentDefinitionRow:
    unknown = sorted(
        set(spec.capabilities) - set(db.scalars(select(CapabilityDefinitionRow.id)).all())
    )
    if unknown:
        raise ValueError(f"Unknown capabilities: {unknown}")
    row = db.get(AgentDefinitionRow, (spec.id, spec.version))
    if row is not None and row.status != "draft":
        raise ValueError("Published agent versions are immutable")
    if row is None:
        max_version = db.scalar(
            select(func.max(AgentDefinitionRow.version)).where(AgentDefinitionRow.id == spec.id)
        )
        if max_version is not None:
            raise ValueError("New agent versions must be created by cloning")
        if spec.version != 1:
            raise ValueError("A new agent must start at version 1")
        row = AgentDefinitionRow(
            id=spec.id,
            version=spec.version,
            name=spec.name,
            status="draft",
            definition=spec.model_dump(mode="json"),
            created_by=actor_id,
        )
        db.add(row)
    else:
        row.name = spec.name
        row.definition = spec.model_dump(mode="json")
    db.commit()
    return row


def publish_agent(db: Session, row: AgentDefinitionRow) -> AgentDefinitionRow:
    if row.status != "draft":
        raise ValueError("Only an agent draft can be published")
    agent_from_row(row)
    row.status = "published"
    db.commit()
    return row


def validate_schedule(cron: str, timezone: str) -> None:
    fields = cron.split()
    if len(fields) != 5 or any(not CRON_PART.fullmatch(field) for field in fields):
        raise ValueError("Cron must contain five bounded fields")
    bounds = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 6)]
    try:
        for expression, (minimum, maximum) in zip(fields, bounds, strict=True):
            for part in expression.split(","):
                base, _, step_text = part.partition("/")
                if step_text and int(step_text) < 1:
                    raise ValueError
                if base == "*":
                    continue
                values = [int(item) for item in base.split("-")]
                if len(values) > 2 or any(not minimum <= item <= maximum for item in values):
                    raise ValueError
                if len(values) == 2 and values[0] > values[1]:
                    raise ValueError
    except ValueError as error:
        raise ValueError("Cron field is outside its allowed range") from error
    try:
        ZoneInfo(timezone)
    except ZoneInfoNotFoundError as error:
        raise ValueError("Unknown IANA timezone") from error


def create_schedule(
    db: Session,
    workflow: WorkflowDefinitionRow,
    cron: str,
    timezone: str,
    actor_id: str | None,
) -> WorkflowSchedule:
    if workflow.status != "published":
        raise ValueError("Schedules must reference a published workflow version")
    validate_schedule(cron, timezone)
    row = WorkflowSchedule(
        workflow_id=workflow.id,
        workflow_version=workflow.version,
        cron=cron,
        timezone=timezone,
        created_by=actor_id,
    )
    db.add(row)
    db.commit()
    return row
