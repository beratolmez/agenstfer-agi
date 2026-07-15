from __future__ import annotations

import argparse
import asyncio
import json
import os
import platform
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx
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


def local_memory_mib() -> int | None:
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal:"):
                return int(line.split()[1]) // 1024
    except (OSError, ValueError, IndexError):
        return None
    return None


async def ollama_runtime(settings: Settings, model_name: str) -> dict[str, object] | None:
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            response = await client.get(settings.ollama_base_url.removesuffix("/v1") + "/api/ps")
            response.raise_for_status()
        for model in response.json().get("models", []):
            if model.get("name") == model_name:
                return {
                    "context_length": model.get("context_length"),
                    "size": model.get("size"),
                    "size_vram": model.get("size_vram"),
                }
    except (httpx.HTTPError, ValueError, TypeError):
        return None
    return None


async def evaluate(profile_id: str, attempts: int) -> dict[str, object]:
    base_settings = Settings(model_profile=profile_id)
    profile = resolve_model_profile(profile_id, base_settings)
    outputs: list[list[str]] = []
    errors: list[str] = []
    failure_stages: list[dict[str, object]] = []
    planted_counts: list[int] = []
    evidence_coverage: list[int] = []
    unsupported_numerical_counts: list[int] = []
    attempt_results: list[dict[str, object]] = []
    started = time.perf_counter()
    for index in range(attempts):
        attempt_started = time.perf_counter()
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
                    output = result.run.output_json or {}
                    company = output.get("company_analysis", {})
                    hypotheses = output.get("hypotheses", {}).get("hypotheses", [])
                    decisions = output.get("evidence_review", {}).get("decisions", [])
                    expected_claims = (
                        len(company.get("strengths", []))
                        + len(company.get("weaknesses", []))
                        + len(hypotheses)
                        + 5
                    )
                    supported_decisions = [item for item in decisions if item.get("supported")]
                    coverage = round(100 * len(supported_decisions) / max(1, expected_claims))
                    evidence_coverage.append(coverage)
                    numerical_ids = {
                        f"metric-{item.id}" for item in result.diagnostic.opportunities
                    }
                    supported_ids = {
                        item.get("claim_id") for item in supported_decisions if item.get("claim_id")
                    }
                    unsupported_count = len(numerical_ids - supported_ids)
                    unsupported_numerical_counts.append(unsupported_count)
                    attempt_results.append(
                        {
                            "attempt": index + 1,
                            "status": "passed",
                            "duration_seconds": round(time.perf_counter() - attempt_started, 2),
                            "token_usage": result.run.token_usage,
                            "material_claim_count": expected_claims,
                            "supported_claim_count": len(supported_decisions),
                            "unsupported_numerical_claims": unsupported_count,
                        }
                    )
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
                    attempt_results.append(
                        {
                            "attempt": index + 1,
                            "status": "failed",
                            "duration_seconds": round(time.perf_counter() - attempt_started, 2),
                            "error_class": type(error).__name__,
                            "failure_step": None if failed_step is None else failed_step.step_id,
                        }
                    )
            finally:
                engine.dispose()
    success_rate = len(outputs) / attempts
    repeated_overlap = min((overlap(outputs[0], item) for item in outputs[1:]), default=1.0)
    checks = {
        "planted_cases": bool(planted_counts) and min(planted_counts) >= 5,
        "material_claim_evidence": bool(evidence_coverage) and min(evidence_coverage) == 100,
        "unsupported_numerical_claims": (
            bool(unsupported_numerical_counts)
            and max(unsupported_numerical_counts) == 0
        ),
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
        "attempt_results": attempt_results,
        "agent_versions": {item.id: item.version for item in AgentRegistry().list()},
        "platform": {
            "system": platform.system(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "cpu_count": os.cpu_count(),
            "memory_total_mib": local_memory_mib(),
        },
        "ollama_runtime": (
            await ollama_runtime(base_settings, profile.model_name) if profile.local else None
        ),
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
