from __future__ import annotations

import asyncio
import hashlib
import uuid
from contextlib import asynccontextmanager, suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any

import httpx
from dbos import DBOS, DBOSConfig
from fastapi import (
    Depends,
    FastAPI,
    File,
    Header,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
)
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from agi_server import __version__
from agi_server.agents.model_gateway import resolve_model_profile
from agi_server.agents.probe import probe_model_profile
from agi_server.agents.registry import ManagedAgentSpec
from agi_server.config import Settings, get_settings
from agi_server.connectors.files import MAX_FILE_BYTES, ReadOnlyTabularConnector
from agi_server.db import (
    AgentDefinitionRow,
    ApprovalRequest,
    Artifact,
    CapabilityDefinitionRow,
    DataSource,
    InstallationState,
    OKFCandidate,
    SourceMapping,
    SourceSyncRun,
    User,
    WorkflowDefinitionRow,
    WorkflowRun,
    WorkflowSchedule,
    WorkflowStepRun,
    engine,
    get_db,
)
from agi_server.diagnostics import run_growth_diagnostic
from agi_server.domain.demo import build_demo_dataset, demo_counts
from agi_server.domain.diagnostic import build_growth_diagnostic
from agi_server.http_security import RequestSecurityMiddleware
from agi_server.ingestion import (
    list_sources,
    resolve_evidence_excerpt,
    sync_connector,
    sync_demo_company,
)
from agi_server.migrations import run_migrations
from agi_server.observability import ObservabilityMiddleware, configure_observability
from agi_server.okf import FileSystemOKFBundle
from agi_server.okf.git_repo import GitKnowledgeRepository
from agi_server.okf.lifecycle import (
    approve_candidate,
    create_demo_candidate,
    create_import_candidate,
    ensure_active_repository,
    reject_candidate,
    request_qmd_reindex,
)
from agi_server.okf.search import KnowledgeSearch
from agi_server.schemas import (
    GrowthDiagnostic,
    HealthResponse,
    SetupProgressUpdate,
    SourceMappingRequest,
)
from agi_server.security import (
    AuthSessionView,
    BootstrapRequest,
    LoginRequest,
    UserCreateRequest,
    UserRolesRequest,
    UserView,
    authenticate,
    bootstrap_admin,
    create_user,
    current_user,
    record_audit,
    require_role,
    start_session,
)
from agi_server.workflow import build_default_workflow, validate_workflow
from agi_server.workflow.models import WorkflowDefinition, WorkflowValidation
from agi_server.workflow.persistent_runtime import (
    decide_persisted_approval,
    expire_approval_state,
    start_persisted_workflow,
)
from agi_server.workflow.registry_service import (
    agent_from_row,
    clone_agent_version,
    clone_workflow_version,
    create_schedule,
    ensure_platform_registry,
    latest_workflow,
    publish_agent,
    publish_workflow,
    save_agent_draft,
    save_workflow_draft,
    workflow_from_row,
)
from agi_server.workflow.runtime import run_workflow_locally
from agi_server.workflow.scheduler import scheduler_loop


@asynccontextmanager
async def lifespan(_: FastAPI):
    run_migrations()
    settings = get_settings()
    ensure_active_repository(settings.company_bundle)
    with Session(engine) as db:
        ensure_platform_registry(db)
    schedule_task = asyncio.create_task(scheduler_loop(settings))
    if settings.enable_dbos:
        DBOS.launch()
    yield
    schedule_task.cancel()
    with suppress(asyncio.CancelledError):
        await schedule_task
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
configure_observability(settings.otlp_endpoint)
app.add_middleware(ObservabilityMiddleware)
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
app.add_middleware(RequestSecurityMiddleware)
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
    allow_headers=["Content-Type", "X-CSRF-Token", "Idempotency-Key"],
)


def api_error(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    details: Any = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    response_headers = {"X-Request-ID": request_id, **(headers or {})}
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(
            {
                "error": {
                    "code": code,
                    "message": message,
                    "details": details,
                    "request_id": request_id,
                }
            }
        ),
        headers=response_headers,
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, error: HTTPException) -> JSONResponse:
    message = error.detail if isinstance(error.detail, str) else "İstek tamamlanamadı"
    details = None if isinstance(error.detail, str) else error.detail
    return api_error(
        request,
        status_code=error.status_code,
        code=f"http.{error.status_code}",
        message=message,
        details=details,
        headers=error.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, error: RequestValidationError
) -> JSONResponse:
    return api_error(
        request,
        status_code=422,
        code="request.validation_failed",
        message="İstek doğrulanamadı",
        details=error.errors(),
    )


@app.get("/api/health", response_model=HealthResponse)
async def health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    components = {"api": "ok", "postgres": "unavailable", "okf": "ok"}
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        components["postgres"] = "ok"
    except Exception:
        components["postgres"] = "unavailable"
    try:
        async with httpx.AsyncClient(timeout=1) as client:
            response = await client.get(settings.ollama_base_url.removesuffix("/v1") + "/api/tags")
            response.raise_for_status()
        components["ollama"] = "ok"
    except httpx.HTTPError:
        components["ollama"] = "unavailable"
    if settings.qmd_url:
        try:
            async with httpx.AsyncClient(timeout=1) as client:
                response = await client.get(settings.qmd_url.rstrip("/") + "/health")
                response.raise_for_status()
            components["qmd"] = "ok"
        except httpx.HTTPError:
            components["qmd"] = "unavailable; lexical fallback active"
    else:
        components["qmd"] = "disabled; lexical fallback active"
    status_value = "ok" if components["postgres"] == "ok" else "degraded"
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


@app.post("/api/models/probe")
async def model_probe(
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User | None, Depends(require_role("admin"))],
    profile: Annotated[str | None, Query(max_length=80)] = None,
) -> dict[str, Any]:
    profile_id = profile or settings.model_profile
    actor_id = None if actor is None else actor.id
    try:
        result = await probe_model_profile(settings, profile_id)
    except Exception as error:
        record_audit(
            db,
            actor_id=actor_id,
            action="model.probe_failed",
            target_type="model_profile",
            target_id=profile_id,
            metadata={"error_type": type(error).__name__},
        )
        db.commit()
        raise HTTPException(
            status_code=409,
            detail="Model structured-output probe tamamlanamadı",
        ) from error
    record_audit(
        db,
        actor_id=actor_id,
        action="model.probe_succeeded",
        target_type="model_profile",
        target_id=profile_id,
        metadata={
            "provider": result["provider"],
            "model": result["model"],
            "usage": result["usage"],
        },
    )
    db.commit()
    return result


