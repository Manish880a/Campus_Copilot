"""
memory.py
---------
Per-chat conversation memory, plus a cached, persistent connection to
the shared ChromaDB collection - one vector store shared by every chat
thread (built by ingest.py); only the conversation history is per-chat.
"""
import streamlit as st
import chromadb
from chromadb.utils import embedding_functions

from config import CHROMA_PERSIST_DIR, COLLECTION_NAME, EMBEDDING_MODEL


@st.cache_resource
def load_vectordb():
    """Open the persistent ChromaDB collection built by ingest.py.
    Returns None if ingest.py hasn't been run yet (or the collection is
    missing) rather than raising, so the app can still start and agents
    can fall back to a web search or an ungrounded answer.

    Note: this is cached for the life of the running app process. If you
    run ingest.py again while the app is already open, restart the app
    (or use the "Clear cache" option) to pick up the new index."""
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )
    try:
        return client.get_collection(name=COLLECTION_NAME, embedding_function=embed_fn)
    except Exception:
        return None


class SessionMemory:
    def __init__(self, state: dict):
        self.state = state
        self.state.setdefault("history", [])
        self.state.setdefault("last_context", [])
        self.state.setdefault("last_agent", None)
        self.state.setdefault("known_deadlines", [])
        self.state.setdefault("title", None)

    def get_vectordb(self):
        return load_vectordb()

    def add_turn(self, role: str, text: str, agent: str = None, query: str = None):
        turn = {"role": role, "text": text}
        if agent is not None:
            turn["agent"] = agent
        if query is not None:
            turn["query"] = query
        self.state["history"].append(turn)

    def get_recent_history(self, n: int = 6):
        return self.state["history"][-n:]

    def set_last_context(self, chunks: list):
        self.state["last_context"] = chunks

    def get_last_context(self):
        return self.state["last_context"]

    def set_last_agent(self, agent_name: str):
        self.state["last_agent"] = agent_name

    def add_deadline(self, deadline: dict):
        self.state["known_deadlines"].append(deadline)

    def history_as_prompt(self, n: int = 6) -> str:
        turns = self.get_recent_history(n)
        return "\n".join(f"{t['role']}: {t['text']}" for t in turns)