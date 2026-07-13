from __future__ import annotations

import re
from copy import deepcopy
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from agi_server.agents.registry import AgentRegistry, ManagedAgentSpec
from agi_server.db import (
    AgentDefinitionRow,
    CapabilityDefinitionRow,
    WorkflowDefinitionRow,
    WorkflowSchedule,
)
from agi_server.workflow.default import build_default_workflow
from agi_server.workflow.models import WorkflowDefinition
from agi_server.workflow.validator import validate_workflow

SAFE_ID = re.compile(r"^[a-z][a-z0-9_-]{2,79}$")
CRON_PART = re.compile(r"^[0-9*/,\-]+$")


def ensure_platform_registry(db: Session) -> None:
    specs = AgentRegistry().list()
    for spec in specs:
        if db.get(AgentDefinitionRow, (spec.id, spec.version)) is None:
            db.add(
                AgentDefinitionRow(
                    id=spec.id,
                    version=spec.version,
                    name=spec.name,
                    status="published",
                    definition=spec.model_dump(mode="json"),
                )
            )
    capabilities = sorted({item for spec in specs for item in spec.capabilities})
    for capability_id in capabilities:
        if db.get(CapabilityDefinitionRow, (capability_id, 1)) is None:
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
    workflow = build_default_workflow().model_copy(update={"status": "published"})
    if db.get(WorkflowDefinitionRow, (workflow.id, workflow.version)) is None:
        db.add(
            WorkflowDefinitionRow(
                id=workflow.id,
                version=workflow.version,
                name=workflow.name,
                status="published",
                definition=workflow.model_dump(mode="json"),
            )
        )
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
    row = db.get(WorkflowDefinitionRow, (definition.id, definition.version))
    if row is not None and row.status != "draft":
        raise ValueError("Published workflow versions are immutable")
    payload = definition.model_copy(update={"status": "draft"}).model_dump(mode="json")
    if row is None:
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


def publish_workflow(db: Session, row: WorkflowDefinitionRow) -> WorkflowDefinitionRow:
    if row.status != "draft":
        raise ValueError("Only a draft can be published")
    workflow = workflow_from_row(row)
    validation = validate_workflow(workflow)
    if not validation.valid:
        raise ValueError(f"Workflow validation failed: {[item.code for item in validation.issues]}")
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