@app.post("/api/auth/bootstrap", response_model=AuthSessionView, status_code=201)
def auth_bootstrap(
    payload: BootstrapRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthSessionView:
    user = bootstrap_admin(payload, db, settings)
    return start_session(request, user)


@app.post("/api/auth/login", response_model=AuthSessionView)
def auth_login(
    payload: LoginRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> AuthSessionView:
    user = authenticate(payload, db)
    record_audit(
        db,
        actor_id=user.id,
        action="auth.login",
        target_type="session",
        target_id=user.id,
    )
    db.commit()
    return start_session(request, user)


@app.get("/api/auth/me", response_model=AuthSessionView)
def auth_me(
    request: Request,
    user: Annotated[User | None, Depends(current_user)],
) -> AuthSessionView:
    return AuthSessionView(
        user=None if user is None else UserView.from_row(user),
        csrf_token=request.session.get("csrf_token"),
    )


@app.post("/api/auth/logout", status_code=204)
def auth_logout(
    request: Request,
    user: Annotated[User | None, Depends(current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    record_audit(
        db,
        actor_id=None if user is None else user.id,
        action="auth.logout",
        target_type="session",
        target_id=None if user is None else user.id,
    )
    db.commit()
    request.session.clear()
    return Response(status_code=204)


@app.get("/api/users")
def user_list(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User | None, Depends(require_role("admin"))],
) -> dict[str, Any]:
    rows = db.query(User).order_by(User.created_at).all()
    return {
        "items": [
            {
                **UserView.from_row(row).model_dump(),
                "active": row.active,
                "created_at": row.created_at,
            }
            for row in rows
        ]
    }


@app.post("/api/users", response_model=UserView, status_code=201)
def user_create(
    payload: UserCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User | None, Depends(require_role("admin"))],
) -> UserView:
    user = create_user(payload, db)
    record_audit(
        db,
        actor_id=None if actor is None else actor.id,
        action="user.created",
        target_type="user",
        target_id=user.id,
        metadata={"roles": user.roles},
    )
    db.commit()
    return UserView.from_row(user)


@app.put("/api/users/{user_id}/roles", response_model=UserView)
def user_roles_update(
    user_id: str,
    payload: UserRolesRequest,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User | None, Depends(require_role("admin"))],
) -> UserView:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    removing_admin = "admin" in user.roles and ("admin" not in payload.roles or not payload.active)
    if removing_admin:
        active_admins = [
            row
            for row in db.query(User).filter(User.active.is_(True)).all()
            if "admin" in row.roles
        ]
        if len(active_admins) <= 1:
            raise HTTPException(status_code=409, detail="Son aktif admin kaldırılamaz")
    user.roles = sorted(set(payload.roles))
    user.active = payload.active
    record_audit(
        db,
        actor_id=None if actor is None else actor.id,
        action="user.roles_updated",
        target_type="user",
        target_id=user.id,
        metadata={"roles": user.roles, "active": user.active},
    )
    db.commit()
    return UserView.from_row(user)


@app.get("/api/setup/status")
def setup_status(
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, Any]:
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
        "bootstrap_required": db.scalar(select(func.count()).select_from(User)) == 0,
        "auth_enabled": not settings.demo_no_auth,
        "cloud_models_enabled": settings.cloud_models_enabled,
    }


@app.get("/api/setup/progress")
def setup_progress(db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    row = db.get(InstallationState, "default")
    if row is None:
        return {
            "current_step": 0,
            "completed_steps": [],
            "configuration": {},
            "status": "in_progress",
            "updated_at": None,
        }
    return {
        "current_step": row.current_step,
        "completed_steps": row.completed_steps,
        "configuration": row.configuration,
        "status": row.status,
        "updated_at": row.updated_at,
    }


@app.put("/api/setup/progress")
def setup_progress_update(
    payload: SetupProgressUpdate,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User | None, Depends(require_role("admin"))],
) -> dict[str, Any]:
    allowed_keys = {"company_name", "objective", "model_profile", "source_mode", "locale"}
    unknown = sorted(set(payload.configuration) - allowed_keys)
    if unknown:
        raise HTTPException(
            status_code=422,
            detail={"unsupported_configuration_keys": unknown},
        )
    completed = sorted(set(payload.completed_steps))
    if payload.status == "completed" and completed != list(range(10)):
        raise HTTPException(status_code=409, detail="Tüm kurulum adımları tamamlanmalıdır")
    row = db.get(InstallationState, "default")
    if row is None:
        row = InstallationState(id="default")
        db.add(row)
    row.current_step = payload.current_step
    row.completed_steps = completed
    row.configuration = payload.configuration
    row.status = payload.status
    row.updated_by = None if actor is None else actor.id
    record_audit(
        db,
        actor_id=None if actor is None else actor.id,
        action="setup.progress_updated",
        target_type="installation",
        target_id="default",
        metadata={
            "current_step": payload.current_step,
            "completed_steps": completed,
            "status": payload.status,
        },
    )
    db.commit()
    return {
        "current_step": row.current_step,
        "completed_steps": row.completed_steps,
        "configuration": row.configuration,
        "status": row.status,
        "updated_at": row.updated_at,
    }


@app.post("/api/setup/demo")
def setup_demo(
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User | None, Depends(require_role("admin"))],
) -> dict[str, Any]:
    ingestion = sync_demo_company(db, settings.raw_root)
    dataset = build_demo_dataset()
    candidate, diff = create_demo_candidate(
        db,
        settings.company_bundle,
        settings.candidates_root,
        None if actor is None else actor.id,
    )
    record_audit(
        db,
        actor_id=None if actor is None else actor.id,
        action="setup.demo_candidate_created",
        target_type="okf_candidate",
        target_id=candidate.id,
        metadata={
            "sources": [item.source_id for item in ingestion.sources],
            "records": ingestion.total_records,
        },
    )
    db.commit()
    return {
        "company": "Anka Endüstriyel Otomasyon",
        "counts": demo_counts(dataset).model_dump(),
        "active_bundle": str(settings.company_bundle),
        "candidate_id": candidate.id,
        "candidate_status": candidate.status,
        "okf_valid": not candidate.validation_report.get("errors"),
        "warnings": len(candidate.validation_report.get("warnings", [])),
        "sources": [item.model_dump(mode="json") for item in ingestion.sources],
        "records_persisted": ingestion.total_records,
        "diff": diff,
    }


