from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path, PurePath

from pydantic import BaseModel


class RawSnapshot(BaseModel):
    source_id: str
    filename: str
    sha256: str
    bytes: int
    collected_at: str
    source_type: str


class RawVault:
    def __init__(self, root: Path | str):
        self.root = Path(root).resolve()

    @staticmethod
    def _validate_name(value: str) -> str:
        name = PurePath(value).name
        if not name or name != value or name in {".", ".."}:
            raise ValueError("Geçersiz vault adı")
        return name

    def store(self, source_id: str, filename: str, payload: bytes, source_type: str) -> RawSnapshot:
        safe_source = self._validate_name(source_id)
        safe_filename = self._validate_name(filename)
        target_dir = self.root / safe_source
        target_dir.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(payload).hexdigest()
        snapshot_path = target_dir / safe_filename
        if (
            snapshot_path.exists()
            and hashlib.sha256(snapshot_path.read_bytes()).hexdigest() != digest
        ):
            raise FileExistsError("Immutable raw snapshot farklı içerikle üzerine yazılamaz")
        snapshot_path.write_bytes(payload)
        snapshot = RawSnapshot(
            source_id=safe_source,
            filename=safe_filename,
            sha256=digest,
            bytes=len(payload),
            collected_at=datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
            source_type=source_type,
        )
        manifest = target_dir / "manifest.json"
        manifest.write_text(
            json.dumps(snapshot.model_dump(), ensure_ascii=False, indent=2),
            encoding="utf-8",
            newline="\n",
        )
        return snapshot
