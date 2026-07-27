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