@app.get("/api/dashboard", response_model=GrowthDiagnostic)
def dashboard(db: Annotated[Session, Depends(get_db)]) -> GrowthDiagnostic:
    latest = db.scalar(
        select(WorkflowRun)
        .where(
            WorkflowRun.workflow_id == "builtin-growth-diagnostic",
            WorkflowRun.status.in_(["awaiting_approval", "completed"]),
        )
        .order_by(WorkflowRun.started_at.desc())
    )
    if latest and latest.output_json and latest.output_json.get("diagnostic"):
        diagnostic = GrowthDiagnostic.model_validate(latest.output_json["diagnostic"])
    else:
        diagnostic = build_growth_diagnostic(db)
    open_approvals = db.scalar(
        select(func.count()).select_from(OKFCandidate).where(OKFCandidate.status == "pending")
    )
    return diagnostic.model_copy(update={"open_approvals": int(open_approvals or 0)})


@app.post("/api/diagnostics/run", response_model=GrowthDiagnostic)
async def run_diagnostic(
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User | None, Depends(require_role("analyst"))],
    settings: Annotated[Settings, Depends(get_settings)],
    idempotency_key: Annotated[
        str | None, Header(alias="Idempotency-Key", min_length=8, max_length=180)
    ] = None,
) -> GrowthDiagnostic:
    actor_id = None if actor is None else actor.id
    key = idempotency_key or f"diagnostic-{uuid.uuid4()}"
    try:
        result = await run_growth_diagnostic(
            db,
            settings,
            actor_id=actor_id,
            idempotency_key=key,
        )
    except Exception as error:
        record_audit(
            db,
            actor_id=actor_id,
            action="diagnostic.run_failed",
            target_type="workflow_run",
            target_id=key,
            metadata={"error_type": type(error).__name__},
        )
        db.commit()
        raise HTTPException(
            status_code=409,
            detail=(
                "Model destekli Growth Diagnostic tamamlanamadı; "
                "model ve veri hazırlığını kontrol edin"
            ),
        ) from error
    record_audit(
        db,
        actor_id=actor_id,
        action="diagnostic.run_completed",
        target_type="workflow_run",
        target_id=result.run.id,
        metadata={
            "candidate_id": result.candidate.id,
            "model_profile": result.run.model_profile,
            "token_usage": result.run.token_usage,
        },
    )
    db.commit()
    return result.diagnostic


@app.get("/api/runs")
def workflow_runs(db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    rows = db.query(WorkflowRun).order_by(WorkflowRun.started_at.desc()).limit(100).all()
    return {
        "items": [
            {
                "id": row.id,
                "workflow_id": row.workflow_id,
                "workflow_version": row.workflow_version,
                "status": row.status,
                "current_step": row.current_step,
                "model_profile": row.model_profile,
                "token_usage": row.token_usage,
                "started_at": row.started_at,
                "completed_at": row.completed_at,
            }
            for row in rows
        ]
    }


@app.get("/api/runs/{run_id}")
def workflow_run_detail(
    run_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    run = db.get(WorkflowRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Workflow run bulunamadı")
    steps = (
        db.query(WorkflowStepRun)
        .filter(WorkflowStepRun.run_id == run_id)
        .order_by(WorkflowStepRun.sequence)
        .all()
    )
    artifacts = (
        db.query(Artifact).filter(Artifact.run_id == run_id).order_by(Artifact.created_at).all()
    )
    return {
        "id": run.id,
        "idempotency_key": run.idempotency_key,
        "workflow_id": run.workflow_id,
        "workflow_version": run.workflow_version,
        "status": run.status,
        "current_step": run.current_step,
        "model_profile": run.model_profile,
        "agent_versions": run.agent_versions,
        "token_usage": run.token_usage,
        "evidence_ids": run.evidence_ids,
        "output": run.output_json,
        "error": run.error_json,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
        "steps": [
            {
                "id": step.id,
                "step_id": step.step_id,
                "sequence": step.sequence,
                "kind": step.kind,
                "agent_id": step.agent_id,
                "agent_version": step.agent_version,
                "model_profile": step.model_profile,
                "model_provider": step.model_provider,
                "model_name": step.model_name,
                "data_classification": step.data_classification,
                "redaction_applied": step.redaction_applied,
                "status": step.status,
                "input_hash": step.input_hash,
                "output": step.output_json,
                "error": step.error_json,
                "token_usage": step.token_usage,
                "started_at": step.started_at,
                "completed_at": step.completed_at,
            }
            for step in steps
        ],
        "artifacts": [
            {
                "id": artifact.id,
                "kind": artifact.kind,
                "sha256": artifact.sha256,
                "download_url": f"/api/runs/{run_id}/artifacts/{artifact.id}",
                "created_at": artifact.created_at,
            }
            for artifact in artifacts
        ],
    }


@app.get("/api/runs/{run_id}/artifacts/{artifact_id}")
def workflow_run_artifact(
    run_id: str,
    artifact_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db)],
) -> FileResponse:
    artifact = db.get(Artifact, artifact_id)
    if artifact is None or artifact.run_id != run_id:
        raise HTTPException(status_code=404, detail="Artifact bulunamadı")
    path = (settings.knowledge_root / artifact.uri).resolve()
    artifact_root = (settings.knowledge_root / "artifacts").resolve()
    if not path.is_relative_to(artifact_root) or not path.is_file():
        raise HTTPException(status_code=409, detail="Artifact dosyası doğrulanamadı")
    expected = artifact.sha256
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise HTTPException(status_code=409, detail="Artifact bütünlük kontrolü başarısız")
    return FileResponse(path, filename=path.name)


@app.post("/api/runs/{run_id}/cancel")
def workflow_run_cancel(
    run_id: str,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User | None, Depends(require_role("analyst"))],
    reason: Annotated[str, Query(min_length=8, max_length=500)],
) -> dict[str, str]:
    run = db.get(WorkflowRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Workflow run bulunamadı")
    if run.status not in {"running", "awaiting_approval"}:
        raise HTTPException(status_code=409, detail="Bu run iptal edilebilir durumda değil")
    approvals = (
        db.query(ApprovalRequest)
        .filter(ApprovalRequest.run_id == run_id, ApprovalRequest.status == "pending")
        .all()
    )
    for approval in approvals:
        approval.status = "cancelled"
        approval.decision_reason = reason
        approval.decided_at = datetime.now(UTC)
        candidate = db.get(OKFCandidate, approval.candidate_id) if approval.candidate_id else None
        if candidate is not None and candidate.status == "pending":
            candidate.status = "rejected"
            candidate.decision_reason = reason
            candidate.decided_at = datetime.now(UTC)
    run.status = "cancelled"
    run.completed_at = datetime.now(UTC)
    record_audit(
        db,
        actor_id=None if actor is None else actor.id,
        action="workflow.run_cancelled",
        target_type="workflow_run",
        target_id=run_id,
        metadata={"reason": reason},
    )
    db.commit()
    return {"run_id": run_id, "status": run.status}


@app.post("/api/runs/{run_id}/retry", status_code=202)
async def workflow_run_retry(
    run_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User | None, Depends(require_role("analyst"))],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=180)],
) -> dict[str, Any]:
    previous = db.get(WorkflowRun, run_id)
    if previous is None:
        raise HTTPException(status_code=404, detail="Workflow run bulunamadı")
    if previous.status not in {"failed", "cancelled", "rejected", "expired"}:
        raise HTTPException(
            status_code=409, detail="Yalnız terminal başarısız run yeniden denenebilir"
        )
    if previous.workflow_id == "builtin-growth-diagnostic":
        try:
            result = await run_growth_diagnostic(
                db,
                settings,
                actor_id=None if actor is None else actor.id,
                idempotency_key=idempotency_key,
            )
            run = result.run
        except Exception as error:
            raise HTTPException(status_code=409, detail="Diagnostic retry tamamlanamadı") from error
    else:
        row = db.get(
            WorkflowDefinitionRow,
            (previous.workflow_id, previous.workflow_version),
        )
        if row is None:
            raise HTTPException(status_code=409, detail="Pinned workflow version bulunamadı")
        try:
            run = await start_persisted_workflow(
                db,
                settings,
                row,
                idempotency_key,
                None if actor is None else actor.id,
                input_json={"retry_of": run_id},
            )
        except Exception as error:
            raise HTTPException(status_code=409, detail="Workflow retry tamamlanamadı") from error
    record_audit(
        db,
        actor_id=None if actor is None else actor.id,
        action="workflow.run_retried",
        target_type="workflow_run",
        target_id=run.id,
        metadata={"retry_of": run_id},
    )
    db.commit()
    return {"run_id": run.id, "status": run.status, "retry_of": run_id}


