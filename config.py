"""
config.py
---------
Central place for all settings. Reads secrets from a .env file so you
never hardcode your Groq API key in source control.
"""
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# NOTE: llama-3.1-70b-versatile and llama3-70b-8192 have both been
# decommissioned by Groq. llama-3.3-70b-versatile is the current
# replacement as of mid-2026. Check https://console.groq.com/docs/models
# if this ever starts erroring with "model_decommissioned".
LLM_MODEL = "llama-3.3-70b-versatile"
ROUTER_MODEL = "llama-3.1-8b-instant"   # small + fast, still current

# ---- ChromaDB settings ----
CHROMA_PERSIST_DIR = "chroma_db"
COLLECTION_NAME = "campus"

# ---- Embedding model (runs locally, free, no API calls) ----
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# ---- Chunking settings ----
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
TOP_K_RESULTS = 4

# ---- Source documents folder ----
DATA_DIR = "data"