from __future__ import annotations

from agi_server.connectors.base import Health, RawRecord, SourceSchema, SyncResult
from agi_server.domain.demo import build_demo_dataset

DEMO_SOURCE_BY_ENTITY = {
    "accounts": "src-crm-001",
    "contacts": "src-crm-001",
    "opportunities": "src-crm-001",
    "activities": "src-crm-001",
    "products": "src-erp-001",
    "orders_invoices": "src-erp-001",
    "strategy_documents": "src-strategy-001",
}


class DemoCompanyConnector:
    source_id = "src-demo-company"

    def __init__(self, page_size: int = 200):
        self.page_size = page_size

    def test_connection(self) -> Health:
        return Health(ok=True, message="Deterministic demo adapter hazır")

    def discover_schema(self) -> SourceSchema:
        dataset = build_demo_dataset()
        dataset["strategy_documents"] = [self._strategy_document()]
        return SourceSchema(
            source_id=self.source_id,
            entities={
                name: sorted(rows[0].keys()) if rows else [] for name, rows in dataset.items()
            },
        )

    def _records(self) -> list[RawRecord]:
        result: list[RawRecord] = []
        dataset = build_demo_dataset()
        dataset["strategy_documents"] = [self._strategy_document()]
        for entity_type, rows in dataset.items():
            for row_index, row in enumerate(rows, start=2):
                external_id = str(row.get("id") or f"{entity_type}-{row_index}")
                result.append(
                    RawRecord(
                        source_id=DEMO_SOURCE_BY_ENTITY[entity_type],
                        entity_type=entity_type,
                        external_id=external_id,
                        data=row,
                        locator={
                            "kind": "tabular",
                            "sheet": entity_type,
                            "row": row_index,
                            "column": "*",
                        },
                    )
                )
        return result

    @staticmethod
    def _strategy_document() -> dict[str, str]:
        return {
            "id": "strategy-001",
            "title": "90 Günlük Büyüme Hedefi",
            "objective": "Mevcut müşteri tabanından kârlı büyüme",
            "content": (
                "Servis gelirini, enerji verimliliği paketlerini ve ihracata uygun "
                "OEM çözümlerini önceliklendir. Dış sistemlerde yazma işlemi yapma."
            ),
        }

    def preview(self, limit: int = 50) -> list[RawRecord]:
        return self._records()[: max(0, min(limit, 50))]

    def sync(self, cursor: str | None = None) -> SyncResult:
        offset = int(cursor or 0)
        records = self._records()
        page = records[offset : offset + self.page_size]
        next_offset = offset + len(page)
        complete = next_offset >= len(records)
        return SyncResult(
            records=page,
            next_cursor=None if complete else str(next_offset),
            complete=complete,
        )

    def health(self) -> Health:
        return self.test_connection()
