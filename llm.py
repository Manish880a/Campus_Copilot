"""
llm.py
------
Single place that talks to Groq, so swapping providers later (or
adding retries/logging) only means editing one file.
"""
from groq import Groq

from config import GROQ_API_KEY, LLM_MODEL

_client = Groq(api_key=GROQ_API_KEY)


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