@app.get("/api/sources")
def sources_list(db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    return {
        "items": [
            {
                "id": source.id,
                "name": source.name,
                "connector_type": source.connector_type,
                "read_only": source.read_only,
                "status": source.status,
                "updated_at": source.updated_at,
            }
            for source in list_sources(db)
        ]
    }


@app.get("/api/sources/sync-runs")
def source_sync_runs(db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    rows = db.query(SourceSyncRun).order_by(SourceSyncRun.started_at.desc()).limit(100).all()
    return {
        "items": [
            {
                "id": row.id,
                "source_id": row.source_id,
                "status": row.status,
                "records_seen": row.records_seen,
                "records_persisted": row.records_persisted,
                "warnings": row.warnings,
                "started_at": row.started_at,
                "completed_at": row.completed_at,
            }
            for row in rows
        ]
    }


@app.post("/api/sources/demo/sync")
def source_demo_sync(
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User | None, Depends(require_role("admin"))],
) -> dict[str, Any]:
    summary = sync_demo_company(db, settings.raw_root)
    record_audit(
        db,
        actor_id=None if actor is None else actor.id,
        action="source.demo_synced",
        target_type="data_source",
        target_id="src-demo-company",
        metadata={"records": summary.total_records},
    )
    db.commit()
    return summary.model_dump(mode="json")


@app.post("/api/sources/files/preview", status_code=201)
async def source_file_preview(
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User | None, Depends(require_role("admin"))],
    file: Annotated[UploadFile, File(...)],
    entity_type: Annotated[
        str, Query(min_length=2, max_length=60, pattern=r"^[a-z][a-z0-9_]*$")
    ] = "accounts",
) -> dict[str, Any]:
    original_name = Path(file.filename or "").name
    suffix = Path(original_name).suffix.lower()
    if suffix not in {".csv", ".xlsx"}:
        raise HTTPException(status_code=422, detail="Yalnız CSV/XLSX destekleniyor")
    source_id = f"src-file-{uuid.uuid4()}"
    settings.uploads_root.mkdir(parents=True, exist_ok=True)
    upload_path = (settings.uploads_root / f"{source_id}{suffix}").resolve()
    if not upload_path.is_relative_to(settings.uploads_root.resolve()):
        raise HTTPException(status_code=400, detail="Geçersiz dosya yolu")
    written = 0
    try:
        with upload_path.open("xb") as handle:
            while chunk := await file.read(1024 * 1024):
                written += len(chunk)
                if written > MAX_FILE_BYTES:
                    raise HTTPException(status_code=413, detail="Dosya 25 MB sınırını aşıyor")
                handle.write(chunk)
        connector = ReadOnlyTabularConnector(upload_path, source_id, entity_type)
        health = connector.test_connection()
        if not health.ok:
            raise HTTPException(status_code=422, detail=health.message)
        schema = connector.discover_schema()
        preview, warnings = connector.preview_with_warnings()
    except Exception:
        upload_path.unlink(missing_ok=True)
        raise
    finally:
        await file.close()

    source = DataSource(
        id=source_id,
        name=original_name,
        connector_type="tabular-file",
        configuration={
            "upload_path": str(upload_path.relative_to(settings.knowledge_root.resolve())),
            "original_filename": original_name,
            "entity_type": entity_type,
            "classification": "internal",
        },
        read_only=True,
        status="previewed",
    )
    db.add(source)
    record_audit(
        db,
        actor_id=None if actor is None else actor.id,
        action="source.file_previewed",
        target_type="data_source",
        target_id=source_id,
        metadata={"filename": original_name, "bytes": written},
    )
    db.commit()
    return {
        "source_id": source_id,
        "filename": original_name,
        "bytes": written,
        "schema": schema.model_dump(mode="json"),
        "preview": [item.model_dump(mode="json") for item in preview],
        "warnings": warnings,
    }


