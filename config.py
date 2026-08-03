"""
config.py
---------
Central place for all settings. Reads secrets from a .env file so you
never hardcode your Groq API key in source control.
"""
import os
from dotenv import load_dotenv

load_dotenv()  # loads variables from a local .env file, if present

# ---- Groq (LLM) settings ----
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# NOTE: llama-3.1-70b-versatile (used in the original build guide) has been
# decommissioned by Groq. As of mid-2026, Groq is also retiring
# llama-3.3-70b-versatile and llama-3.1-8b-instant in favor of the
# openai/gpt-oss family. Check https://console.groq.com/docs/deprecations
# and https://console.groq.com/docs/models if these ever stop working for you.
LLM_MODEL = "openai/gpt-oss-120b"      # main answering model (QA / quiz / deadlines)
ROUTER_MODEL = "openai/gpt-oss-20b"    # small + fast model just for routing decisions

# ---- ChromaDB settings ----
CHROMA_PERSIST_DIR = "chroma_db"
COLLECTION_NAME = "campus_docs"

# ---- Embedding model (runs locally, free, no API calls) ----
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# ---- Chunking settings ----
CHUNK_SIZE = 800       # characters per chunk
CHUNK_OVERLAP = 150    # overlap between consecutive chunks
TOP_K_RESULTS = 4      # how many chunks to retrieve per query

# ---- Source documents folder ----
DATA_DIR = "data"
