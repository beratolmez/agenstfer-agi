from .ingest import get_or_create_collection


def retrieve_knowledge(query: str, n_results: int = 3):
    """Query ChromaDB collection for relevant active OKF wiki segments."""
    collection = get_or_create_collection()
    results = collection.query(query_texts=[query], n_results=n_results)
    hits = []
    if results and "documents" in results and results["documents"]:
        docs = results["documents"][0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0] if "distances" in results else []
        for i, doc in enumerate(docs):
            meta = metas[i] if i < len(metas) else {}
            dist = distances[i] if i < len(distances) else 0.0
            hits.append(
                {
                    "file": meta.get("path") or meta.get("source") or "concept.md",
                    "title": meta.get("title") or "OKF Concept",
                    "score": round(1.0 - float(dist), 4),
                    "snippet": str(doc)[:320],
                    "engine": "chroma",
                    "locator": meta.get("locator") or f"ev_concept_{meta.get('path')}",
                }
            )
    return hits
