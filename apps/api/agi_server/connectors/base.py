from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, Field


class Health(BaseModel):
    ok: bool
    message: str


class SourceSchema(BaseModel):
    source_id: str
    entities: dict[str, list[str]]
    read_only: bool = True


class RawRecord(BaseModel):
    source_id: str
    entity_type: str
    external_id: str
    data: dict[str, Any]
    locator: dict[str, Any]


class SyncResult(BaseModel):
    records: list[RawRecord]
    next_cursor: str | None = None
    complete: bool = True
    warnings: list[str] = Field(default_factory=list)


class ConnectorPort(Protocol):
    def test_connection(self) -> Health: ...

    def discover_schema(self) -> SourceSchema: ...

    def preview(self, limit: int = 50) -> list[RawRecord]: ...

    def sync(self, cursor: str | None = None) -> SyncResult: ...

    def health(self) -> Health: ...
