"""
web_search.py
-------------
Free, keyless web search fallback (DuckDuckGo via the `ddgs` package).
Used only by the Q&A agent, and only when the answer isn't found in the
indexed college documents - so students still get a useful answer
instead of a dead end, while Quiz and Deadline stay strictly grounded
in the actual course materials.
"""
from ddgs import DDGS


def search_web(query: str, max_results: int = 4) -> list[dict]:
    """
    Return up to `max_results` web results as:
        [{"title": ..., "snippet": ..., "url": ...}, ...]

    Never raises - returns an empty list on failure (e.g. rate limiting)
    so callers can handle a quiet fallback instead of crashing the chat.
    """
    try:
        with DDGS() as ddgs:
            raw = ddgs.text(query, max_results=max_results)
            return [
                {
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                    "url": r.get("href", ""),
                }
                for r in raw
            ]
    except Exception as e:
        print(f"Web search failed: {e}")
        return []