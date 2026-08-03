# 🎓 Campus Copilot

A multi-agent Retrieval-Augmented Generation (RAG) assistant that answers questions from your college's own documents — syllabus, handbook, previous papers — and routes each query to a specialized sub-agent: **Q&A**, **Quiz Generator**, or **Deadline Tracker**. Q&A falls back to a free web search when the answer isn't in your documents. Built with a custom HUD-style light/dark UI, multi-chat history, and per-message copy/regenerate controls.

**Stack:** Python · Streamlit · ChromaDB (local, free) · sentence-transformers (local embeddings, free) · Groq API (LLM) · DuckDuckGo web search (free, keyless)

## Why this project

Most "chatbot wrapper" projects are a single API call in a chat box. This one combines several things that are genuinely hard to get right together:

- **A correct RAG pipeline** — chunking, embedding, vector storage, and retrieval, so answers are grounded in real documents instead of the model guessing.
- **Multi-agent routing** — a lightweight classifier hands each query to the right specialist instead of one agent doing everything badly.
- **Session memory** — conversation history and previously found facts persist across turns, so follow-up questions (even one-word ones) work naturally.
- **Graceful web fallback** — when the college documents don't have an answer, Q&A rewrites the question using conversation context and searches the web instead of dead-ending, clearly labeling web-sourced answers as such.

## Architecture

```
data/*.pdf,*.txt
     |
     v
ingest.py --(chunk + embed)--> ChromaDB (chroma_db/)
                                    ^
                                    | retrieve(query)
User message --> Router agent --+
                  |--> QA agent -------+--> (web search fallback if no doc match)
                  |--> Quiz agent ------+--> Groq LLM --> reply
                  |--> Deadline agent --+
                                    |
                        (reply + agent label + query
                         saved to the active chat's
                         memory via memory.py)
```

Two pipelines run in this app:

- **Offline** (once, or whenever docs change): documents in `data/` → chunked → embedded locally → stored in a persistent ChromaDB collection.
- **Online** (every chat message): user message → Router agent labels it QA / QUIZ / DEADLINE → that agent retrieves the most relevant chunks → Groq LLM generates a grounded reply (or, for Q&A with no document match, a context-aware web search fallback) → reply is saved to the active chat thread and rendered with agent-colored badges.

## Features

- **Three specialist agents** — Q&A, Quiz, and Deadline — each grounded strictly in your indexed documents.
- **Web search fallback (Q&A only)** — free, keyless DuckDuckGo search, used only when your documents don't cover the question. Follow-up messages (e.g. just a city name after "what's the weather?") are rewritten into a standalone search query using conversation context before searching.
- **Multi-chat sidebar** — start a "New Chat" at any time; past chats stay listed and clickable, each with its own independent memory (scoped to the current browser session).
- **Copy & Regenerate** — every assistant reply has a copy-to-clipboard button and a regenerate button that re-asks the same question fresh.
- **Light/dark HUD theme** — a custom dotted-grid, glowing console aesthetic that fully re-themes on toggle, including Streamlit's own header and sidebar chrome.

## Project structure

```
campus-copilot/
├── app.py                  # Streamlit UI - entry point
├── config.py                # settings: model names, chunk size, paths
├── ingest.py                 # builds the ChromaDB vector index from data/
├── retriever.py              # shared ChromaDB query helper
├── memory.py                 # per-chat session memory manager
├── llm.py                    # Groq API call wrapper
├── web_search.py             # free DuckDuckGo web search fallback
├── agents/
│   ├── router.py             # classifies query -> QA / QUIZ / DEADLINE
│   ├── qa_agent.py           # RAG question answering + web fallback
│   ├── quiz_agent.py         # RAG-grounded quiz generation
│   └── deadline_agent.py     # RAG-grounded deadline lookup
├── data/                     # put your syllabus/handbook/papers here (gitignored)
├── chroma_db/                # auto-created persistent vector store (gitignored)
├── requirements.txt
├── .env.example
└── .gitignore
```

## Prerequisites

- Python 3.10+
- A free Groq API key from [console.groq.com](https://console.groq.com)
- Your college documents as PDFs or plain text files

## Setup

```bash
git clone https://github.com/<your-username>/campus-copilot.git
cd campus-copilot

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env       # then paste in your real GROQ_API_KEY
```

## Usage

```bash
# 1. Add your documents
cp your-syllabus.pdf your-handbook.pdf data/

# 2. Build the vector index (re-run whenever documents change)
python ingest.py

# 3. Launch the app
streamlit run app.py
```

Open the local URL Streamlit prints (usually `http://localhost:8501`). Try one question of each type to confirm routing:

- *"What's the attendance policy in the handbook?"* → Q&A agent (from your documents)
- *"What's the weather in your city today?"* → Q&A agent (falls back to the web, clearly labeled)
- *"Quiz me on chapter 3"* → Quiz agent
- *"When is the assignment 2 submission due?"* → Deadline agent

## How it stays reliable

1. **Routing logic stays decoupled from answering logic** — the router only ever returns one of three labels and never touches document context, so a routing bug can't corrupt an answer.
2. **RAG correctness comes from grounding, not model size** — every agent is instructed to answer only from retrieved chunks (or, for Q&A's fallback, only from web results) and say plainly when something isn't found.
3. **Memory is additive, not load-bearing** — the pipeline works correctly on a single turn even with empty memory; memory only adds continuity on top.
4. **Web search is scoped to Q&A only** — Quiz and Deadline stay strictly document-grounded, since a quiz question or a deadline pulled from a random web result would defeat the point.

## Troubleshooting

| Issue | Fix |
|---|---|
| `TypeError: Client.__init__() got an unexpected keyword argument 'proxies'` | Your `groq` package is outdated relative to `httpx`. Run `pip install --upgrade groq`. |
| "Collection does not exist" | Run `python ingest.py` before `streamlit run app.py`. |
| Router picks the wrong agent | Tighten the label list in `router.py`'s system prompt (temperature is already 0). |
| Answers ignore your documents | Check `data/` actually has files before ingesting; check `CHUNK_SIZE` isn't cutting key info awkwardly. |
| Web fallback loses context on follow-ups | Make sure you're on the current `qa_agent.py` — it rewrites short follow-ups into standalone search queries before searching. |
| Slow first run | `sentence-transformers` downloads the embedding model once; later runs are fast and offline. |

## Extension ideas

- Persist chat history to disk (SQLite) so it survives a browser refresh, not just a session
- Add a thumbs-up/down feedback control per answer to track which agent underperforms
- Add a 4th agent for campus events or a contact directory
- Swap the character-based chunker for a sentence-aware splitter (e.g. via `tiktoken`)
- Deploy on Streamlit Community Cloud (free)

## License

MIT — see [LICENSE](LICENSE).
