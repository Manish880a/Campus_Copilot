"""
memory.py
---------
Small session-memory manager. Each chat thread gets its own plain dict
(stored inside st.session_state["chats"][chat_id] by app.py), and this
class just gives that dict a clean, agent-friendly interface:

    - conversation turns (for follow-up questions like "explain that more")
    - the last retrieved context (so a follow-up doesn't need to re-embed
      an near-identical query)
    - any facts the deadline agent has extracted, so the router/Q&A agent
      can reference them later in the same chat

Each assistant turn can optionally carry:
    - agent: which specialist answered (for the colored badge)
    - query: the original user message that produced it (needed so the
      "Regenerate" button can re-run the same question)
"""


class SessionMemory:
    def __init__(self, state: dict):
        # `state` is a plain dict scoped to one chat thread (or a plain
        # dict in tests) - NOT necessarily st.session_state itself.
        self.state = state
        self.state.setdefault("history", [])          # list of turn dicts
        self.state.setdefault("last_context", [])      # last retrieved chunks
        self.state.setdefault("last_agent", None)       # which agent answered last
        self.state.setdefault("known_deadlines", [])    # facts found so far

    def add_turn(self, role: str, text: str, agent: str = None, query: str = None):
        turn = {"role": role, "text": text}
        if agent is not None:
            turn["agent"] = agent
        if query is not None:
            turn["query"] = query
        self.state["history"].append(turn)

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