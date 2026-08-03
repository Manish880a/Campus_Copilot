"""
agents/quiz_agent.py
----------------------
Generates practice questions grounded in the retrieved document
chunks, so quizzes stay on-syllabus instead of hallucinated topics.
"""
from llm import chat
from retriever import retrieve

QUIZ_SYSTEM_PROMPT = """You are Campus Copilot's Quiz agent. Using ONLY the
provided document excerpts, write a short quiz for the student.
- Default to 5 multiple-choice questions unless the student asked for a
  different number or format.
- Each question needs 4 options (A-D) and you must mark the correct answer.
- Base every question on the given excerpts; do not invent facts outside them.
- Format cleanly with numbered questions."""


def answer(query: str, memory) -> str:
    hits = retrieve(query)
    memory.set_last_context(hits)

    if not hits:
        return "I couldn't find any indexed documents to build a quiz from. Has ingest.py been run yet?"

    context = "\n\n".join(
        f"[Source: {h['source']}]\n{h['text']}" for h in hits
    )

    user_prompt = f"""Document excerpts:
{context}

Student request: {query}"""

    return chat(QUIZ_SYSTEM_PROMPT, user_prompt, temperature=0.6)
