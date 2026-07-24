from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from agi_server.config import Settings
from agi_server.db import (
    ApprovalRequest,
    SessionLocal,
    WorkflowDefinitionRow,
    WorkflowSchedule,
)
from agi_server.workflow.persistent_runtime import expire_approval_state, start_persisted_workflow


def _field_matches(value: int, expression: str, minimum: int, maximum: int) -> bool:
    def matches_part(part: str) -> bool:
        base, _, step_text = part.partition("/")
        step = int(step_text) if step_text else 1
        if step < 1:
            return False
        if base == "*":
            start, end = minimum, maximum
        elif "-" in base:
            start_text, end_text = base.split("-", 1)
            start, end = int(start_text), int(end_text)
        else:
            return value == int(base)
        return minimum <= start <= value <= end <= maximum and (value - start) % step == 0

    try:
        return any(matches_part(part) for part in expression.split(","))
    except (TypeError, ValueError):
        return False


def cron_matches(cron: str, instant: datetime, timezone: str) -> bool:
    local = instant.astimezone(ZoneInfo(timezone))
    minute, hour, day, month, weekday = cron.split()
    cron_weekday = (local.weekday() + 1) % 7
    return all(
        [
            _field_matches(local.minute, minute, 0, 59),
            _field_matches(local.hour, hour, 0, 23),
            _field_matches(local.day, day, 1, 31),
            _field_matches(local.month, month, 1, 12),
            _field_matches(cron_weekday, weekday, 0, 6),
        ]
    )


async def run_due_schedules(
    db: Session,
    settings: Settings,
    now: datetime | None = None,
) -> list[str]:
    instant = now or datetime.now(UTC)
    started: list[str] = []
    rows = list(db.scalars(select(WorkflowSchedule).where(WorkflowSchedule.enabled.is_(True))))
    for schedule in rows:
        if not cron_matches(schedule.cron, instant, schedule.timezone):
            continue
        local = instant.astimezone(ZoneInfo(schedule.timezone))
        fire_key = f"{schedule.id}:{local:%Y%m%d%H%M}"
        if schedule.last_fire_key == fire_key:
            continue
        workflow = db.get(
            WorkflowDefinitionRow,
            (schedule.workflow_id, schedule.workflow_version),
        )
        if workflow is None or workflow.status != "published":
            schedule.enabled = False
            db.commit()
            continue
        schedule.last_fire_key = fire_key
        db.commit()
        try:
            run = await start_persisted_workflow(
                db,
                settings,
                workflow,
                f"schedule:{fire_key}",
                schedule.created_by,
                input_json={"schedule_id": schedule.id, "fire_key": fire_key},
            )
            started.append(run.id)
        except Exception:
            # start_persisted_workflow persists a content-safe failed run when execution starts.
            continue
    return started


def expire_approvals(db: Session, now: datetime | None = None) -> int:
    instant = now or datetime.now(UTC)
    rows = list(
        db.scalars(
            select(ApprovalRequest)
            .where(
                ApprovalRequest.status.in_(["pending", "decision_submitted"]),
                ApprovalRequest.expires_at <= instant,
            )
            .with_for_update(skip_locked=True)
        )
    )
    for approval in rows:
        expire_approval_state(db, approval, instant)
    db.commit()
    return len(rows)


async def dispatch_queued_events(
    db: Session,
    settings: Settings,
) -> list[str]:
    from agi_server.db import EventDispatchQueue, EventInbox

    dispatched_run_ids: list[str] = []
    stmt = (
        select(EventDispatchQueue)
        .where(EventDispatchQueue.status == "queued")
        .with_for_update(skip_locked=True)
    )
    queued_items = list(db.scalars(stmt))

    for item in queued_items:
        version = item.target_workflow_version
        if version is None:
            stmt_wf = select(WorkflowDefinitionRow).where(
                WorkflowDefinitionRow.id == item.target_workflow_id,
                WorkflowDefinitionRow.status == "published",
            )
            wf_row = db.scalars(stmt_wf).first()
            if wf_row is None:
                item.status = "skipped"
                item.error = "Target workflow is not published"
                db.commit()
                continue
            version = wf_row.version
        else:
            wf_row = db.get(WorkflowDefinitionRow, (item.target_workflow_id, version))

        if wf_row is None or wf_row.status != "published":
            item.status = "skipped"
            item.error = "Target workflow is not published"
            db.commit()
            continue

        inbox_event = db.get(EventInbox, item.event_id)
        payload = inbox_event.payload if inbox_event else {}

        try:
            run = await start_persisted_workflow(
                db,
                settings,
                wf_row,
                f"event:{item.event_id}",
                actor_id=None,
                input_json={"event_id": item.event_id, "payload": payload},
            )
            item.status = "dispatched"
            item.workflow_run_id = run.id
            item.dispatched_at = datetime.now(UTC)
            db.commit()
            dispatched_run_ids.append(run.id)
        except Exception as exc:
            item.status = "failed"
            item.error = str(exc)
            db.commit()

    return dispatched_run_ids


async def scheduler_loop(settings: Settings) -> None:
    while True:
        with SessionLocal() as db:
            expire_approvals(db)
            await run_due_schedules(db, settings)
            await dispatch_queued_events(db, settings)
        await asyncio.sleep(30)
