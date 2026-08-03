"""
ingest.py
---------
Run this once (and again whenever documents change) to build the
vector database:

    python ingest.py

Steps:
    1. Load every .pdf / .txt file from the data/ folder
    2. Split each document into overlapping text chunks
    3. Embed the chunks locally with sentence-transformers
    4. Store the chunks + embeddings + metadata in a persistent
       ChromaDB collection
"""
import os
import glob
import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader

from config import (
    CHROMA_PERSIST_DIR,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    DATA_DIR,
)


def load_text_from_file(path: str) -> str:
    """Extract raw text from a .pdf or .txt file."""
    if path.lower().endswith(".pdf"):
        reader = PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Simple sliding-window character chunker with overlap."""
    text = " ".join(text.split())  # normalize whitespace
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return [c for c in chunks if c.strip()]


def build_index():
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

    # Local, free embedding function (downloads model once, then runs offline)
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )

    # Fresh collection each run so re-ingesting doesn't duplicate chunks
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME, embedding_function=embed_fn
    )

    files = glob.glob(os.path.join(DATA_DIR, "*.pdf")) + glob.glob(
        os.path.join(DATA_DIR, "*.txt")
    )

    if not files:
        print(f"No .pdf/.txt files found in {DATA_DIR}/. Add your syllabus, "
              f"handbook, previous papers, etc. and re-run.")
        return

    all_ids, all_docs, all_meta = [], [], []
    for path in files:
        fname = os.path.basename(path)
        print(f"Processing {fname} ...")
        text = load_text_from_file(path)
        chunks = chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
        for i, chunk in enumerate(chunks):
            all_ids.append(f"{fname}-{i}")
            all_docs.append(chunk)
            all_meta.append({"source": fname, "chunk_index": i})

    # Chroma has a batch-size limit on some backends; add in batches of 100
    batch = 100
    for i in range(0, len(all_docs), batch):
        collection.add(
            ids=all_ids[i:i + batch],
            documents=all_docs[i:i + batch],
            metadatas=all_meta[i:i + batch],
        )

    print(f"Indexed {len(all_docs)} chunks from {len(files)} document(s) "
          f"into ChromaDB at '{CHROMA_PERSIST_DIR}/'.")


if __name__ == "__main__":
    build_index()
