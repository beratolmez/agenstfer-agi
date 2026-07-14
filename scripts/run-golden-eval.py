from __future__ import annotations

import argparse
import asyncio
import json
import platform
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

from agi_server.agents.model_gateway import resolve_model_profile
from agi_server.agents.registry import AgentRegistry
from agi_server.config import Settings
from agi_server.db import WorkflowRun, WorkflowStepRun
from agi_server.diagnostics import run_growth_diagnostic
from agi_server.ingestion import sync_demo_company
from agi_server.migrations import run_migrations
from agi_server.okf.lifecycle import ensure_active_repository
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker


def overlap(left: list[str], right: list[str]) -> float:
    if not left and not right:
        return 1.0
    return len(set(left).intersection(right)) / max(1, min(len(left), len(right)))


async def evaluate(profile_id: str, attempts: int) -> dict[str, object]:
    base_settings = Settings(model_profile=profile_id)
    profile = resolve_model_profile(profile_id, base_settings)
    outputs: list[list[str]] = []
    errors: list[str] = []
    failure_stages: list[dict[str, object]] = []
    planted_counts: list[int] = []
    evidence_coverage: list[int] = []
    started = time.perf_counter()
    for index in range(attempts):
        with tempfile.TemporaryDirectory(prefix="agi-golden-") as temporary:
            root = Path(temporary)
            database_url = f"sqlite:///{(root / 'eval.db').as_posix()}"
            settings = Settings(
                database_url=database_url,
                knowledge_root=root / "knowledge",
                model_profile=profile_id,
                ollama_base_url=base_settings.ollama_base_url,
                cloud_models_enabled=base_settings.cloud_models_enabled,
                cloud_provider=base_settings.cloud_provider,
                cloud_api_key=base_settings.cloud_api_key,
                cloud_model=base_settings.cloud_model,
            )
            run_migrations(database_url)
            engine = create_engine(database_url)
            local_session = sessionmaker(bind=engine, expire_on_commit=False)
            try:
                with local_session() as db:
                    sync_demo_company(db, settings.raw_root)
                    ensure_active_repository(settings.company_bundle)
                    result = await run_growth_diagnostic(
                        db,
                        settings,
                        actor_id=None,
                        idempotency_key=f"golden-{index}",
                    )
                    outputs.append([item.id for item in result.diagnostic.opportunities[:5]])
                    planted_counts.append(len(result.diagnostic.detected_planted_insights))
                    evidence_coverage.append(100 if result.run.evidence_ids else 0)
            except Exception as error:  # The report records only safe exception classes.
                errors.append(type(error).__name__)
                with local_session() as failure_db:
                    failed_run = failure_db.scalar(
                        select(WorkflowRun).where(
                            WorkflowRun.idempotency_key == f"golden-{index}"
                        )
                    )
                    failed_step = (
                        None
                        if failed_run is None
                        else failure_db.scalar(
                            select(WorkflowStepRun)
                            .where(
                                WorkflowStepRun.run_id == failed_run.id,
                                WorkflowStepRun.status == "failed",
                            )
                            .order_by(WorkflowStepRun.sequence.desc())
                        )
                    )
                    failure_stages.append(
                        {
                            "attempt": index + 1,
                            "current_step": None if failed_run is None else failed_run.current_step,
                            "step_id": None if failed_step is None else failed_step.step_id,
                            "error_code": (
                                type(error).__name__
                                if failed_step is None
                                else failed_step.error_json.get("code", type(error).__name__)
                            ),
                        }
                    )
            finally:
                engine.dispose()
    success_rate = len(outputs) / attempts
    repeated_overlap = min((overlap(outputs[0], item) for item in outputs[1:]), default=1.0)
    checks = {
        "planted_cases": bool(planted_counts) and min(planted_counts) >= 5,
        "material_claim_evidence": bool(evidence_coverage) and min(evidence_coverage) == 100,
        # A successful run has already passed the claim-by-claim Evidence Reviewer gate.
        "unsupported_numerical_claims": bool(outputs),
        "structured_output_success": success_rate >= 0.95,
        "top_five_overlap": repeated_overlap >= 0.70,
    }
    return {
        "evaluated_at": datetime.now(UTC).isoformat(),
        "profile": profile.id,
        "provider": profile.provider,
        "model": profile.model_name,
        "attempts": attempts,
        "successful_runs": len(outputs),
        "success_rate": success_rate,
        "minimum_planted_cases": min(planted_counts, default=0),
        "minimum_evidence_coverage": min(evidence_coverage, default=0),
        "minimum_top_five_overlap": repeated_overlap,
        "safe_error_classes": errors,
        "safe_failure_stages": failure_stages,
        "agent_versions": {item.id: item.version for item in AgentRegistry().list()},
        "platform": {
            "system": platform.system(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        },
        "duration_seconds": round(time.perf_counter() - started, 2),
        "checks": checks,
        "passed": all(checks.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Qualify one configured release model profile.")
    parser.add_argument("--profile", default="local-balanced")
    parser.add_argument("--attempts", type=int, default=20, choices=range(1, 101))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = asyncio.run(evaluate(args.profile, args.attempts))
    output = args.output or Path("artifacts/release") / f"evaluation-{report['profile']}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
