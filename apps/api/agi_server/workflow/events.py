from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from agi_server.db import EventDispatchQueue, EventInbox, WorkflowDefinitionRow
from agi_server.workflow.triggers import trigger_engine


def ingest_webhook_event(
    db: Session,
    source_id: str,
    event_type: str,
    payload: dict[str, Any],
    idempotency_key: str | None = None,
) -> tuple[EventInbox, list[EventDispatchQueue]]:
    """Ingest webhook payload as untrusted input into PostgreSQL EventInbox and dispatch queue."""
    if idempotency_key:
        stmt = select(EventInbox).where(EventInbox.idempotency_key == idempotency_key)
        existing = db.scalars(stmt).first()
        if existing is not None:
            dispatches = list(
                db.scalars(
                    select(EventDispatchQueue).where(
                        EventDispatchQueue.event_id == existing.id
                    )
                )
            )
            return existing, dispatches

    event_id = f"evt-{uuid.uuid4()}"
    matched_rules = trigger_engine.match_rules(event_type)
    dispatches: list[EventDispatchQueue] = []

    for rule in matched_rules:
        # Verify target workflow has a published version
        stmt = select(WorkflowDefinitionRow).where(
            WorkflowDefinitionRow.id == rule.target_workflow_id,
            WorkflowDefinitionRow.status == "published",
        )
        published_wf = db.scalars(stmt).first()

        dispatch = EventDispatchQueue(
            id=f"disp-{uuid.uuid4()}",
            event_id=event_id,
            trigger_rule_id=rule.id,
            target_workflow_id=rule.target_workflow_id,
            target_workflow_version=published_wf.version if published_wf else None,
            status="queued" if published_wf else "skipped",
            error=None if published_wf else "Target workflow is not published",
        )
        dispatches.append(dispatch)

    status = "triggered" if dispatches else "no_match"
    inbox_row = EventInbox(
        id=event_id,
        source_id=source_id,
        event_type=event_type,
        idempotency_key=idempotency_key,
        payload=payload,
        status=status,
        matched_rules_count=len(dispatches),
    )

    db.add(inbox_row)
    for dispatch in dispatches:
        db.add(dispatch)
    db.commit()

    return inbox_row, dispatches
