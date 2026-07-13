from __future__ import annotations

import re
from dataclasses import dataclass

import httpx

from agi_server.okf.bundle import FileSystemOKFBundle


@dataclass(frozen=True)
class SearchHit:
    path: str
    title: str
    score: float
    snippet: str
    engine: str


class KnowledgeSearch:
    def __init__(self, bundle: FileSystemOKFBundle, qmd_url: str | None = None):
        self.bundle = bundle
        self.qmd_url = qmd_url

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
                                path=str(row.get("file") or row.get("path")),
                                title=str(row.get("title") or row.get("file")),
                                score=float(row.get("score") or 0),
                                snippet=str(row.get("snippet") or row.get("content") or "")[:320],
                                engine="qmd",
                            )
                            for row in rows[:limit]
                        ]
            except (httpx.HTTPError, ValueError, TypeError):
                pass
        return self._lexical(clean_query, limit)

    def _lexical(self, query: str, limit: int) -> list[SearchHit]:
        terms = {term.lower() for term in re.findall(r"[\wçğıöşüÇĞİÖŞÜ-]+", query) if len(term) > 1}
        hits: list[SearchHit] = []
        for concept in self.bundle.list_concepts():
            haystack = f"{concept.title}\n{concept.body}".lower()
            matched = sum(haystack.count(term) for term in terms)
            if matched:
                hits.append(
                    SearchHit(
                        path=concept.path,
                        title=concept.title,
                        score=float(matched),
                        snippet=" ".join(concept.body.replace("#", "").split())[:320],
                        engine="lexical-fallback",
                    )
                )
        return sorted(hits, key=lambda item: (-item.score, item.path))[:limit]
