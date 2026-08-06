# 🎓 Campus Copilot

> An AI-powered study assistant that answers questions from your college documents, quizzes you on any topic, and tracks your deadlines — all in one chat interface.

---

## ✨ Features

| Feature | Description |
|---|---|
| 📘 **Q&A Agent** | Ask anything about your syllabus, handbook, or previous exam papers. Answers are grounded in your own documents with source citations. Falls back to a live web search if your docs don't cover it. |
| ✏️ **Quiz Agent** | Ask to be quizzed on any topic. Get MCQs, short-answer questions, or practice tests generated on the spot. |
| ⏰ **Deadline Agent** | Mention a due date or exam date and it's logged. Ask "what's due this week?" to get a summary. |
| 🔀 **Smart Router** | Every message is classified automatically — no need to select a mode. The right agent picks up your question. |
| 💬 **Multi-chat** | Multiple independent chat threads, each with its own memory, just like a real chat app. |

---

## 🏗️ Architecture

```
User message
     │
     ▼
 Router Agent  ──── (fast, small LLM) ────► QA / QUIZ / DEADLINE
                                                     │
                              ┌──────────────────────┤
                              ▼                      ▼
                      ChromaDB (RAG)          Groq LLM API
                      local vector DB         (main model)
                              │
                    ┌─────────┴─────────┐
                    │   No answer?      │
                    ▼                   │
             DuckDuckGo Web Search      │
                    │                   │
                    └─────────┬─────────┘
                              ▼
                         Final reply
                              │
                              ▼
                     Session Memory
                  (per-chat history)
```

**Tech stack:**

- **Frontend** — [Streamlit](https://streamlit.io/) with custom CSS (HUD / glassmorphism design)
- **LLM** — [Groq](https://groq.com/) (`openai/gpt-oss-120b` for answers, `openai/gpt-oss-20b` for routing)
- **Vector DB** — [ChromaDB](https://www.trychroma.com/) (local, persistent)
- **Embeddings** — `all-MiniLM-L6-v2` via `sentence-transformers` (runs fully offline, no API cost)
- **PDF parsing** — `pypdf`
- **Web fallback** — DuckDuckGo Search (`ddgs`)

---

## 🚀 Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/Manish880a/Campus_Copilot.git
cd Campus_Copilot
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your Groq API key

Copy the example env file and fill in your key:

```bash
cp .env.example .env
```

Edit `.env`:
```
GROQ_API_KEY=your_groq_api_key_here
```

> Get a free API key at [console.groq.com](https://console.groq.com)

### 5. Add your college documents

Drop your `.pdf` or `.txt` files into the `data/` folder:

```
data/
├── syllabus.pdf
├── student_handbook.pdf
├── previous_papers_2024.pdf
└── ...
```

### 6. Build the vector database

Run this once (and again whenever you add or update documents):

```bash
python ingest.py
```

### 7. Launch the app

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 💬 Usage Examples

| What you type | Which agent handles it |
|---|---|
| `"What's the attendance policy?"` | 📘 Q&A Agent |
| `"Explain DBMS normalization"` | 📘 Q&A Agent |
| `"Quiz me on OS scheduling algorithms"` | ✏️ Quiz Agent |
| `"Give me 5 MCQs on data structures"` | ✏️ Quiz Agent |
| `"Assignment 2 is due on 15th August"` | ⏰ Deadline Agent |
| `"What deadlines do I have this week?"` | ⏰ Deadline Agent |

---

## 📁 Project Structure

```
Campus_Copilot/
├── app.py              # Streamlit UI — main entry point
├── memory.py           # Per-chat session memory manager
├── config.py           # All settings (models, chunk sizes, paths)
├── ingest.py           # PDF/TXT → ChromaDB indexing pipeline
├── retriever.py        # ChromaDB vector search wrapper
├── llm.py              # Groq API wrapper
├── web_search.py       # DuckDuckGo search fallback
├── agents/
│   ├── router.py       # Classifies queries → QA / QUIZ / DEADLINE
│   ├── qa_agent.py     # RAG-based Q&A + web fallback
│   ├── quiz_agent.py   # Quiz / MCQ generator
│   └── deadline_agent.py # Deadline tracker
├── data/               # ← Put your PDFs/TXTs here
├── .streamlit/
│   └── config.toml     # Streamlit theme config
├── .env.example        # Template for environment variables
└── requirements.txt
```

---

## ⚙️ Configuration

All settings are in [`config.py`](config.py):

| Setting | Default | Description |
|---|---|---|
| `LLM_MODEL` | `openai/gpt-oss-120b` | Main answering model |
| `ROUTER_MODEL` | `openai/gpt-oss-20b` | Fast routing/rewrite model |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Local embedding model |
| `CHUNK_SIZE` | `800` | Characters per document chunk |
| `CHUNK_OVERLAP` | `150` | Overlap between chunks |
| `TOP_K_RESULTS` | `4` | Chunks retrieved per query |
| `CHROMA_PERSIST_DIR` | `chroma_db` | Vector DB storage path |
| `DATA_DIR` | `data` | Folder for source documents |

---

## 🔄 Re-indexing Documents

Whenever you add, remove, or update files in `data/`, re-run:

```bash
python ingest.py
```

This rebuilds the vector database from scratch — no duplicates.

---

## 🛠️ Requirements

- Python **3.10+**
- A free [Groq API key](https://console.groq.com)
- Your college documents in `.pdf` or `.txt` format

---

## 📄 License

MIT — free to use, modify, and distribute.

---

<div align="center">
  Built for students, by a student 🎓
</div>
