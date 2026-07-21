from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest
from agi_server.config import Settings
from agi_server.db import AuditEvent, Base, WorkflowDefinitionRow
from agi_server.main import (
    agent_version_detail,
    run_diagnostic,
    setup_progress_update,
    workflow_schedule_update,
)
from agi_server.schemas import SetupProgressUpdate
from agi_server.workflow.registry_service import create_schedule, ensure_platform_registry
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker


def _database(tmp_path: Path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'compatibility.db').as_posix()}")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine, expire_on_commit=False)


def test_diagnostic_compatibility_view_starts_only_the_published_pinned_workflow(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    engine, local_session = _database(tmp_path)
    settings = Settings(knowledge_root=tmp_path / "knowledge")
    captured: dict[str, object] = {}

    async def fake_start(db, received_settings, workflow, key, actor_id, *, input_json):
        captured.update(
            {
                "settings": received_settings,
                "workflow": workflow,
                "key": key,
                "actor_id": actor_id,
                "input": input_json,
            }
        )
        return SimpleNamespace(
            id="11111111-1111-4111-8111-111111111111",
            status="running",
            current_step="company_agent",
            model_profile="local-balanced",
        )

    monkeypatch.setattr("agi_server.main.start_persisted_workflow", fake_start)
    with local_session() as db:
        ensure_platform_registry(db)
        response = asyncio.run(
            run_diagnostic(
                db,
                None,
                settings,
                "compatibility-run-001",
                "builtin-growth-diagnostic",
                3,
            )
        )
        workflow = captured["workflow"]
        assert isinstance(workflow, WorkflowDefinitionRow)
        assert workflow.id == "builtin-growth-diagnostic"
        assert workflow.version == 3
        assert workflow.status == "published"
        assert captured["input"] == {"compatibility_view": "diagnostics.run"}
        assert response == {
            "run_id": "11111111-1111-4111-8111-111111111111",
            "status": "running",
            "current_step": "company_agent",
            "workflow_id": "builtin-growth-diagnostic",
            "workflow_version": 3,
            "model_profile": "local-balanced",
        }
        audit = db.scalar(select(AuditEvent).where(AuditEvent.action == "diagnostic.run_started"))
        assert audit is not None
        assert audit.target_id == response["run_id"]
    engine.dispose()


def test_diagnostic_compatibility_view_rejects_a_draft_version(tmp_path: Path) -> None:
    engine, local_session = _database(tmp_path)
    settings = Settings(knowledge_root=tmp_path / "knowledge")
    with local_session() as db:
        ensure_platform_registry(db)
        published = db.get(WorkflowDefinitionRow, ("builtin-growth-diagnostic", 3))
        assert published is not None
        draft = WorkflowDefinitionRow(
            id="draft-diagnostic",
            version=1,
            name="Draft diagnostic",
            status="draft",
            definition=published.definition,
        )
        db.add(draft)
        db.commit()

        with pytest.raises(HTTPException) as rejected:
            asyncio.run(
                run_diagnostic(
                    db,
                    None,
                    settings,
                    "compatibility-run-002",
                    draft.id,
                    draft.version,
                )
            )
        assert rejected.value.status_code == 404
    engine.dispose()





@pytest.mark.parametrize("profile", ["unknown-provider", "cloud-balanced"])
def test_setup_rejects_unknown_or_disabled_model_profiles(
    tmp_path: Path, profile: str
) -> None:
    engine, local_session = _database(tmp_path)
    settings = Settings(knowledge_root=tmp_path / "knowledge")
    payload = SetupProgressUpdate(
        current_step=2,
        completed_steps=[0, 1],
        configuration={
            "company_name": "Anka Endüstriyel Otomasyon",
            "objective": "Mevcut müşterilerden kanıtlı büyüme üretmek",
            "model_profile": profile,
            "source_mode": "synthetic-demo",
            "locale": "tr-TR",
        },
    )
    with local_session() as db, pytest.raises(HTTPException) as rejected:
        setup_progress_update(payload, settings, db, None)
    assert rejected.value.status_code == 422
    engine.dispose()


def test_admin_agent_detail_survives_refresh_with_the_versioned_prompt(tmp_path: Path) -> None:
    engine, local_session = _database(tmp_path)
    with local_session() as db:
        ensure_platform_registry(db)

        detail = agent_version_detail("company-analyst", 3, db, None)

        assert detail["id"] == "company-analyst"
        assert detail["version"] == 3
        assert detail["status"] == "published"
        assert "system_prompt" in detail
        assert len(detail["system_prompt"]) > 20
    engine.dispose()


def test_admin_can_disable_and_reenable_a_persisted_schedule_with_audit(
    tmp_path: Path,
) -> None:
    engine, local_session = _database(tmp_path)
    with local_session() as db:
        ensure_platform_registry(db)
        workflow = db.get(WorkflowDefinitionRow, ("builtin-growth-diagnostic", 3))
        assert workflow is not None
        schedule = create_schedule(db, workflow, "15 9 * * 1-5", "Europe/Istanbul", None)

        disabled = workflow_schedule_update(schedule.id, db, None, False)
        enabled = workflow_schedule_update(schedule.id, db, None, True)

        assert disabled["enabled"] is False
        assert enabled["enabled"] is True
        actions = list(
            db.scalars(
                select(AuditEvent.action)
                .where(AuditEvent.target_id == schedule.id)
                .order_by(AuditEvent.occurred_at)
            )
        )
        assert actions == ["workflow.schedule_disabled", "workflow.schedule_enabled"]
    engine.dispose()
