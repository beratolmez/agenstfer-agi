from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any

import httpx
from dbos import DBOS, DBOSConfig, SetWorkflowID
from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, Response, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from agi_server import __version__
from agi_server.agents import AgentRegistry
from agi_server.agents.model_gateway import resolve_model_profile
from agi_server.config import Settings, get_settings
from agi_server.connectors.files import MAX_FILE_BYTES, ReadOnlyTabularConnector
from agi_server.db import (
    DataSource,
    OKFCandidate,
    SourceMapping,
    SourceSyncRun,
    User,
    engine,
    get_db,
)
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
from agi_server.schemas import GrowthDiagnostic, HealthResponse, SourceMappingRequest
from agi_server.security import (
    AuthSessionView,
    BootstrapRequest,
    LoginRequest,
    UserView,
    authenticate,
    bootstrap_admin,
    current_user,
    record_audit,
    require_role,
    start_session,
)
from agi_server.workflow import build_default_workflow, validate_workflow
from agi_server.workflow.models import WorkflowDefinition, WorkflowValidation
from agi_server.workflow.runtime import durable_workflow_interpreter, run_workflow_locally


@asynccontextmanager
async def lifespan(_: FastAPI):
    run_migrations()
    settings = get_settings()
    ensure_active_repository(settings.company_bundle)
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
    allow_headers=["Content-Type", "X-CSRF-Token"],
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
    return build_growth_diagnostic(db)


@app.post("/api/diagnostics/run", response_model=GrowthDiagnostic)
def run_diagnostic(
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User | None, Depends(require_role("analyst"))],
) -> GrowthDiagnostic:
    # The current vertical slice is deterministic; DBOS/Pydantic AI are plugged in by Phase 3/4.
    result = build_growth_diagnostic(db)
    record_audit(
        db,
        actor_id=None if actor is None else actor.id,
        action="diagnostic.fixture_run",
        target_type="diagnostic",
        target_id=result.id,
        metadata={"mode": "deterministic_fixture"},
    )
    db.commit()
    return result


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
def agents() -> list[dict[str, Any]]:
    return [spec.model_dump(exclude={"system_prompt"}) for spec in AgentRegistry().list()]


@app.get("/api/workflows/default", response_model=WorkflowDefinition)
def default_workflow() -> WorkflowDefinition:
    return build_default_workflow()


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


@app.post("/api/workflows/run", status_code=202)
def workflow_run(
    workflow: WorkflowDefinition,
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User | None, Depends(require_role("analyst"))],
    idempotency_key: Annotated[str, Query(min_length=8, max_length=180)],
) -> dict[str, Any]:
    validation = validate_workflow(workflow)
    if not validation.valid:
        raise HTTPException(
            status_code=422, detail=[item.model_dump() for item in validation.issues]
        )
    if not settings.enable_dbos:
        response = {
            "workflow_id": idempotency_key,
            "status": "dry-run",
            "result": run_workflow_locally(workflow),
        }
        record_audit(
            db,
            actor_id=None if actor is None else actor.id,
            action="workflow.local_run",
            target_type="workflow",
            target_id=workflow.id,
            metadata={"version": workflow.version, "idempotency_key": idempotency_key},
        )
        db.commit()
        return response
    with SetWorkflowID(idempotency_key):
        handle = DBOS.start_workflow(
            durable_workflow_interpreter,
            workflow.model_dump(mode="json"),
            {"dry_run": False},
        )
    workflow_id = handle.get_workflow_id()
    record_audit(
        db,
        actor_id=None if actor is None else actor.id,
        action="workflow.started",
        target_type="workflow_run",
        target_id=workflow_id,
        metadata={"workflow_id": workflow.id, "version": workflow.version},
    )
    db.commit()
    return {"workflow_id": workflow_id, "status": "started"}


@app.post("/api/workflows/{workflow_id}/approval", status_code=202)
def workflow_approval(
    workflow_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db)],
    actor: Annotated[User | None, Depends(require_role("approver"))],
    decision: Annotated[str, Query(pattern="^(approved|rejected)$")],
    node_id: Annotated[str, Query(min_length=2, max_length=64)] = "approval",
    reason: Annotated[str, Query(min_length=3, max_length=500)] = "Reviewed in MVP console",
) -> dict[str, str]:
    if not settings.enable_dbos:
        raise HTTPException(status_code=409, detail="DBOS runtime bu profilde kapalı")
    DBOS.send(
        workflow_id,
        {
            "decision": decision,
            "actor_role": "approver",
            "actor_id": None if actor is None else actor.id,
            "reason": reason,
        },
        topic=f"approval:{node_id}",
        idempotency_key=f"{workflow_id}:{node_id}:{decision}",
    )
    record_audit(
        db,
        actor_id=None if actor is None else actor.id,
        action=f"workflow.approval_{decision}",
        target_type="workflow_run",
        target_id=workflow_id,
        metadata={"node_id": node_id, "reason": reason},
    )
    db.commit()
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