@app.post("/api/sources/{source_id}/mapping", status_code=201)
def source_mapping_create(
    source_id: str,
    payload: SourceMappingRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User | None, Depends(require_role("admin"))],
) -> dict[str, Any]:
    source = db.get(DataSource, source_id)
    if source is None or source.connector_type != "tabular-file":
        raise HTTPException(status_code=404, detail="Dosya kaynağı bulunamadı")
    if "id" not in payload.field_mapping:
        raise HTTPException(status_code=422, detail="Mapping canonical 'id' alanını içermelidir")
    upload_path = (settings.knowledge_root / source.configuration["upload_path"]).resolve()
    connector = ReadOnlyTabularConnector(upload_path, source_id, payload.entity_type)
    available = set(connector.discover_schema().entities[payload.entity_type])
    unknown = sorted(set(payload.field_mapping.values()) - available)
    if unknown:
        raise HTTPException(status_code=422, detail={"unknown_source_fields": unknown})
    latest = (
        db.query(SourceMapping)
        .filter(SourceMapping.source_id == source_id)
        .order_by(SourceMapping.version.desc())
        .first()
    )
    version = 1 if latest is None else latest.version + 1
    mapping = SourceMapping(
        source_id=source_id,
        version=version,
        entity_type=payload.entity_type,
        field_mapping=payload.field_mapping,
        validation={"classification": payload.classification, "required": ["id"]},
        created_by=None if actor is None else actor.id,
    )
    db.add(mapping)
    source.configuration = {
        **source.configuration,
        "entity_type": payload.entity_type,
        "classification": payload.classification,
    }
    source.status = "mapped"
    record_audit(
        db,
        actor_id=None if actor is None else actor.id,
        action="source.mapping_created",
        target_type="source_mapping",
        target_id=f"{source_id}:{version}",
        metadata={"entity_type": payload.entity_type, "fields": sorted(payload.field_mapping)},
    )
    db.commit()
    return {
        "source_id": source_id,
        "version": version,
        "entity_type": payload.entity_type,
        "field_mapping": payload.field_mapping,
        "classification": payload.classification,
    }


@app.post("/api/sources/{source_id}/sync")
def source_file_sync(
    source_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User | None, Depends(require_role("admin"))],
) -> dict[str, Any]:
    source = db.get(DataSource, source_id)
    if source is None or source.connector_type != "tabular-file":
        raise HTTPException(status_code=404, detail="Dosya kaynağı bulunamadı")
    mapping = (
        db.query(SourceMapping)
        .filter(SourceMapping.source_id == source_id)
        .order_by(SourceMapping.version.desc())
        .first()
    )
    if mapping is None:
        raise HTTPException(status_code=409, detail="Kaynak sync öncesinde map edilmelidir")
    upload_path = (settings.knowledge_root / source.configuration["upload_path"]).resolve()
    if not upload_path.is_relative_to(settings.uploads_root.resolve()):
        raise HTTPException(status_code=409, detail="Kaynak dosya yolu geçersiz")
    connector = ReadOnlyTabularConnector(
        upload_path,
        source_id,
        mapping.entity_type,
        field_mapping=mapping.field_mapping,
    )
    summary = sync_connector(db, connector, settings.raw_root)
    record_audit(
        db,
        actor_id=None if actor is None else actor.id,
        action="source.file_synced",
        target_type="data_source",
        target_id=source_id,
        metadata={"records": summary.total_records, "mapping_version": mapping.version},
    )
    db.commit()
    return summary.model_dump(mode="json")


@app.get("/api/okf/validate")
def validate_okf(settings: Annotated[Settings, Depends(get_settings)]) -> dict[str, Any]:
    return FileSystemOKFBundle(settings.company_bundle).validate().model_dump()


@app.get("/api/okf/export")
def export_okf(
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User | None, Depends(require_role("analyst"))],
) -> Response:
    payload = FileSystemOKFBundle(settings.company_bundle).export_zip()
    record_audit(
        db,
        actor_id=None if actor is None else actor.id,
        action="okf.exported",
        target_type="okf_revision",
        target_id=GitKnowledgeRepository(settings.company_bundle).ensure_baseline(),
        metadata={"bytes": len(payload)},
    )
    db.commit()
    return Response(
        payload,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="company-okf-0.1.zip"'},
    )


