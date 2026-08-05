"""
llm.py
------
Single place that talks to Groq, so swapping providers or models later
only means editing config.py.
"""
from groq import Groq

from config import GROQ_API_KEY, LLM_MODEL

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found - copy .env.example to .env and add your key")

_client = Groq(api_key=GROQ_API_KEY)


def general_llm(prompt: str, temperature: float = 0.3) -> str:
    """Single-turn call with no system prompt. Used only as a last-resort
    ungrounded answer when neither the documents nor a web search have
    anything - always clearly labeled as such by the caller."""
    response = _client.chat.completions.create(
        model=LLM_MODEL,
        temperature=temperature,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def chat(system_prompt: str, user_prompt: str, model: str = LLM_MODEL,
          temperature: float = 0.3) -> str:
    """Send a single system+user turn to Groq and return the text reply."""
    response = _client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content