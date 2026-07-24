import asyncio
from pathlib import Path

from agi_server.config import Settings
from agi_server.db import (
    ApprovalRequest,
    Base,
    OKFCandidate,
    WorkflowDefinitionRow,
    WorkflowStepRun,
)
from agi_server.ingestion import sync_demo_company
from agi_server.okf.git_repo import GitKnowledgeRepository
from agi_server.okf.lifecycle import ensure_active_repository
from agi_server.workflow.default import build_default_workflow
from agi_server.workflow.langgraph_runtime import LangGraphWorkflowEngine
from agi_server.workflow.persistent_runtime import (
    decide_persisted_approval,
    start_persisted_workflow,
)
from agi_server.workflow.registry_service import ensure_platform_registry, workflow_from_row
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from tests.test_workflow_platform import _models


def _database(tmp_path: Path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'langgraph_test.db').as_posix()}")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine, expire_on_commit=False)


def test_langgraph_engine_execution_and_pause_resume(tmp_path: Path) -> None:
    engine, local_session = _database(tmp_path)
    knowledge_root = tmp_path / "knowledge"
    settings = Settings(knowledge_root=knowledge_root, qmd_url=None)

    with local_session() as db:
        sync_demo_company(db, settings.raw_root)
        ensure_active_repository(settings.company_bundle)
        ensure_platform_registry(db)
        models = _models(db)

        workflow_row = db.get(
            WorkflowDefinitionRow,
            (build_default_workflow().id, build_default_workflow().version),
        )
        assert workflow_row is not None
        workflow = workflow_from_row(workflow_row)
        assert len(workflow.nodes) == 12

        run = asyncio.run(
            start_persisted_workflow(
                db,
                settings,
                workflow_row,
                "lg-workflow-test-001",
                None,
                model_overrides=models,
            )
        )

        assert run.status == "awaiting_approval"
        assert run.agent_versions == {
            "company-analyst": 3,
            "growth-opportunity-analyst": 3,
            "evidence-reviewer": 3,
            "wiki-curator": 2,
        }

        approval = db.scalar(select(ApprovalRequest).where(ApprovalRequest.run_id == run.id))
        assert approval is not None
        assert approval.status == "pending"

        assert (
            db.scalar(
                select(WorkflowStepRun)
                .where(WorkflowStepRun.run_id == run.id)
                .with_only_columns(WorkflowStepRun.id)
            )
            is not None
        )

        candidate_id = db.scalar(select(OKFCandidate.id).where(OKFCandidate.run_id == run.id))
        assert candidate_id is not None
        before_revision = GitKnowledgeRepository(settings.company_bundle).ensure_baseline()

        resumed_run, qmd = asyncio.run(
            decide_persisted_approval(
                db,
                settings,
                approval,
                decision="approved",
                reason="LangGraph default workflow test approved.",
                actor_id=None,
                idempotency_key="lg-approval-decision-001",
            )
        )

        assert resumed_run.id == run.id
        assert resumed_run.status == "completed"
        assert db.get(OKFCandidate, candidate_id).status == "approved"
        after_revision = GitKnowledgeRepository(settings.company_bundle).ensure_baseline()
        assert after_revision != before_revision

    engine.dispose()


def test_langgraph_engine_direct_invocation(tmp_path: Path) -> None:
    engine, local_session = _database(tmp_path)
    knowledge_root = tmp_path / "knowledge"
    settings = Settings(knowledge_root=knowledge_root, qmd_url=None)

    with local_session() as db:
        sync_demo_company(db, settings.raw_root)
        ensure_active_repository(settings.company_bundle)
        ensure_platform_registry(db)
        models = _models(db)

        workflow_row = db.get(
            WorkflowDefinitionRow,
            (build_default_workflow().id, build_default_workflow().version),
        )
        assert workflow_row is not None
        workflow = workflow_from_row(workflow_row)

        run = asyncio.run(
            start_persisted_workflow(
                db,
                settings,
                workflow_row,
                "lg-direct-test-001",
                None,
                model_overrides=models,
            )
        )

        engine_inst = LangGraphWorkflowEngine(
            db, settings, run, workflow, model_overrides=models
        )
        assert engine_inst.graph is not None

    engine.dispose()
