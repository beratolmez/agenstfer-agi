from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any

import httpx
from dbos import DBOS, DBOSConfig, SetWorkflowID
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from agi_server import __version__
from agi_server.agents import AgentRegistry
from agi_server.agents.model_gateway import resolve_model_profile
from agi_server.config import Settings, get_settings
from agi_server.db import get_db, init_db
from agi_server.domain.demo import build_demo_dataset, demo_counts
from agi_server.domain.diagnostic import build_growth_diagnostic
from agi_server.ingestion import RawVault
from agi_server.okf import FileSystemOKFBundle
from agi_server.okf.compiler import compile_demo_bundle
from agi_server.okf.git_repo import GitKnowledgeRepository
from agi_server.okf.search import KnowledgeSearch
from agi_server.schemas import GrowthDiagnostic, HealthResponse
from agi_server.security import (
    BootstrapRequest,
    LoginRequest,
    UserView,
    authenticate,
    bootstrap_admin,
    require_role,
)
from agi_server.workflow import build_default_workflow, validate_workflow
from agi_server.workflow.models import WorkflowDefinition, WorkflowValidation
from agi_server.workflow.runtime import durable_workflow_interpreter, run_workflow_locally


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    settings = get_settings()
    if not settings.company_bundle.joinpath("index.md").exists():
        compile_demo_bundle(settings.company_bundle)
    if settings.enable_dbos:
        DBOS.launch()
    yield
    if settings.enable_dbos:
        DBOS.destroy(workflow_completion_timeout_sec=5)


app = FastAPI(
    title="Agentic Growth Intelligence API",
    version=__version__,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)
settings = get_settings()
if settings.enable_dbos:
    dbos_url = settings.database_url.replace("postgresql+psycopg://", "postgresql://")
    DBOS(
        config=DBOSConfig(
            name="agi-control-plane",
            database_url=dbos_url,
            application_version=__version__,
            run_admin_server=False,
        ),
        fastapi=app,
    )
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    session_cookie="agi_session",
    same_site="strict",
    https_only=settings.environment == "production",
    max_age=8 * 60 * 60,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)


@app.get("/api/health", response_model=HealthResponse)
async def health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    components = {"api": "ok", "postgres": "configured", "okf": "ok"}
    try:
        async with httpx.AsyncClient(timeout=1) as client:
            response = await client.get(settings.ollama_base_url.removesuffix("/v1") + "/api/tags")
            response.raise_for_status()
        components["ollama"] = "ok"
    except httpx.HTTPError:
        components["ollama"] = "unavailable; deterministic demo active"
    status_value = "ok" if components["ollama"] == "ok" else "degraded"
    return HealthResponse(
        status=status_value,
        version=__version__,
        mode="local-first",
        components=components,
    )


@app.get("/api/model/status")
async def model_status(settings: Annotated[Settings, Depends(get_settings)]) -> dict[str, Any]:
    """Expose configuration state without ever returning the provider secret."""
    try:
        profile = resolve_model_profile(settings.model_profile, settings)
    except (PermissionError, ValueError) as error:
        return {
            "ready": False,
            "profile": settings.model_profile,
            "provider": settings.cloud_provider or "ollama",
            "message": str(error),
        }
    if profile.local:
        try:
            async with httpx.AsyncClient(timeout=1) as client:
                tags_url = settings.ollama_base_url.removesuffix("/v1") + "/api/tags"
                response = await client.get(tags_url)
                response.raise_for_status()
            installed = {item.get("name") for item in response.json().get("models", [])}
        except httpx.HTTPError:
            installed = set()
        if profile.model_name not in installed:
            return {
                "ready": False,
                "profile": profile.id,
                "provider": profile.provider,
                "model": profile.model_name,
                "local": True,
                "message": "Ollama erişilebilir, fakat seçili model henüz yüklü değil",
            }
    return {
        "ready": True,
        "profile": profile.id,
        "provider": profile.provider,
        "model": profile.model_name,
        "local": profile.local,
        "message": "Yerel model" if profile.local else "Cloud model; allowlist proxy üzerinden",
    }


