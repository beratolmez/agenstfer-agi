import csv

import pytest
from agi_server.connectors.crm_erp import (
    ReadOnlyCRMConnector,
    ReadOnlyERPConnector,
)


@pytest.fixture
def temp_crm_csv(tmp_path):
    file_path = tmp_path / "crm_accounts.csv"
    with open(file_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "account_name", "industry", "revenue"])
        writer.writerow(["acc-101", "Acme Industrial", "Manufacturing", "5000000"])
        writer.writerow(["acc-102", "Global Tech", "Software", "12000000"])
    return file_path


@pytest.fixture
def temp_erp_csv(tmp_path):
    file_path = tmp_path / "erp_invoices.csv"
    with open(file_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "customer_id", "amount", "status"])
        writer.writerow(["inv-901", "acc-101", "150000", "paid"])
        writer.writerow(["inv-902", "acc-102", "320000", "pending"])
    return file_path


def test_unsupported_crm_entity_raises_value_error(temp_crm_csv):
    with pytest.raises(ValueError, match="Unsupported CRM entity_type"):
        ReadOnlyCRMConnector(
            path_or_uri=temp_crm_csv,
            source_id="src-crm-test",
            entity_type="invalid_entity",
        )


def test_unsupported_erp_entity_raises_value_error(temp_erp_csv):
    with pytest.raises(ValueError, match="Unsupported ERP entity_type"):
        ReadOnlyERPConnector(
            path_or_uri=temp_erp_csv,
            source_id="src-erp-test",
            entity_type="invalid_entity",
        )


def test_read_only_crm_connector_sync(temp_crm_csv):
    connector = ReadOnlyCRMConnector(
        path_or_uri=temp_crm_csv,
        source_id="src-crm-001",
        entity_type="accounts",
    )
    health = connector.health()
    assert health.ok is True

    schema = connector.discover_schema()
    assert schema.read_only is True
    assert "accounts" in schema.entities

    sync_result = connector.sync()
    assert sync_result.complete is True
    assert len(sync_result.records) == 2

    rec1 = sync_result.records[0]
    assert rec1.external_id == "acc-101"
    assert rec1.data["account_name"] == "Acme Industrial"
    assert rec1.locator["crm_system"] == "read_only_crm"


def test_read_only_erp_connector_sync(temp_erp_csv):
    connector = ReadOnlyERPConnector(
        path_or_uri=temp_erp_csv,
        source_id="src-erp-001",
        entity_type="invoices",
    )
    health = connector.health()
    assert health.ok is True

    schema = connector.discover_schema()
    assert schema.read_only is True
    assert "invoices" in schema.entities

    sync_result = connector.sync()
    assert sync_result.complete is True
    assert len(sync_result.records) == 2

    rec1 = sync_result.records[0]
    assert rec1.external_id == "inv-901"
    assert rec1.data["amount"] == "150000"
    assert rec1.locator["erp_system"] == "read_only_erp"
