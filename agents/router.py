"""
agents/router.py
-----------------
Decides which specialized agent should handle an incoming query.
Uses a small, fast Groq model with a constrained prompt so it reliably
returns one of exactly three labels.
"""
from llm import chat
from config import ROUTER_MODEL

ROUTER_SYSTEM_PROMPT = """You are a routing classifier for a college assistant.
Classify the user's message into exactly ONE of these labels:

- QA: factual questions about course content, syllabus, handbook rules,
  policies, previous exam papers, or anything else that should be answered
  by looking up the college documents.
- QUIZ: the user wants practice questions, a quiz, MCQs, or to be tested
  on a topic.
- DEADLINE: the user is asking about due dates, submission dates, exam
  dates, or wants something added to / checked against a deadline list.

Reply with ONLY the single label word: QA, QUIZ, or DEADLINE. No punctuation,
no explanation."""


def route(query: str) -> str:
    """Return one of 'QA', 'QUIZ', 'DEADLINE'."""
    label = chat(ROUTER_SYSTEM_PROMPT, query, model=ROUTER_MODEL, temperature=0)
    label = label.strip().upper()
    for valid in ("QA", "QUIZ", "DEADLINE"):
        if valid in label:
            return valid
    return "QA"  # safe default
