"""
retriever.py
------------
Thin wrapper around the ChromaDB collection so every agent queries
the vector store the same way.
"""
import chromadb
from chromadb.utils import embedding_functions

from config import CHROMA_PERSIST_DIR, COLLECTION_NAME, EMBEDDING_MODEL, TOP_K_RESULTS

_client = None
_collection = None


def get_collection():
    """Lazily connect to the persistent ChromaDB collection (singleton)."""
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )
        _collection = _client.get_collection(
            name=COLLECTION_NAME, embedding_function=embed_fn
        )
    return _collection


def retrieve(query: str, top_k: int = TOP_K_RESULTS):
    """
    Return a list of {"text": ..., "source": ..., "score": ...}
    for the most relevant chunks to `query`.
    """
    collection = get_collection()
    results = collection.query(query_texts=[query], n_results=top_k)

    hits = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]

    for doc, meta, dist in zip(docs, metas, dists):
        hits.append({
            "text": doc,
            "source": meta.get("source", "unknown"),
            "score": dist,
        })
    return hits