@app.post("/api/okf/import", status_code=201)
async def import_okf(
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User | None, Depends(require_role("admin"))],
    file: Annotated[UploadFile, File(...)],
) -> dict[str, Any]:
    payload = await file.read(50_000_001)
    await file.close()
    if len(payload) > 50_000_000:
        raise HTTPException(status_code=413, detail="OKF archive 50 MB sınırını aşıyor")
    try:
        candidate, diff = create_import_candidate(
            db,
            settings.company_bundle,
            settings.candidates_root,
            None if actor is None else actor.id,
            payload,
        )
    except (ValueError, OSError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    record_audit(
        db,
        actor_id=None if actor is None else actor.id,
        action="okf.import_candidate_created",
        target_type="okf_candidate",
        target_id=candidate.id,
        metadata={"archive_bytes": len(payload)},
    )
    db.commit()
    return {
        "candidate_id": candidate.id,
        "status": candidate.status,
        "validation_report": candidate.validation_report,
        "diff": diff,
    }


@app.get("/api/okf/candidates")
def okf_candidates(db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    rows = db.query(OKFCandidate).order_by(OKFCandidate.created_at.desc()).limit(100).all()
    return {
        "items": [
            {
                "id": row.id,
                "run_id": row.run_id,
                "status": row.status,
                "base_revision": row.base_revision,
                "candidate_revision": row.candidate_revision,
                "validation_report": row.validation_report,
                "created_by": row.created_by,
                "created_at": row.created_at,
                "expires_at": row.expires_at,
                "decided_by": row.decided_by,
                "decided_at": row.decided_at,
                "decision_reason": row.decision_reason,
            }
            for row in rows
        ]
    }


@app.get("/api/okf/candidates/{candidate_id}/diff")
def okf_candidate_diff(
    candidate_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    row = db.get(OKFCandidate, candidate_id)
    if row is None or not row.candidate_revision:
        raise HTTPException(status_code=404, detail="OKF candidate bulunamadı")
    repository = GitKnowledgeRepository(settings.company_bundle)
    return {
        "candidate_id": candidate_id,
        "status": row.status,
        "diff": repository.candidate_diff(row.base_revision, row.candidate_revision),
    }


@app.get("/api/okf/diff")
def okf_diff(
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    row = (
        db.query(OKFCandidate)
        .filter(OKFCandidate.status == "pending")
        .order_by(OKFCandidate.created_at.desc())
        .first()
    )
    if row is None or not row.candidate_revision:
        return {"candidate_id": "", "status": "none", "diff": ""}
    return {
        "candidate_id": row.id,
        "status": row.status,
        "diff": GitKnowledgeRepository(settings.company_bundle).candidate_diff(
            row.base_revision, row.candidate_revision
        ),
    }


@app.post("/api/okf/candidates/{candidate_id}/decision")
async def decide_okf_candidate(
    candidate_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
    actor: Annotated[User | None, Depends(require_role("approver"))],
    db: Annotated[Session, Depends(get_db)],
    decision: Annotated[str, Query(pattern="^(approved|rejected)$")],
    reason: Annotated[str, Query(min_length=8, max_length=500)],
) -> dict[str, str]:
    actor_id = None if actor is None else actor.id
    try:
        if decision == "approved":
            row, revision = approve_candidate(
                db, settings.company_bundle, candidate_id, actor_id, reason
            )
            qmd = await request_qmd_reindex(settings.qmd_url)
        else:
            row = reject_candidate(db, candidate_id, actor_id, reason)
            revision = row.base_revision
            qmd = "unchanged"
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except (ValueError, RuntimeError) as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    record_audit(
        db,
        actor_id=actor_id,
        action=f"okf.candidate_{decision}",
        target_type="okf_candidate",
        target_id=candidate_id,
        metadata={"reason": reason, "revision": revision, "qmd": qmd},
    )
    db.commit()
    return {
        "candidate_id": candidate_id,
        "status": row.status,
        "revision": revision,
        "qmd": qmd,
    }


@app.post("/api/okf/approve")
async def approve_okf_diff(
    settings: Annotated[Settings, Depends(get_settings)],
    actor: Annotated[User | None, Depends(require_role("approver"))],
    db: Annotated[Session, Depends(get_db)],
    message: Annotated[str, Query(min_length=8, max_length=180)] = "Approve OKF candidate",
) -> dict[str, str]:
    candidate = (
        db.query(OKFCandidate)
        .filter(OKFCandidate.status == "pending")
        .order_by(OKFCandidate.created_at.desc())
        .first()
    )
    if candidate is None:
        raise HTTPException(status_code=409, detail="Onaylanacak OKF adayı yok")
    try:
        candidate, revision = approve_candidate(
            db,
            settings.company_bundle,
            candidate.id,
            None if actor is None else actor.id,
            message,
        )
    except (ValueError, RuntimeError) as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    qmd = await request_qmd_reindex(settings.qmd_url)
    record_audit(
        db,
        actor_id=None if actor is None else actor.id,
        action="okf.approved",
        target_type="okf_revision",
        target_id=candidate.id,
        metadata={"message": message, "revision": revision, "qmd": qmd},
    )
    db.commit()
    return {"status": "approved", "revision": revision, "qmd": qmd}


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
def evidence(
    evidence_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    try:
        resolved = resolve_evidence_excerpt(db, settings.raw_root, evidence_id)
    except RuntimeError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    if resolved is not None:
        return resolved
    raise HTTPException(status_code=404, detail="Evidence bulunamadı")


@app.get("/api/agents")
def agents(db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    ensure_platform_registry(db)
    rows = (
        db.query(AgentDefinitionRow)
        .order_by(AgentDefinitionRow.id, AgentDefinitionRow.version.desc())
        .all()
    )
    return {
        "items": [
            {
                **agent_from_row(row).model_dump(exclude={"system_prompt"}),
                "status": row.status,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
            }
            for row in rows
        ]
    }


@app.get("/api/agents/{agent_id}/versions")
def agent_versions(
    agent_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    rows = (
        db.query(AgentDefinitionRow)
        .filter(AgentDefinitionRow.id == agent_id)
        .order_by(AgentDefinitionRow.version.desc())
        .all()
    )
    return {
        "items": [
            {
                **agent_from_row(row).model_dump(exclude={"system_prompt"}),
                "status": row.status,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
            }
            for row in rows
        ]
    }


@app.post("/api/agents/{agent_id}/versions/{version}/clone", status_code=201)
def agent_clone(
    agent_id: str,
    version: int,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User | None, Depends(require_role("admin"))],
) -> dict[str, Any]:
    source = db.get(AgentDefinitionRow, (agent_id, version))
    if source is None:
        raise HTTPException(status_code=404, detail="Agent version bulunamadı")
    row = clone_agent_version(db, source, None if actor is None else actor.id)
    record_audit(
        db,
        actor_id=None if actor is None else actor.id,
        action="agent.version_cloned",
        target_type="agent_version",
        target_id=f"{row.id}:{row.version}",
        metadata={"source_version": version},
    )
    db.commit()
    return {**agent_from_row(row).model_dump(), "status": row.status}


@app.put("/api/agents/{agent_id}/draft")
def agent_draft_save(
    agent_id: str,
    payload: ManagedAgentSpec,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User | None, Depends(require_role("admin"))],
) -> dict[str, Any]:
    if payload.id != agent_id:
        raise HTTPException(status_code=422, detail="Agent ID payload ile eşleşmiyor")
    try:
        row = save_agent_draft(db, payload, None if actor is None else actor.id)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    record_audit(
        db,
        actor_id=None if actor is None else actor.id,
        action="agent.draft_saved",
        target_type="agent_version",
        target_id=f"{row.id}:{row.version}",
    )
    db.commit()
    return {**agent_from_row(row).model_dump(), "status": row.status}


@app.post("/api/agents/{agent_id}/versions/{version}/publish")
def agent_publish(
    agent_id: str,
    version: int,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User | None, Depends(require_role("admin"))],
) -> dict[str, Any]:
    row = db.get(AgentDefinitionRow, (agent_id, version))
    if row is None:
        raise HTTPException(status_code=404, detail="Agent draft bulunamadı")
    try:
        publish_agent(db, row)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    record_audit(
        db,
        actor_id=None if actor is None else actor.id,
        action="agent.version_published",
        target_type="agent_version",
        target_id=f"{row.id}:{row.version}",
    )
    db.commit()
    return {**agent_from_row(row).model_dump(exclude={"system_prompt"}), "status": row.status}


@app.get("/api/capabilities")
def capabilities(db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    ensure_platform_registry(db)
    rows = (
        db.query(CapabilityDefinitionRow)
        .order_by(CapabilityDefinitionRow.id, CapabilityDefinitionRow.version.desc())
        .all()
    )
    return {
        "items": [
            {
                "id": row.id,
                "version": row.version,
                "name": row.name,
                "status": row.status,
                "definition": row.definition,
            }
            for row in rows
        ]
    }


@app.get("/api/workflows/default", response_model=WorkflowDefinition)
def default_workflow(db: Annotated[Session, Depends(get_db)]) -> WorkflowDefinition:
    ensure_platform_registry(db)
    row = latest_workflow(db, "growth-diagnostic")
    if row is None:
        return build_default_workflow()
    return workflow_from_row(row)


@app.get("/api/workflows")
def workflow_list(db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    ensure_platform_registry(db)
    rows = (
        db.query(WorkflowDefinitionRow)
        .order_by(WorkflowDefinitionRow.id, WorkflowDefinitionRow.version.desc())
        .all()
    )
    return {
        "items": [
            {
                "id": row.id,
                "version": row.version,
                "name": row.name,
                "status": row.status,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
            }
            for row in rows
        ]
    }


@app.get("/api/workflows/{workflow_id}/versions")
def workflow_versions(
    workflow_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    rows = (
        db.query(WorkflowDefinitionRow)
        .filter(WorkflowDefinitionRow.id == workflow_id)
        .order_by(WorkflowDefinitionRow.version.desc())
        .all()
    )
    return {"items": [workflow_from_row(row).model_dump(mode="json") for row in rows]}


@app.get(
    "/api/workflows/{workflow_id}/versions/{version}",
    response_model=WorkflowDefinition,
)
def workflow_version_detail(
    workflow_id: str,
    version: int,
    db: Annotated[Session, Depends(get_db)],
) -> WorkflowDefinition:
    row = db.get(WorkflowDefinitionRow, (workflow_id, version))
    if row is None:
        raise HTTPException(status_code=404, detail="Workflow version bulunamadı")
    return workflow_from_row(row)


@app.post("/api/workflows", response_model=WorkflowDefinition, status_code=201)
def workflow_create(
    workflow: WorkflowDefinition,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User | None, Depends(require_role("analyst"))],
) -> WorkflowDefinition:
    try:
        row = save_workflow_draft(db, workflow, None if actor is None else actor.id)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    record_audit(
        db,
        actor_id=None if actor is None else actor.id,
        action="workflow.draft_created",
        target_type="workflow_version",
        target_id=f"{row.id}:{row.version}",
    )
    db.commit()
    return workflow_from_row(row)


@app.put("/api/workflows/{workflow_id}/draft", response_model=WorkflowDefinition)
def workflow_draft_save(
    workflow_id: str,
    workflow: WorkflowDefinition,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User | None, Depends(require_role("analyst"))],
) -> WorkflowDefinition:
    if workflow.id != workflow_id:
        raise HTTPException(status_code=422, detail="Workflow ID payload ile eşleşmiyor")
    try:
        row = save_workflow_draft(db, workflow, None if actor is None else actor.id)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    record_audit(
        db,
        actor_id=None if actor is None else actor.id,
        action="workflow.draft_saved",
        target_type="workflow_version",
        target_id=f"{row.id}:{row.version}",
    )
    db.commit()
    return workflow_from_row(row)


@app.post(
    "/api/workflows/{workflow_id}/versions/{version}/clone",
    response_model=WorkflowDefinition,
    status_code=201,
)
def workflow_clone(
    workflow_id: str,
    version: int,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User | None, Depends(require_role("analyst"))],
    target_id: Annotated[str | None, Query(max_length=80)] = None,
) -> WorkflowDefinition:
    source = db.get(WorkflowDefinitionRow, (workflow_id, version))
    if source is None:
        raise HTTPException(status_code=404, detail="Workflow version bulunamadı")
    try:
        row = clone_workflow_version(
            db,
            source,
            None if actor is None else actor.id,
            target_id=target_id,
        )
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    record_audit(
        db,
        actor_id=None if actor is None else actor.id,
        action="workflow.version_cloned",
        target_type="workflow_version",
        target_id=f"{row.id}:{row.version}",
        metadata={"source": f"{source.id}:{source.version}"},
    )
    db.commit()
    return workflow_from_row(row)


@app.post("/api/workflows/validate", response_model=WorkflowValidation)
def workflow_validate(workflow: WorkflowDefinition) -> WorkflowValidation:
    return validate_workflow(workflow)


@app.post("/api/workflows/dry-run")
def workflow_dry_run(
    workflow: WorkflowDefinition,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User | None, Depends(require_role("analyst"))],
) -> dict[str, Any]:
    result = run_workflow_locally(workflow)
    record_audit(
        db,
        actor_id=None if actor is None else actor.id,
        action="workflow.dry_run",
        target_type="workflow",
        target_id=workflow.id,
        metadata={"version": workflow.version},
    )
    db.commit()
    return result


@app.post("/api/workflows/{workflow_id}/versions/{version}/dry-run")
def workflow_version_dry_run(
    workflow_id: str,
    version: int,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User | None, Depends(require_role("analyst"))],
) -> dict[str, Any]:
    row = db.get(WorkflowDefinitionRow, (workflow_id, version))
    if row is None:
        raise HTTPException(status_code=404, detail="Workflow version bulunamadı")
    result = run_workflow_locally(workflow_from_row(row))
    record_audit(
        db,
        actor_id=None if actor is None else actor.id,
        action="workflow.version_dry_run",
        target_type="workflow_version",
        target_id=f"{workflow_id}:{version}",
    )
    db.commit()
    return result


@app.post(
    "/api/workflows/{workflow_id}/versions/{version}/publish",
    response_model=WorkflowDefinition,
)
def workflow_publish(
    workflow_id: str,
    version: int,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User | None, Depends(require_role("admin"))],
) -> WorkflowDefinition:
    row = db.get(WorkflowDefinitionRow, (workflow_id, version))
    if row is None:
        raise HTTPException(status_code=404, detail="Workflow draft bulunamadı")
    try:
        publish_workflow(db, row)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    record_audit(
        db,
        actor_id=None if actor is None else actor.id,
        action="workflow.version_published",
        target_type="workflow_version",
        target_id=f"{workflow_id}:{version}",
    )
    db.commit()
    return workflow_from_row(row)


@app.post("/api/workflows/{workflow_id}/versions/{version}/run", status_code=202)
async def workflow_version_run(
    workflow_id: str,
    version: int,
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User | None, Depends(require_role("analyst"))],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=180)],
) -> dict[str, Any]:
    row = db.get(WorkflowDefinitionRow, (workflow_id, version))
    if row is None:
        raise HTTPException(status_code=404, detail="Published workflow version bulunamadı")
    try:
        run = await start_persisted_workflow(
            db,
            settings,
            row,
            idempotency_key,
            None if actor is None else actor.id,
        )
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=409, detail="Workflow run tamamlanamadı") from error
    record_audit(
        db,
        actor_id=None if actor is None else actor.id,
        action="workflow.started",
        target_type="workflow_run",
        target_id=run.id,
        metadata={"workflow_id": workflow_id, "version": version},
    )
    db.commit()
    return {"run_id": run.id, "status": run.status, "current_step": run.current_step}


