from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

import httpx

from agi_server.okf.bundle import FileSystemOKFBundle

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@dataclass(frozen=True)
class SearchHit:
    path: str
    title: str
    score: float
    snippet: str
    engine: str
    locator: str | None = None


class KnowledgeSearch:
    def __init__(
        self,
        bundle: FileSystemOKFBundle,
        qmd_url: str | None = None,
        db: Session | None = None,
    ):
        self.bundle = bundle
        self.qmd_url = qmd_url
        self.db = db

    def _resolve_locator(self, raw_loc: str | None, default_path: str) -> str | None:
        if raw_loc:
            if self.db is not None:
                from agi_server.db import EvidenceItem
                row = self.db.get(EvidenceItem, raw_loc)
                if row is not None:
                    return raw_loc
                return None
            return None
        if self.db is not None and default_path:
            from agi_server.db import EvidenceItem
            row = self.db.get(EvidenceItem, default_path)
            if row is not None:
                return str(row.id)
        return None

    def search_sync(self, query: str, limit: int = 8) -> list[SearchHit]:
        clean_query = query.strip()[:500]
        if self.qmd_url and clean_query:
            try:
                with httpx.Client(timeout=5) as client:
                    response = client.get(
                        f"{self.qmd_url.rstrip('/')}/search",
                        params={"q": clean_query, "limit": limit},
                    )
                    response.raise_for_status()
                    rows = response.json()
                    if isinstance(rows, list):
                        return [
                            SearchHit(
                                path=str(row.get("file") or row.get("path") or "concept.md"),
                                title=str(row.get("title") or row.get("file") or "Untitled"),
                                score=float(row.get("score") or 0),
                                snippet=str(row.get("snippet") or row.get("content") or "")[:320],
                                engine=str(row.get("engine") or "chroma"),
                                locator=self._resolve_locator(
                                    row.get("locator") or row.get("evidence_id"),
                                    str(row.get("file") or row.get("path") or ""),
                                ),
                            )
                            for row in rows[:limit]
                        ]
            except (httpx.HTTPError, ValueError, TypeError):
                pass
        return self._lexical(clean_query, limit)

    async def search(self, query: str, limit: int = 8) -> list[SearchHit]:
        clean_query = query.strip()[:500]
        if self.qmd_url and clean_query:
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    response = await client.get(
                        f"{self.qmd_url.rstrip('/')}/search",
                        params={"q": clean_query, "limit": limit},
                    )
                    response.raise_for_status()
                    rows = response.json()
                    if isinstance(rows, list):
                        return [
                            SearchHit(
                                path=str(row.get("file") or row.get("path") or "concept.md"),
                                title=str(row.get("title") or row.get("file") or "Untitled"),
                                score=float(row.get("score") or 0),
                                snippet=str(row.get("snippet") or row.get("content") or "")[:320],
                                engine=str(row.get("engine") or "chroma"),
                                locator=self._resolve_locator(
                                    row.get("locator") or row.get("evidence_id"),
                                    str(row.get("file") or row.get("path") or ""),
                                ),
                            )
                            for row in rows[:limit]
                        ]
            except (httpx.HTTPError, ValueError, TypeError):
                pass
        return self._lexical(clean_query, limit)

    def _lexical(self, query: str, limit: int) -> list[SearchHit]:
        terms = {
            term.lower() for term in re.findall(r"[\wçğıöşüÇĞİÖŞÜ-]+", query) if len(term) > 1
        }
        hits: list[SearchHit] = []
        for concept in self.bundle.list_concepts():
            haystack = f"{concept.title}\n{concept.body}".lower()
            matched = sum(haystack.count(term) for term in terms)
            if matched:
                clean_body = " ".join(concept.body.replace("#", "").split())
                hits.append(
                    SearchHit(
                        path=concept.path,
                        title=concept.title,
                        score=float(matched),
                        snippet=clean_body[:320],
                        engine="lexical-fallback",
                        locator=self._resolve_locator(None, concept.path),
                    )
                )
        return sorted(hits, key=lambda item: (-item.score, item.path))[:limit]
