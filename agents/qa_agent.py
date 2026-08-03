"""
agents/qa_agent.py
-------------------
Standard RAG: retrieve relevant chunks from ChromaDB, then ask Groq to
answer using only that context (with citations to the source file).

If the college documents don't contain the answer, this falls back to
a free, keyless DuckDuckGo web search - so the student gets a useful
answer instead of a dead end. Web-sourced answers are always labeled
so it's clear they didn't come from the college's own materials.

Before searching the web, a short-follow-up message (like a one-word
reply "kolkata" after "what's the weather today?") is rewritten into a
standalone query using the recent conversation - otherwise the web
search loses the context of what was actually being asked.
"""
from llm import chat
from retriever import retrieve
from web_search import search_web
from config import ROUTER_MODEL

# Sentinel the model returns when the documents don't have the answer.
# Checking for this exact token is far more reliable than trying to
# detect "I couldn't find it" phrased in natural language.
NO_ANSWER_TOKEN = "NO_ANSWER_IN_DOCS"

QA_SYSTEM_PROMPT = f"""You are Campus Copilot's Q&A agent. Answer the
student's question using ONLY the provided document excerpts.
- If the answer isn't in the excerpts, respond with EXACTLY this token
  and nothing else: {NO_ANSWER_TOKEN}
- Do not guess or use outside knowledge when answering from documents.
- Keep answers concise and student-friendly.
- Cite the source file name in parentheses after facts you use, e.g. (handbook.pdf)."""

REWRITE_SYSTEM_PROMPT = """Rewrite the student's latest message into a
short, standalone web search query. Use the conversation so far to
resolve short follow-ups (e.g. if the latest message is just a city
name after a weather question, the query should be "weather in
<city>"). Reply with ONLY the rewritten query text, nothing else."""

WEB_SYSTEM_PROMPT = """You are Campus Copilot's Q&A agent, now answering
from general web search results because the college documents didn't
cover this question.
- Use the conversation so far to understand what's really being asked,
  especially if the latest message is a short follow-up (like just a
  city name or a single word).
- Answer using ONLY the provided web search results below.
- Keep it concise and student-friendly.
- Cite the source (site name or URL) after facts you use.
- If the search results don't answer the question either, say so plainly
  rather than guessing."""


def _build_search_query(query: str, memory) -> str:
    """Turn a possibly-context-dependent message into a standalone
    search query, using recent conversation history. Falls back to the
    raw query if there's no prior history or the rewrite call fails."""
    prior_turns = memory.get_recent_history(n=7)[:-1]  # exclude current turn
    if not prior_turns:
        return query

    history_text = "\n".join(f"{t['role']}: {t['text']}" for t in prior_turns)
    user_prompt = f"""Conversation so far:
{history_text}

Latest message: {query}"""

    try:
        rewritten = chat(REWRITE_SYSTEM_PROMPT, user_prompt, model=ROUTER_MODEL, temperature=0)
        return rewritten.strip() or query
    except Exception:
        return query


def _answer_from_web(query: str, memory) -> str:
    search_query = _build_search_query(query, memory)
    results = search_web(search_query)
    if not results:
        return (
            "I couldn't find this in your college documents, and the web "
            "search didn't return anything useful either. Try rephrasing "
            "the question."
        )

    context = "\n\n".join(
        f"[{r['title']}]({r['url']})\n{r['snippet']}" for r in results
    )
    history = memory.history_as_prompt()
    user_prompt = f"""Conversation so far:
{history}

Web search results:
{context}

Latest message: {query}"""

    reply = chat(WEB_SYSTEM_PROMPT, user_prompt)
    return f"🌐 *Not found in your college documents — answered from the web:*\n\n{reply}"


def answer(query: str, memory) -> str:
    hits = retrieve(query)
    memory.set_last_context(hits)

    # No indexed documents at all (or none relevant) - go straight to web.
    if not hits:
        return _answer_from_web(query, memory)

    context = "\n\n".join(
        f"[Source: {h['source']}]\n{h['text']}" for h in hits
    )
    history = memory.history_as_prompt()
    user_prompt = f"""Conversation so far:
{history}

Document excerpts:
{context}

Student question: {query}"""

    reply = chat(QA_SYSTEM_PROMPT, user_prompt)

    # Model explicitly signaled the docs didn't cover it - fall back to web.
    if reply.strip() == NO_ANSWER_TOKEN:
        return _answer_from_web(query, memory)

    return reply