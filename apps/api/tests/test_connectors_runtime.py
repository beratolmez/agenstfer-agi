from pathlib import Path

import pytest
from agi_server.connectors.demo import DemoCompanyConnector
from agi_server.ingestion.raw_vault import RawVault
from agi_server.workflow import build_default_workflow
from agi_server.workflow.runtime import run_workflow_locally


def test_demo_connector_uses_cursor_and_is_read_only():
    connector = DemoCompanyConnector(page_size=100)
    first = connector.sync()
    second = connector.sync(first.next_cursor)
    assert len(first.records) == 100
    assert first.next_cursor == "100"
    assert second.records[0].external_id != first.records[0].external_id
    assert not hasattr(connector, "update")


def test_raw_vault_is_immutable(tmp_path: Path):
    vault = RawVault(tmp_path / "raw")
    snapshot = vault.store("src-1", "data.csv", b"id,name\n1,Atlas\n", "csv")
    assert len(snapshot.sha256) == 64
    vault.store("src-1", "data.csv", b"id,name\n1,Atlas\n", "csv")
    with pytest.raises(FileExistsError):
        vault.store("src-1", "data.csv", b"changed", "csv")


def test_local_workflow_dry_run_executes_catalog_in_order():
    result = run_workflow_locally(build_default_workflow())
    assert result["status"] == "dry-run-completed"
    assert result["approval"]["status"] == "skipped-in-dry-run"
    assert result["artifact_uri"] == "okf://reports/growth-diagnostic-v1"
    assert len(result["diagnostic"]["opportunities"]) == 5
