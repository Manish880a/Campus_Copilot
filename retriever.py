"""
retriever.py
------------
Query helper - takes an already-loaded ChromaDB collection (see
memory.py's cached loader) so every agent queries the same store the
same way.
"""
from config import TOP_K_RESULTS


def retrieve(query: str, collection, top_k: int = TOP_K_RESULTS):
    """Return a list of {"text": ..., "source": ..., "score": ...}."""
    if collection is None:
        return []

    results = collection.query(query_texts=[query], n_results=top_k)

    hits = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]

    for doc, meta, dist in zip(docs, metas, dists):
        hits.append({
            "text": doc,
            "source": (meta or {}).get("source", "unknown"),
            "score": dist,
        })
    return hits