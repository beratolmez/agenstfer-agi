import httpx
import pytest
from agi_server.okf.bundle import FileSystemOKFBundle
from agi_server.okf.lifecycle import request_qmd_reindex
from agi_server.okf.models import OKFConcept
from agi_server.okf.search import KnowledgeSearch, SearchHit


@pytest.mark.asyncio
async def test_knowledge_search_lexical_fallback_when_qmd_url_is_none(tmp_path):
    bundle_dir = tmp_path / "bundle"
    bundle = FileSystemOKFBundle(bundle_dir)
    bundle.create("Test Bundle")
    bundle.write(
        OKFConcept(
            path="growth.md",
            frontmatter={"type": "Concept", "title": "Growth Strategy"},
            body="# Growth Strategy\nFocus on B2B expansion.",
        )
    )

    searcher = KnowledgeSearch(bundle=bundle, qmd_url=None)
    hits = await searcher.search("growth")

    assert len(hits) == 1
    hit = hits[0]
    assert isinstance(hit, SearchHit)
    assert hit.path == "growth.md"
    assert hit.title == "Growth Strategy"
    assert hit.engine == "lexical-fallback"
    assert len(hit.snippet) <= 320
    assert hit.locator == "ev_concept_growth.md"


@pytest.mark.asyncio
async def test_knowledge_search_lexical_fallback_when_chroma_unreachable(tmp_path):
    bundle_dir = tmp_path / "bundle"
    bundle = FileSystemOKFBundle(bundle_dir)
    bundle.create("Test Bundle")
    bundle.write(
        OKFConcept(
            path="product.md",
            frontmatter={"type": "Concept", "title": "Product Roadmap"},
            body="# Product Roadmap\nEnterprise features.",
        )
    )

    searcher = KnowledgeSearch(bundle=bundle, qmd_url="http://127.0.0.1:59999")
    hits = await searcher.search("roadmap")

    assert len(hits) == 1
    hit = hits[0]
    assert hit.engine == "lexical-fallback"
    assert hit.path == "product.md"


@pytest.mark.asyncio
async def test_knowledge_search_maps_chroma_hits(tmp_path, monkeypatch):
    bundle_dir = tmp_path / "bundle"
    bundle = FileSystemOKFBundle(bundle_dir)
    bundle.create("Test Bundle")

    class MockResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return [
                {
                    "file": "pricing.md",
                    "title": "Pricing Strategy",
                    "score": 0.95,
                    "snippet": "Tiered enterprise subscription packages with discount terms." * 6,
                    "engine": "chroma",
                    "locator": "ev_concept_pricing.md",
                }
            ]

    class MockAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url, params=None):
            return MockResponse()

    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)

    searcher = KnowledgeSearch(bundle=bundle, qmd_url="http://mock-chroma:8181")
    hits = await searcher.search("pricing")

    assert len(hits) == 1
    hit = hits[0]
    assert hit.path == "pricing.md"
    assert hit.title == "Pricing Strategy"
    assert hit.engine == "chroma"
    assert len(hit.snippet) <= 320
    assert hit.locator == "ev_concept_pricing.md"


@pytest.mark.asyncio
async def test_qmd_reindex_returns_fallback_status_when_unreachable():
    status_none = await request_qmd_reindex(None)
    assert status_none == "disabled; lexical fallback active"

    status_unreachable = await request_qmd_reindex("http://127.0.0.1:59999")
    assert status_unreachable == "unavailable; lexical fallback active"
