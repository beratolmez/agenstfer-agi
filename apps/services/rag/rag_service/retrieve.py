from .ingest import get_or_create_collection

def retrieve_knowledge(query: str, n_results: int = 3):
    """Query the ChromaDB for relevant OKF wiki segments."""
    collection = get_or_create_collection()
    
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    return results
