from __future__ import annotations

import os
from pathlib import Path

import pytest
from agi_server.agents.registry import AgentRegistry


def test_agent_registry_list_works_from_any_cwd(tmp_path: Path):
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        registry = AgentRegistry()
        specs = registry.list()
        assert len(specs) == 4
        ids = {spec.id for spec in specs}
        assert "company-analyst" in ids
        assert "evidence-reviewer" in ids
        assert "growth-opportunity-analyst" in ids
        assert "wiki-curator" in ids
    finally:
        os.chdir(original_cwd)


def test_agent_registry_raises_runtime_error_on_empty_dir(tmp_path: Path):
    empty_dir = tmp_path / "empty_specs"
    empty_dir.mkdir()
    registry = AgentRegistry(directory=empty_dir)
    with pytest.raises(RuntimeError, match="No agent specs found in directory"):
        registry.list()


def test_agent_spec_capabilities_must_be_allowlisted_in_builtin_capabilities():
    from agi_server.agents.capabilities import BUILTIN_CAPABILITIES
    from agi_server.agents.registry import ManagedAgentSpec

    specs = AgentRegistry().list()
    for spec in specs:
        for cap in spec.capabilities:
            assert cap in BUILTIN_CAPABILITIES, f"Capability {cap} not in BUILTIN_CAPABILITIES"

    with pytest.raises(ValueError, match="Unknown capability IDs in spec"):
        ManagedAgentSpec(
            id="test-agent",
            name="Test Agent",
            version=1,
            model_profile="local-balanced",
            output_type="CompanyAnalysis",
            capabilities=["knowledge.search", "unsupported_fake_cap.read"],
            timeout_seconds=60,
            max_output_tokens=500,
            data_classification="internal",
            approval_risk="low",
            system_prompt="This is a test prompt that meets minimum length requirement.",
        )


def test_ensure_platform_registry_seeds_all_builtin_capabilities(tmp_path: Path):
    from agi_server.agents.capabilities import BUILTIN_CAPABILITIES
    from agi_server.db import Base, CapabilityDefinitionRow
    from agi_server.workflow.registry_service import ensure_platform_registry
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(f"sqlite:///{(tmp_path / 'cap_test.db').as_posix()}")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    with session_factory() as db:
        ensure_platform_registry(db)
        rows = list(db.scalars(select(CapabilityDefinitionRow.id)))
        assert set(rows) == set(BUILTIN_CAPABILITIES.keys())
    engine.dispose()
