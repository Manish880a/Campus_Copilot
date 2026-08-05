"""
agents/deadline_agent.py
--------------------------
Finds dates/deadlines mentioned in the retrieved chunks and also
remembers deadlines it has already surfaced this chat, so a later
"what's still due?" question benefits from earlier lookups too.
"""
from llm import chat
from retriever import retrieve

DEADLINE_SYSTEM_PROMPT = """You are Campus Copilot's Deadline agent. Using
ONLY the provided document excerpts (and any previously found deadlines
listed below), answer the student's question about dates, deadlines, or
submissions.
- List relevant deadlines clearly with dates and what they're for.
- If nothing relevant is found, say so plainly rather than guessing a date.
- Sort chronologically when listing multiple deadlines."""


def answer(query: str, memory) -> str:
    collection = memory.get_vectordb()
    hits = retrieve(query, collection) if collection else []
    memory.set_last_context(hits)

    if not hits:
        return "I couldn't find any indexed documents to check for deadlines. Has ingest.py been run yet?"

    context = "\n\n".join(f"[Source: {h['source']}]\n{h['text']}" for h in hits)
    known = memory.state.get("known_deadlines", [])
    known_text = "\n".join(f"- {d}" for d in known) if known else "(none yet)"

    user_prompt = f"""Document excerpts:
{context}

Deadlines already found earlier this session:
{known_text}

Student question: {query}"""

    result = chat(DEADLINE_SYSTEM_PROMPT, user_prompt, temperature=0.2)
    memory.add_deadline(f"Q: {query} -> {result[:200]}")
    return result