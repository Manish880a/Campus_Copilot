"""
memory.py
---------
Very small session-memory manager. Streamlit already keeps
`st.session_state` alive for the duration of a user's session, so
this class just gives that state a clean, agent-friendly interface:

    - conversation turns (for follow-up questions like "explain that more")
    - the last retrieved context (so a follow-up doesn't need to re-embed
      an near-identical query)
    - any facts the deadline agent has extracted, so the router/Q&A agent
      can reference them later in the same session
"""


class SessionMemory:
    def __init__(self, state: dict):
        # `state` is st.session_state (or a plain dict in tests)
        self.state = state
        self.state.setdefault("history", [])          # list of {"role", "text"}
        self.state.setdefault("last_context", [])      # last retrieved chunks
        self.state.setdefault("last_agent", None)       # which agent answered last
        self.state.setdefault("known_deadlines", [])    # facts found so far

    def add_turn(self, role: str, text: str, agent: str = None):
        # `agent` is the short label (QA / QUIZ / DEADLINE) for assistant
        # turns, so the UI can re-render the right badge/icon on history replay.
        self.state["history"].append({"role": role, "text": text, "agent": agent})

    def get_recent_history(self, n: int = 6):
        """Last n turns, formatted for inclusion in an LLM prompt."""
        return self.state["history"][-n:]

    def set_last_context(self, chunks: list):
        self.state["last_context"] = chunks

    def get_last_context(self):
        return self.state["last_context"]

    def set_last_agent(self, agent_name: str):
        self.state["last_agent"] = agent_name

    def add_deadline(self, deadline: dict):
        self.state["known_deadlines"].append(deadline)

    def history_as_prompt(self, n: int = 6) -> str:
        turns = self.get_recent_history(n)
        return "\n".join(f"{t['role']}: {t['text']}" for t in turns)