@app.post("/api/auth/bootstrap", response_model=UserView, status_code=201)
def auth_bootstrap(
    payload: BootstrapRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserView:
    user = bootstrap_admin(payload, db, settings)
    request.session["user_id"] = user.id
    return UserView.from_row(user)


@app.post("/api/auth/login", response_model=UserView)
def auth_login(
    payload: LoginRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> UserView:
    user = authenticate(payload, db)
    request.session["user_id"] = user.id
    return UserView.from_row(user)


@app.post("/api/auth/logout", status_code=204)
def auth_logout(request: Request) -> Response:
    request.session.clear()
    return Response(status_code=204)


@app.get("/api/setup/status")
def setup_status() -> dict[str, Any]:
    return {
        "steps": [
            "Bootstrap ve ilk admin",
            "Roller",
            "Yerel model testi",
            "Şirket hedefi",
            "Demo veya dosya kaynakları",
            "Mapping ve önizleme",
            "OKF bundle",
            "Growth Diagnostic",
            "Taslak rapor",
            "OKF diff ve onay",
        ],
        "demo_available": True,
        "cloud_models_enabled": settings.cloud_models_enabled,
    }


@app.post("/api/setup/demo")
def setup_demo(settings: Annotated[Settings, Depends(get_settings)]) -> dict[str, Any]:
    bundle = compile_demo_bundle(settings.company_bundle)
    dataset = build_demo_dataset()
    snapshot = RawVault(settings.knowledge_root / "raw").store(
        "src-demo-company",
        "dataset.json",
        json.dumps(dataset, ensure_ascii=False, sort_keys=True).encode("utf-8"),
        "demo-company",
    )
    report = bundle.validate()
    return {
        "company": "Anka Endüstriyel Otomasyon",
        "counts": demo_counts(dataset).model_dump(),
        "bundle": str(bundle.root),
        "okf_valid": report.valid,
        "warnings": len(report.warnings),
        "raw_snapshot_sha256": snapshot.sha256,
    }


@app.get("/api/dashboard", response_model=GrowthDiagnostic)
def dashboard() -> GrowthDiagnostic:
    return build_growth_diagnostic()


@app.post("/api/diagnostics/run", response_model=GrowthDiagnostic)
def run_diagnostic() -> GrowthDiagnostic:
    # The current vertical slice is deterministic; DBOS/Pydantic AI are plugged in by Phase 3/4.
    return build_growth_diagnostic()


@app.get("/api/okf/validate")
def validate_okf(settings: Annotated[Settings, Depends(get_settings)]) -> dict[str, Any]:
    return FileSystemOKFBundle(settings.company_bundle).validate().model_dump()


@app.get("/api/okf/export")
def export_okf(settings: Annotated[Settings, Depends(get_settings)]) -> Response:
    payload = FileSystemOKFBundle(settings.company_bundle).export_zip()
    return Response(
        payload,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="company-okf-0.1.zip"'},
    )


@app.get("/api/okf/diff")
def okf_diff(settings: Annotated[Settings, Depends(get_settings)]) -> dict[str, str]:
    repository = GitKnowledgeRepository(settings.company_bundle)
    return {"diff": repository.diff()}


@app.post("/api/okf/approve")
def approve_okf_diff(
    settings: Annotated[Settings, Depends(get_settings)],
    _: Annotated[Any, Depends(require_role("approver"))],
    message: Annotated[str, Query(min_length=8, max_length=180)] = "Approve OKF candidate",
) -> dict[str, str]:
    repository = GitKnowledgeRepository(settings.company_bundle)
    try:
        revision = repository.commit_approved(message)
    except Exception as error:
        raise HTTPException(status_code=409, detail="Onaylanacak OKF değişikliği yok") from error
    return {"status": "approved", "revision": revision}


@app.get("/api/knowledge")
async def knowledge_list(
    settings: Annotated[Settings, Depends(get_settings)],
    query: str = Query(default="", max_length=500),
) -> dict[str, Any]:
    bundle = FileSystemOKFBundle(settings.company_bundle)
    if query:
        hits = await KnowledgeSearch(bundle, settings.qmd_url).search(query)
        return {"query": query, "items": [hit.__dict__ for hit in hits]}
    backlinks = bundle.backlinks()
    return {
        "items": [
            {
                "path": item.path,
                "concept_id": item.concept_id,
                "title": item.title,
                "type": item.type or "Reserved",
                "backlinks": len(backlinks.get(item.path, [])),
            }
            for item in bundle.list_concepts()
        ]
    }


@app.get("/api/knowledge/{concept_path:path}")
def knowledge_concept(
    concept_path: str,
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, Any]:
    try:
        concept = FileSystemOKFBundle(settings.company_bundle).read(concept_path)
    except (FileNotFoundError, ValueError) as error:
        raise HTTPException(status_code=404, detail="Concept bulunamadı") from error
    return {
        **concept.model_dump(),
        "links": FileSystemOKFBundle.links(concept),
        "backlinks": FileSystemOKFBundle(settings.company_bundle).backlinks().get(concept.path, []),
    }


@app.get("/api/evidence/{evidence_id}")
def evidence(evidence_id: str) -> dict[str, Any]:
    for opportunity in build_growth_diagnostic().opportunities:
        for item in opportunity.evidence:
            if item.id == evidence_id:
                return item.model_dump()
    raise HTTPException(status_code=404, detail="Evidence bulunamadı")


@app.get("/api/agents")
def agents() -> list[dict[str, Any]]:
    return [spec.model_dump(exclude={"system_prompt"}) for spec in AgentRegistry().list()]


@app.get("/api/workflows/default", response_model=WorkflowDefinition)
def default_workflow() -> WorkflowDefinition:
    return build_default_workflow()


@app.post("/api/workflows/validate", response_model=WorkflowValidation)
def workflow_validate(workflow: WorkflowDefinition) -> WorkflowValidation:
    return validate_workflow(workflow)


@app.post("/api/workflows/dry-run")
def workflow_dry_run(workflow: WorkflowDefinition) -> dict[str, Any]:
    return run_workflow_locally(workflow)


@app.post("/api/workflows/run", status_code=202)
def workflow_run(
    workflow: WorkflowDefinition,
    settings: Annotated[Settings, Depends(get_settings)],
    idempotency_key: Annotated[str, Query(min_length=8, max_length=180)],
) -> dict[str, Any]:
    validation = validate_workflow(workflow)
    if not validation.valid:
        raise HTTPException(
            status_code=422, detail=[item.model_dump() for item in validation.issues]
        )
    if not settings.enable_dbos:
        return {
            "workflow_id": idempotency_key,
            "status": "dry-run",
            "result": run_workflow_locally(workflow),
        }
    with SetWorkflowID(idempotency_key):
        handle = DBOS.start_workflow(
            durable_workflow_interpreter,
            workflow.model_dump(mode="json"),
            {"dry_run": False},
        )
    return {"workflow_id": handle.get_workflow_id(), "status": "started"}


@app.post("/api/workflows/{workflow_id}/approval", status_code=202)
def workflow_approval(
    workflow_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
    decision: Annotated[str, Query(pattern="^(approved|rejected)$")],
    node_id: Annotated[str, Query(min_length=2, max_length=64)] = "approval",
) -> dict[str, str]:
    if not settings.enable_dbos:
        raise HTTPException(status_code=409, detail="DBOS runtime bu profilde kapalı")
    DBOS.send(
        workflow_id,
        {"decision": decision, "actor_role": "approver"},
        topic=f"approval:{node_id}",
        idempotency_key=f"{workflow_id}:{node_id}:{decision}",
    )
    return {"workflow_id": workflow_id, "decision": decision}


static_dir = Path(settings.static_dir)
if static_dir.exists():
    assets = static_dir / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str) -> FileResponse:
        candidate = (static_dir / path).resolve()
        if candidate.is_relative_to(static_dir.resolve()) and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(static_dir / "index.html")
