from pathlib import Path

import pytest
from agi_server.config import Settings
from agi_server.db import AuditEvent, Base, User
from agi_server.http_security import RequestSecurityMiddleware
from agi_server.migrations import INITIAL_REVISION, LEGACY_TABLES, alembic_config, run_migrations
from agi_server.security import BootstrapRequest, bootstrap_admin
from alembic import command
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from starlette.middleware.sessions import SessionMiddleware


def sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


def test_explicit_migration_upgrades_empty_database(tmp_path: Path) -> None:
    url = sqlite_url(tmp_path / "empty.db")

    run_migrations(url)

    engine = create_engine(url)
    assert LEGACY_TABLES.issubset(inspect(engine).get_table_names())
    with engine.connect() as connection:
        revision = connection.scalar(text("SELECT version_num FROM alembic_version"))
        assert revision == "20260724_0009"
    engine.dispose()


def test_known_legacy_scaffold_is_stamped_without_recreating_tables(tmp_path: Path) -> None:
    url = sqlite_url(tmp_path / "legacy.db")
    command.upgrade(alembic_config(url), INITIAL_REVISION)
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE alembic_version"))
    engine.dispose()

    run_migrations(url)

    engine = create_engine(url)
    with engine.connect() as connection:
        revision = connection.scalar(text("SELECT version_num FROM alembic_version"))
        assert revision == "20260724_0009"
    engine.dispose()


def test_production_rejects_demo_auth_and_default_secrets() -> None:
    with pytest.raises(ValueError, match="DEMO_NO_AUTH"):
        Settings(environment="production", demo_no_auth=True)

    with pytest.raises(ValueError, match="bootstrap token"):
        Settings(environment="production", demo_no_auth=False)


def test_production_cloud_key_must_come_from_secret_file(tmp_path: Path) -> None:
    secure = {
        "environment": "production",
        "demo_no_auth": False,
        "bootstrap_token": "b" * 32,
        "session_secret": "s" * 40,
        "master_key": "m" * 40,
        "cloud_models_enabled": True,
        "cloud_provider": "groq",
    }
    with pytest.raises(ValueError, match="secret file"):
        Settings(**secure, cloud_api_key="not-allowed-in-production")

    secret_file = tmp_path / "provider-key"
    secret_file.write_text("provider-secret", encoding="utf-8")
    settings = Settings(**secure, cloud_api_key_file=secret_file)
    assert settings.cloud_api_key is not None
    assert settings.cloud_api_key.get_secret_value() == "provider-secret"


def test_bootstrap_creates_one_admin_with_roles_and_audit(tmp_path: Path) -> None:
    url = sqlite_url(tmp_path / "bootstrap.db")
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    local_session = sessionmaker(bind=engine, expire_on_commit=False)
    payload = BootstrapRequest(
        token="test-bootstrap-token",
        email="admin@example.com",
        name="Test Admin",
        password="correct-horse-battery-staple",
    )

    with local_session() as db:
        user = bootstrap_admin(
            payload,
            db,
            Settings(bootstrap_token="test-bootstrap-token"),
        )
        assert user.roles == ["admin", "analyst", "approver"]
        assert db.query(AuditEvent).filter_by(action="auth.bootstrap").count() == 1
        with pytest.raises(HTTPException) as conflict:
            bootstrap_admin(payload, db, Settings(bootstrap_token="test-bootstrap-token"))
        assert getattr(conflict.value, "status_code", None) == 409

    engine.dispose()


def test_session_and_csrf_middleware_fail_closed(tmp_path: Path, monkeypatch) -> None:
    url = sqlite_url(tmp_path / "security.db")
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    local_session = sessionmaker(bind=engine, expire_on_commit=False)
    with local_session() as db:
        db.add(
            User(
                id="user-1",
                email="admin@example.test",
                name="Admin",
                password_hash="unused",
                roles=["admin"],
                active=True,
            )
        )
        db.commit()

    import agi_server.http_security as security_module

    monkeypatch.setattr(security_module, "SessionLocal", local_session)
    monkeypatch.setattr(
        security_module,
        "get_settings",
        lambda: Settings(demo_no_auth=False, database_url=url),
    )

    app = FastAPI()
    app.add_middleware(RequestSecurityMiddleware)
    app.add_middleware(SessionMiddleware, secret_key="test-session-secret-with-32-characters")

    @app.post("/api/auth/login")
    def login(request: Request) -> dict[str, str]:
        request.session.update({"user_id": "user-1", "csrf_token": "csrf-test"})
        return {"csrf_token": "csrf-test"}

    @app.get("/api/private")
    def private_get() -> dict[str, bool]:
        return {"ok": True}

    @app.post("/api/private")
    def private_post() -> dict[str, bool]:
        return {"ok": True}

    with TestClient(app) as client:
        unauthenticated = client.get("/api/private")
        assert unauthenticated.status_code == 401
        assert unauthenticated.json()["error"]["code"] == "auth.required"
        assert unauthenticated.headers["X-Request-ID"]

        client.post("/api/auth/login")
        assert client.get("/api/private").status_code == 200
        assert client.post("/api/private").status_code == 403
        assert client.post("/api/private", headers={"X-CSRF-Token": "csrf-test"}).status_code == 200

    engine.dispose()