@app.post("/api/workflows/{workflow_id}/versions/{version}/schedules", status_code=201)
def workflow_schedule_create(
    workflow_id: str,
    version: int,
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User | None, Depends(require_role("admin"))],
    cron: Annotated[str, Query(min_length=9, max_length=120)],
    timezone: Annotated[str, Query(min_length=3, max_length=80)] = "Europe/Istanbul",
) -> dict[str, Any]:
    workflow = db.get(WorkflowDefinitionRow, (workflow_id, version))
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow version bulunamadı")
    try:
        row = create_schedule(
            db,
            workflow,
            cron,
            timezone,
            None if actor is None else actor.id,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    record_audit(
        db,
        actor_id=None if actor is None else actor.id,
        action="workflow.schedule_created",
        target_type="workflow_schedule",
        target_id=row.id,
        metadata={"workflow_id": workflow_id, "version": version},
    )
    db.commit()
    return {
        "id": row.id,
        "workflow_id": row.workflow_id,
        "workflow_version": row.workflow_version,
        "cron": row.cron,
        "timezone": row.timezone,
        "enabled": row.enabled,
    }


@app.get("/api/workflow-schedules")
def workflow_schedules(db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    rows = db.query(WorkflowSchedule).order_by(WorkflowSchedule.created_at.desc()).all()
    return {
        "items": [
            {
                "id": row.id,
                "workflow_id": row.workflow_id,
                "workflow_version": row.workflow_version,
                "cron": row.cron,
                "timezone": row.timezone,
                "enabled": row.enabled,
                "last_fire_key": row.last_fire_key,
            }
            for row in rows
        ]
    }


@app.get("/api/approvals")
def approval_list(db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    rows = db.query(ApprovalRequest).order_by(ApprovalRequest.expires_at.desc()).all()
    return {
        "items": [
            {
                "id": row.id,
                "run_id": row.run_id,
                "kind": row.kind,
                "status": row.status,
                "artifact_uri": row.artifact_uri,
                "requested_role": row.requested_role,
                "candidate_id": row.candidate_id,
                "decision_by": row.decision_by,
                "decision_reason": row.decision_reason,
                "expires_at": row.expires_at,
                "decided_at": row.decided_at,
            }
            for row in rows
        ]
    }


@app.post("/api/approvals/{approval_id}/decision")
async def approval_decision(
    approval_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User | None, Depends(require_role("approver"))],
    decision: Annotated[str, Query(pattern="^(approved|rejected)$")],
    reason: Annotated[str, Query(min_length=8, max_length=500)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=180)],
) -> dict[str, Any]:
    approval = db.scalar(
        select(ApprovalRequest).where(ApprovalRequest.id == approval_id).with_for_update()
    )
    if approval is None:
        raise HTTPException(status_code=404, detail="Approval bulunamadı")
    if settings.enable_dbos:
        duplicate_key = db.scalar(
            select(ApprovalRequest.id).where(
                ApprovalRequest.decision_idempotency_key == idempotency_key,
                ApprovalRequest.id != approval.id,
            )
        )
        if duplicate_key is not None:
            raise HTTPException(status_code=409, detail="Decision idempotency key was already used")
        if approval.decision_idempotency_key == idempotency_key:
            run = db.get(WorkflowRun, approval.run_id)
            return {
                "approval_id": approval_id,
                "decision": decision,
                "run_status": approval.status if run is None else run.status,
                "qmd": "duplicate",
            }
        if approval.status != "pending":
            raise HTTPException(status_code=409, detail="Approval decision is stale")
        expires_at = approval.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at <= datetime.now(UTC):
            expire_approval_state(db, approval, datetime.now(UTC))
            db.commit()
            raise HTTPException(status_code=409, detail="Approval has expired")
        payload = {
            "approval_id": approval.id,
            "decision": decision,
            "reason": reason,
            "actor_id": None if actor is None else actor.id,
            "idempotency_key": idempotency_key,
        }
        try:
            await DBOS.send_async(
                approval.run_id,
                payload,
                topic=f"approval:{approval.id}",
                idempotency_key=idempotency_key,
            )
        except Exception as error:
            db.rollback()
            raise HTTPException(
                status_code=503, detail="Approval runtime is temporarily unavailable"
            ) from error
        approval.status = "decision_submitted"
        approval.decision_by = None if actor is None else actor.id
        approval.decision_reason = reason
        approval.decision_idempotency_key = idempotency_key
        record_audit(
            db,
            actor_id=None if actor is None else actor.id,
            action="approval.decision_submitted",
            target_type="approval_request",
            target_id=approval_id,
            metadata={"run_id": approval.run_id, "decision": decision, "reason": reason},
        )
        db.commit()
        return {
            "approval_id": approval_id,
            "decision": decision,
            "run_status": "decision_submitted",
            "qmd": "pending",
        }
    try:
        run, qmd = await decide_persisted_approval(
            db,
            settings,
            approval,
            decision=decision,
            reason=reason,
            actor_id=None if actor is None else actor.id,
            idempotency_key=idempotency_key,
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except (ValueError, RuntimeError) as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    record_audit(
        db,
        actor_id=None if actor is None else actor.id,
        action=f"approval.{decision}",
        target_type="approval_request",
        target_id=approval_id,
        metadata={"run_id": run.id, "reason": reason, "qmd": qmd},
    )
    db.commit()
    return {"approval_id": approval_id, "decision": decision, "run_status": run.status, "qmd": qmd}


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
