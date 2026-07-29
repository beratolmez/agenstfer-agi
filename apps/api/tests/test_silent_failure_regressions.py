"""Regressions for three defects that failed silently instead of surfacing.

Each of these shipped for a while because nothing observed the failing path: the
scheduler died without a log line, the fallback runtime raised inside its own error
handler, and the MCP endpoint was only ever tested with ``db=None``.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from agi_server.config import Settings
from agi_server.db import Base, MCPProfile, WorkflowDefinitionRow, WorkflowRun
from agi_server.main import MCPTestRequest, source_test_mcp
from agi_server.workflow import scheduler
from agi_server.workflow.default import build_default_workflow
from agi_server.workflow.persistent_runtime import start_persisted_workflow
from agi_server.workflow.registry_service import (
    clone_workflow_version,
    ensure_platform_registry,
    publish_workflow,
    save_workflow_draft,
    workflow_from_row,
)
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker


def _database(tmp_path: Path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'regressions.db').as_posix()}")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine, expire_on_commit=False)


# R1 -------------------------------------------------------------------------


def test_scheduler_loop_keeps_ticking_after_a_failing_tick(monkeypatch) -> None:
    """A single bad tick must not end the loop for the rest of the process lifetime."""
    ticks = {"count": 0}

    def failing_expire(_db):
        ticks["count"] += 1
        raise RuntimeError("database is unreachable")

    async def stop_after_two_ticks(_seconds):
        if ticks["count"] >= 2:
            raise asyncio.CancelledError

    monkeypatch.setattr(scheduler, "expire_approvals", failing_expire)
    monkeypatch.setattr(asyncio, "sleep", stop_after_two_ticks)

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(scheduler.scheduler_loop(Settings(_env_file=None)))

    # The loop reached a second tick, so the first failure did not terminate it.
    assert ticks["count"] >= 2


# R2 -------------------------------------------------------------------------


def test_failed_run_records_error_instead_of_staying_running(tmp_path: Path) -> None:
    """The fallback runtime must persist the failure, not raise inside its handler.

    It previously read ``active_step.node_id``; the column is ``step_id``, so the
    error handler itself raised AttributeError, the original error was lost and the
    run stayed ``running`` forever.
    """
    engine, local_session = _database(tmp_path)
    knowledge_root = tmp_path / "knowledge"
    settings = Settings(_env_file=None, knowledge_root=knowledge_root, qmd_url=None)

    with local_session() as db:
        ensure_platform_registry(db)
        builtin = build_default_workflow()
        source = db.get(WorkflowDefinitionRow, (builtin.id, builtin.version))
        assert source is not None

        # A non-builtin id routes to the fallback engine rather than LangGraph.
        draft = clone_workflow_version(db, source, None, target_id="fallback-regression")
        definition = workflow_from_row(draft)
        broken_nodes = [
            node.model_copy(update={"config": {**node.config, "connector_id": "not-allowlisted"}})
            if node.id == "sync"
            else node
            for node in definition.nodes
        ]
        save_workflow_draft(db, definition.model_copy(update={"nodes": broken_nodes}), None)
        publish_workflow(db, draft)

        with pytest.raises(ValueError):
            asyncio.run(
                start_persisted_workflow(db, settings, draft, "fallback-regression-001", None)
            )

        run = db.scalar(
            select(WorkflowRun).where(WorkflowRun.idempotency_key == "fallback-regression-001")
        )
        assert run is not None
        assert run.status == "failed"
        assert run.error_json, "the failure must be persisted, not swallowed"
        assert run.error_json.get("node_id") == "sync"
    engine.dispose()


# R3 -------------------------------------------------------------------------


def test_source_test_mcp_rejects_unapproved_server_with_a_live_session(tmp_path: Path) -> None:
    """The approval lookup must work against a real session, not only ``db=None``.

    It previously queried ``MCPProfile.server_url``, a column that does not exist, so
    every real request raised AttributeError and returned 500.
    """
    engine, local_session = _database(tmp_path)
    with local_session() as db:
        payload = MCPTestRequest(mcp_url="https://mcp.unapproved.invalid/rpc")
        with pytest.raises(HTTPException) as exc_info:
            source_test_mcp(payload, db=db, actor=None)
        assert exc_info.value.status_code == 400
        assert "Onaylanmamış MCP sunucusu" in exc_info.value.detail
    engine.dispose()


def test_source_test_mcp_finds_an_approved_profile_by_server_identity(tmp_path: Path) -> None:
    """An approved profile is matched on server_identity and gets past the allowlist gate."""
    engine, local_session = _database(tmp_path)
    with local_session() as db:
        db.add(
            MCPProfile(
                id="mcp-approved",
                name="Approved Read-Only MCP",
                server_identity="https://mcp.approved.invalid/rpc",
                allowed_tools=["get_crm_account"],
            )
        )
        db.commit()

        payload = MCPTestRequest(mcp_url="https://mcp.approved.invalid/rpc")
        # The host is unreachable, so this still fails - but on the connection, which
        # proves the profile lookup succeeded rather than rejecting on the allowlist.
        with pytest.raises(HTTPException) as exc_info:
            source_test_mcp(payload, db=db, actor=None)
        assert "Onaylanmamış MCP sunucusu" not in exc_info.value.detail
    engine.dispose()


# R4 -------------------------------------------------------------------------


def test_cloud_redaction_preserves_evidence_identifiers() -> None:
    """Redaction must not corrupt the identifiers the evidence gate resolves against.

    The phone pattern previously guarded only digit boundaries, so a digit run inside a hex
    evidence id matched. Prompts sent to a cloud model carried "ev-ca2e[REDACTED_PHONE]f026",
    the model cited that mangled id, and the gate rejected the claim as unresolvable.
    """
    from agi_server.agents.runtime import redact_identifiers

    evidence_id = "ev-2a0cc365f38caa31f118cb0dfbfa984f0ed675c176fe7cf9e0b7d55e45e63c4d"
    prompt = f"Bu iddiayi {evidence_id} kanitina bagla."
    assert redact_identifiers(prompt) == prompt

    # Real contact identifiers must still be removed before a cloud call.
    assert "[REDACTED_PHONE]" in redact_identifiers("Bize +90 212 555 0000 numarasindan ulasin")
    assert "[REDACTED_EMAIL]" in redact_identifiers("info@aisfer.com adresine yazin")
