from __future__ import annotations

from pathlib import Path

from agi_server.connectors.base import Health, RawRecord, SourceSchema, SyncResult
from agi_server.connectors.files import ReadOnlyTabularConnector

SUPPORTED_CRM_ENTITIES = {"accounts", "contacts", "leads", "opportunities"}
SUPPORTED_ERP_ENTITIES = {"products", "orders", "invoices", "customer_revenue"}


class ReadOnlyCRMConnector:
    """Read-only CRM Connector reading Account, Contact, Lead, Opportunity data."""

    def __init__(
        self,
        path_or_uri: Path | str,
        source_id: str,
        entity_type: str = "accounts",
        field_mapping: dict[str, str] | None = None,
    ):
        if entity_type not in SUPPORTED_CRM_ENTITIES:
            valid = sorted(SUPPORTED_CRM_ENTITIES)
            raise ValueError(f"Unsupported CRM entity_type: {entity_type}. Supported: {valid}")
        self.source_id = source_id
        self.entity_type = entity_type
        self.tabular = ReadOnlyTabularConnector(
            path=path_or_uri,
            source_id=source_id,
            entity_type=entity_type,
            field_mapping=field_mapping,
        )

    def test_connection(self) -> Health:
        health = self.tabular.test_connection()
        if not health.ok:
            return health
        return Health(ok=True, message=f"Read-Only CRM connector ready for {self.entity_type}")

    def discover_schema(self) -> SourceSchema:
        schema = self.tabular.discover_schema()
        return SourceSchema(
            source_id=self.source_id,
            entities=schema.entities,
            read_only=True,
        )

    def preview(self, limit: int = 50) -> list[RawRecord]:
        return self.tabular.preview(limit=limit)

    def sync(self, cursor: str | None = None) -> SyncResult:
        result = self.tabular.sync(cursor=cursor)
        crm_records: list[RawRecord] = []
        for record in result.records:
            data = record.data
            locator = {
                **record.locator,
                "crm_system": "read_only_crm",
                "entity": self.entity_type,
            }
            crm_records.append(
                RawRecord(
                    source_id=self.source_id,
                    entity_type=self.entity_type,
                    external_id=record.external_id,
                    data=data,
                    locator=locator,
                )
            )
        return SyncResult(
            records=crm_records,
            next_cursor=result.next_cursor,
            complete=result.complete,
            warnings=result.warnings,
        )

    def health(self) -> Health:
        return self.test_connection()


class ReadOnlyERPConnector:
    """Read-only ERP Connector reading Product, Order, Invoice, CustomerRevenue data."""

    def __init__(
        self,
        path_or_uri: Path | str,
        source_id: str,
        entity_type: str = "invoices",
        field_mapping: dict[str, str] | None = None,
    ):
        if entity_type not in SUPPORTED_ERP_ENTITIES:
            valid = sorted(SUPPORTED_ERP_ENTITIES)
            raise ValueError(f"Unsupported ERP entity_type: {entity_type}. Supported: {valid}")
        self.source_id = source_id
        self.entity_type = entity_type
        self.tabular = ReadOnlyTabularConnector(
            path=path_or_uri,
            source_id=source_id,
            entity_type=entity_type,
            field_mapping=field_mapping,
        )

    def test_connection(self) -> Health:
        health = self.tabular.test_connection()
        if not health.ok:
            return health
        return Health(ok=True, message=f"Read-Only ERP connector ready for {self.entity_type}")

    def discover_schema(self) -> SourceSchema:
        schema = self.tabular.discover_schema()
        return SourceSchema(
            source_id=self.source_id,
            entities=schema.entities,
            read_only=True,
        )

    def preview(self, limit: int = 50) -> list[RawRecord]:
        return self.tabular.preview(limit=limit)

    def sync(self, cursor: str | None = None) -> SyncResult:
        result = self.tabular.sync(cursor=cursor)
        erp_records: list[RawRecord] = []
        for record in result.records:
            data = record.data
            locator = {
                **record.locator,
                "erp_system": "read_only_erp",
                "entity": self.entity_type,
            }
            erp_records.append(
                RawRecord(
                    source_id=self.source_id,
                    entity_type=self.entity_type,
                    external_id=record.external_id,
                    data=data,
                    locator=locator,
                )
            )
        return SyncResult(
            records=erp_records,
            next_cursor=result.next_cursor,
            complete=result.complete,
            warnings=result.warnings,
        )

    def health(self) -> Health:
        return self.test_connection()
