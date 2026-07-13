from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from agi_server.config import get_settings

INITIAL_REVISION = "20260713_0001"
LEGACY_TABLES = {
    "users",
    "evidence_items",
    "canonical_entities",
    "canonical_facts",
    "workflow_definitions",
    "workflow_runs",
    "approval_requests",
    "audit_events",
}


def project_root() -> Path:
    candidates = [Path.cwd(), *Path(__file__).resolve().parents]
    for candidate in candidates:
        if (candidate / "alembic.ini").is_file() and (
            candidate / "apps" / "api" / "alembic"
        ).is_dir():
            return candidate
    raise RuntimeError("Cannot locate alembic.ini and apps/api/alembic")


def alembic_config(database_url: str) -> Config:
    root = project_root()
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "apps" / "api" / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    config.attributes["database_url"] = database_url
    return config


def run_migrations(database_url: str | None = None) -> None:
    """Upgrade the database and stamp the one known pre-Alembic scaffold safely."""
    url = database_url or get_settings().database_url
    engine = create_engine(
        url,
        connect_args={"check_same_thread": False} if url.startswith("sqlite") else {},
    )
    try:
        tables = set(inspect(engine).get_table_names())
    finally:
        engine.dispose()

    config = alembic_config(url)
    if "alembic_version" not in tables and LEGACY_TABLES.issubset(tables):
        command.stamp(config, INITIAL_REVISION)
    elif "alembic_version" not in tables and tables.intersection(LEGACY_TABLES):
        raise RuntimeError("Partial legacy schema detected; automatic migration is unsafe")
    command.upgrade(config, "head")
